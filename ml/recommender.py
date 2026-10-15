"""Backend-ready prediction interface. Loads saved artifacts once; no retraining per request.

Informational recommendations only — not medical advice.
"""
import ast
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import (ALLERGY_TO_FLAG, ALLERGEN_FLAG_COLS, ARTIFACTS_DIR,
                     GOAL_ALIASES, GOAL_NUTRITION_TARGETS)

NUTRISCORE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}


def _parse_list_cell(s):
    if pd.isna(s):
        return []
    t = str(s).strip()
    if t.startswith("["):
        try:
            v = ast.literal_eval(t)
            return [str(x).strip().lower() for x in v] if isinstance(v, list) else [t.lower()]
        except Exception:
            return [t.lower()]
    return [t.lower()]


def _norm(s, default=""):
    return str(s).strip().lower() if s is not None and str(s).strip() else default


class FitnessRecommender:
    # Active food catalog: Indian-food derived catalog (indian_catalog.csv,
    # built from healthy_foods_database via ml/indian_catalog.py). No merge
    # with any other dataset (no verified cross-dataset key). The OFF
    # allergen-annotated catalog is EXCLUDED: it has no usable Indian-food
    # selection, so it cannot serve this experience even as an allergy fallback.
    def __init__(self, diet_model, knn_bundle, food: pd.DataFrame,
                 workout: pd.DataFrame, meta: dict, diet_meta: dict,
                 artifacts_dir: Path, food_allergen: pd.DataFrame | None = None,
                 recipes: pd.DataFrame | None = None):
        self._diet_model = diet_model
        self._knn = knn_bundle
        self._food = food
        self._food_allergen = food_allergen
        self._workout = workout
        self._recipes = recipes
        self._meta = meta
        self._diet_meta = diet_meta or {}
        self._dir = Path(artifacts_dir)

    @classmethod
    def load(cls, artifacts_dir: str | Path = ARTIFACTS_DIR) -> "FitnessRecommender":
        d = Path(artifacts_dir)
        missing = [f for f in ["diet_model.joblib", "knn.joblib", "indian_catalog.csv",
                               "recipe_catalog.csv",
                               "meta.json", "diet_meta.json"]
                   if not (d / f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing artifacts in {d}: {missing}. Run `python -m ml.train` first.")
        diet_model = joblib.load(d / "diet_model.joblib")
        knn = joblib.load(d / "knn.joblib")
        if not isinstance(knn, dict) or "general" not in knn:
            knn = {"general": knn, "allergen": None}  # legacy single-catalog artifacts
        food = pd.read_csv(d / "indian_catalog.csv")
        recipes = pd.read_csv(d / "recipe_catalog.csv")
        # Workout catalog is large and optional: diet endpoints work without it.
        workout = pd.read_csv(d / "workout_catalog.csv") if (d / "workout_catalog.csv").exists() else None
        meta = json.loads((d / "meta.json").read_text())
        diet_meta = json.loads((d / "diet_meta.json").read_text())
        return cls(diet_model, knn, food, workout, meta, diet_meta, d, recipes=recipes)

    # ---------------- diet ----------------
    def predict_diet_category(self, profile: dict) -> dict:
        """Predict Diet_Recommendation from a user/health profile dict."""
        if not isinstance(profile, dict):
            raise ValueError("profile must be a dict")
        row = {c: profile.get(c) for c in
               ["Age", "Gender", "Weight_kg", "Height_cm", "BMI", "Severity",
                "Physical_Activity_Level", "Daily_Caloric_Intake", "Cholesterol_mg/dL",
                "Blood_Pressure_mmHg", "Glucose_mg/dL", "Dietary_Restrictions",
                "Allergies", "Preferred_Cuisine", "Weekly_Exercise_Hours",
                "Adherence_to_Diet_Plan", "Dietary_Nutrient_Imbalance_Score"]}
        # If BMI missing but weight/height present, compute it (documented, testable)
        if row.get("BMI") is None and row.get("Weight_kg") and row.get("Height_cm"):
            try:
                row["BMI"] = float(row["Weight_kg"]) / (float(row["Height_cm"]) / 100) ** 2
            except Exception:
                pass
        X = pd.DataFrame([row])
        pred = self._diet_model.predict(X)[0]
        proba = None
        if hasattr(self._diet_model, "predict_proba"):
            try:
                proba = {str(k): round(float(v), 4) for k, v in
                         zip(self._diet_model.classes_, self._diet_model.predict_proba(X)[0])}
            except Exception:
                proba = None
        return {"diet_category": str(pred), "probabilities": proba,
                "model": "RandomForest", "version": self._meta.get("version"),
                "note": "Informational only; Disease_Type intentionally excluded from features.",
                "explanation": self._category_explanation(dict(X.iloc[0]), str(pred), proba)}

    def _category_explanation(self, features: dict, pred: str, proba: dict | None) -> dict:
        """Runtime RF explanation built from actual inputs + saved train metadata."""
        m = self._diet_meta
        shown = {k: _py(v) for k, v in features.items()}
        return {
            "predicted_category": pred,
            "probabilities": proba,
            "input_features": shown,
            "goal_independent": ("The user's goal is NOT a model feature: the category is "
                                 "predicted from the health profile only, so a weight-loss "
                                 "goal can still yield 'Balanced'. This is by design, not a bug; "
                                 "the category was never hardcoded to match the goal."),
            "top_features": (m.get("feature_importance") or [])[:8],
            "target_distribution": m.get("target_distribution"),
            "test_metrics": {"accuracy": m.get("accuracy"), "f1_macro": m.get("f1_macro"),
                             "f1_weighted": m.get("f1_weighted"),
                             "dummy_accuracy": m.get("dummy_accuracy"),
                             "n_train": m.get("n_train"), "n_test": m.get("n_test")},
            "disclaimer": m.get("disclaimer", "Model output, not a medical diagnosis."),
        }

    # ---------------- food ranking ----------------
    ALLERGEN_DATA_MSG = ("Catalog contains no allergen information: compatibility "
                         "cannot be established and is never assumed.")

    def _apply_food_filters(self, df: pd.DataFrame, allergies, restrictions):
        excluded, enforced = [], []
        keep = pd.Series(True, index=df.index)
        has_flags = any(c.startswith("contains_") for c in df.columns)
        for a in (allergies or []):
            if not has_flags:
                # No allergen data at all: exclude every uncertain candidate.
                keep &= False
                excluded.append({"type": "allergy_unverifiable", "value": a,
                                 "reason": self.ALLERGEN_DATA_MSG})
                continue
            key = _norm(a)
            flag = next((f for sub, f in ALLERGY_TO_FLAG.items() if sub in key), None)
            if flag is None:
                # Unknown allergy: cannot verify safety -> record limitation, do not filter silently
                excluded.append({"type": "allergy_unmapped", "value": a})
                continue
            if flag not in df.columns:
                # Missing flag data must NOT be treated as allergen-free -> drop all uncertain
                keep &= False
                excluded.append({"type": "allergy_unknown_data", "value": a})
                continue
            mask = df[flag].fillna(False).astype(bool)
            keep &= ~mask
            enforced.append({"allergy": a, "flag": flag,
                             "excluded_rows": int(mask.sum())})
        for r in (restrictions or []):
            key = _norm(r)
            if "sodium" in key:
                before = int(keep.sum())
                keep &= df["sodium_100g"].fillna(9e9) <= 0.4
                enforced.append({"restriction": r, "rule": "sodium_100g <= 0.4 g",
                                 "excluded_rows": before - int(keep.sum())})
            elif "sugar" in key:
                before = int(keep.sum())
                keep &= df["sugars_100g"].fillna(9e9) <= 5.0
                enforced.append({"restriction": r, "rule": "sugars_100g <= 5.0 g",
                                 "excluded_rows": before - int(keep.sum())})
            else:
                excluded.append({"type": "restriction_unsupported", "value": r})
        return df[keep], excluded, enforced

    def recommend_diet(self, profile: dict) -> dict:
        """Full diet recommendation: predicted category + KNN-ranked foods (JSON-serializable)."""
        if not isinstance(profile, dict):
            raise ValueError("profile must be a dict")
        top_k = int(profile.get("top_k", 10))
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        cat = self.predict_diet_category(profile)
        goal = _norm(profile.get("goal", "balanced"), "balanced")
        goal_key = GOAL_ALIASES.get(goal, "balanced")
        target = GOAL_NUTRITION_TARGETS[goal_key]

        # Catalog routing: the sole active catalog is the Indian-food derived
        # catalog, which has no allergen data. Any requested allergy therefore
        # excludes all candidates with a warning (handled in _apply_food_filters).
        # There is deliberately NO fallback to international branded products.
        allergies = profile.get("allergies", []) or []
        restrictions = profile.get("dietary_restrictions", []) or []
        catalog, bundle, ckey = self._food, self._knn.get("general", self._knn), "indian"
        n_before = int(len(catalog))
        eligible, filter_notes, enforced = self._apply_food_filters(catalog, allergies, restrictions)
        for a in allergies:
            flag = next((f for sub, f in ALLERGY_TO_FLAG.items() if sub in _norm(a)), None)
            if flag is None and not any(n.get("type") == "allergy_unmapped" and n.get("value") == a
                                        for n in filter_notes):
                filter_notes.append({"type": "allergy_unmapped", "value": a,
                                     "reason": "Label maps to no known catalog flag; "
                                               "compatibility cannot be established."})
        has_allergen_data = any(c.startswith("contains_") for c in catalog.columns)
        source_file = "indian_catalog.csv (derived from healthy_foods_database.csv)"
        base = {"diet_category": cat, "goal_profile": goal_key,
                "category_method": ("RandomForest classifier predicts the diet category "
                                    "from the health profile (informational only)."),
                "ranking_method": ("KNN ranks catalog foods by scaled Euclidean distance "
                                   "to an explicit per-100g reference nutrient profile. "
                                   "Distance measures closeness, not suitability."),
                "scope": ("Single-food suggestions only — not a daily meal plan: the "
                          "implementation does not select meal slots or portions and does "
                          "not total daily nutrients."),
                "catalog_used": {"key": ckey, "source_dataset": source_file,
                                 "rows": n_before,
                                 "allergen_data": has_allergen_data,
                                 "why": ("Indian-food-only catalog (dishes + staple ingredients, "
                                         "see ml/indian_catalog.py). No international fallback.")},
                "candidate_counts": {"before_filtering": n_before, "after_filtering": int(len(eligible))},
                "n_eligible": int(len(eligible)),
                "restrictions_enforced": enforced,
                "allergen_data": "available" if has_allergen_data else "unavailable",
                "filter_notes": filter_notes,
                "version": self._meta.get("version")}
        if not has_allergen_data and allergies:
            base["allergen_warning"] = self.ALLERGEN_DATA_MSG
        # --- recipe + eligible-food outputs (same eligibility rules) ---
        recipe_constraints = self._recipe_constraints(profile, restrictions)
        meals = self._recommend_meals(recipe_constraints) if self._recipes is not None else None
        base["eligible_foods"] = self._eligible_food_groups(eligible, catalog)
        base["excluded_foods"] = self._excluded_foods(catalog, eligible, allergies, restrictions)
        if meals is not None:
            base["recipes"] = meals["compatible"]
            base["recipes_needs_review"] = meals["needs_review"]
            base["filtering_summary"] = meals["filtering_summary"]
        base["warnings"] = self._collect_warnings(base, allergies, restrictions, meals)
        if eligible.empty:
            return {**base, "items": [],
                    "unmet": ("No foods satisfy all constraints; relax restrictions. "
                              + (self.ALLERGEN_DATA_MSG if allergies and not has_allergen_data else ""))}

        cols = bundle["cols"]
        med = bundle["medians"]
        q_df = pd.DataFrame([{c: target.get(c, med[c]) for c in cols}])
        q = bundle["scaler"].transform(q_df[cols])
        k = min(top_k, len(eligible))
        Xe = bundle["scaler"].transform(eligible[cols].fillna(pd.Series(med)))
        dist, idx = bundle["nn"].fit(Xe).kneighbors(q, n_neighbors=k)
        items = []
        for rank, (d, i) in enumerate(zip(dist[0], idx[0], strict=True), 1):
            r = eligible.iloc[i]
            # Missing nutrition is reported explicitly — never displayed as zero.
            missing = [c for c in cols if pd.isna(r.get(c))]
            allergy_status, allergy_evidence = self._allergy_status(
                has_allergen_data, allergies, r)
            name = None if pd.isna(r.get("product_name")) else str(r.get("product_name"))
            items.append({
                "rank": rank,
                "product_name": name,
                "food_type": None if pd.isna(r.get("food_type")) else str(r.get("food_type")),
                "brands": None if pd.isna(r.get("brands")) else str(r.get("brands")),
                "energy_kcal": _f(r.get("energy_kcal")), "proteins_100g": _f(r.get("proteins_100g")),
                "fat_100g": _f(r.get("fat_100g")), "carbs_100g": _f(r.get("carbs_100g")),
                "sugars_100g": _f(r.get("sugars_100g")), "fiber_100g": _f(r.get("fiber_100g")),
                "sodium_100g": _f(r.get("sodium_100g")),
                "health_score": None if pd.isna(r.get("health_score")) else float(r.get("health_score")),
                "missing_nutrition": missing,
                "distance": round(float(d), 4),
                "why": (f"Selected by KNN closeness to the '{goal_key}' reference nutrient "
                        f"profile after filters (scaled Euclidean distance {float(d):.3f}; "
                        f"closeness is not a suitability guarantee)"),
                "explanation": {
                    "source_dataset": source_file,
                    "serving_basis": "per 100 g",
                    "cuisine_evidence": {
                        "class": None if pd.isna(r.get("cuisine_evidence")) else str(r.get("cuisine_evidence")),
                        "matched_term": None if pd.isna(r.get("evidence_term")) else str(r.get("evidence_term")),
                        "branded": False if pd.isna(r.get("is_branded")) else bool(r.get("is_branded")),
                    },
                    "restrictions_checked": [e.get("restriction", e.get("allergy")) for e in enforced],
                    "allergy_status": allergy_status,
                    "allergy_evidence": allergy_evidence,
                    "rank_reason": (f"KNN rank #{rank} of {len(eligible)} eligible foods: "
                                    f"scaled Euclidean distance {round(float(d), 4)} to the '{goal_key}' "
                                    f"reference profile over {', '.join(cols)}"),
                    "missing_fields": missing,
                    "note": ("Numerical closeness is not proof of suitability or safety; "
                             "see allergy_status and missing_fields."),
                },
            })
        return {**base, "items": items}

    # ---------------- meals: eligible foods + recipes ----------------
    @staticmethod
    def _recipe_constraints(profile: dict, restrictions: list) -> dict:
        low = [_norm(r) for r in restrictions]
        veg = any(v in low for v in ("vegetarian", "veg"))
        pref = str(profile.get("diet_preference", "any"))
        if veg and pref.lower() == "any":
            pref = "vegetarian"  # documented mapping; reported in explain output
        max_time = profile.get("max_time_min")
        if max_time is not None:
            try:
                max_time = float(max_time)
            except (TypeError, ValueError):
                raise ValueError("max_time_min must be numeric")
            if max_time <= 0:
                raise ValueError("max_time_min must be positive")
        course = profile.get("course", "main course")
        if course is not None and str(course).strip().lower() in ("", "any"):
            course = None
        return {"diet_preference": pref,
                "vegetarian_mapped": veg and pref.lower() == "vegetarian",
                "course": course,
                "max_time_min": max_time,
                "allergies": profile.get("allergies", []) or [],
                "low_sugar": any("sugar" in r for r in low),
                "low_sodium": any("sodium" in r for r in low)}

    def _recommend_meals(self, constraints: dict) -> dict:
        from .recipes import match_recipes
        return match_recipes(self._recipes, constraints)

    @staticmethod
    def _eligible_food_groups(eligible: pd.DataFrame, catalog: pd.DataFrame) -> dict:
        from .recipes import catalog_food_group
        groups: dict = {}
        for _, r in eligible.iterrows():
            name = None if pd.isna(r.get("product_name")) else str(r.get("product_name"))
            g = catalog_food_group(name or "")
            groups.setdefault(g, []).append({
                "name": name,
                "eligibility_status": "eligible",
                "evidence": f"indian_catalog.csv ({r.get('cuisine_evidence')}: "
                            f"{r.get('evidence_term')})",
                "energy_kcal": _f(r.get("energy_kcal")),
                "proteins_100g": _f(r.get("proteins_100g")),
            })
        return groups

    @staticmethod
    def _excluded_foods(catalog: pd.DataFrame, eligible: pd.DataFrame,
                        allergies: list, restrictions: list) -> list:
        dropped = catalog.loc[catalog.index.difference(eligible.index)]
        low = [_norm(r) for r in restrictions]
        out = []
        for _, r in dropped.iterrows():
            name = None if pd.isna(r.get("product_name")) else str(r.get("product_name"))
            reasons = []
            if allergies:
                reasons.append("allergy requested but catalog has no allergen data "
                               "(excluded as unverifiable)")
            if any("sodium" in x for x in low):
                reasons.append("sodium_100g > 0.4 g or missing (fail-closed)")
            if any("sugar" in x for x in low):
                reasons.append("sugars_100g > 5.0 g or missing (fail-closed)")
            out.append({"name": name, "eligibility_status": "excluded",
                        "evidence": "; ".join(reasons) or "filtered out"})
        return out

    @staticmethod
    def _collect_warnings(base: dict, allergies: list, restrictions: list, meals: dict | None) -> list:
        w = []
        if base.get("allergen_warning"):
            w.append("Allergy safety cannot be certified: " + base["allergen_warning"])
        for n in base.get("filter_notes", []):
            if n.get("type") in ("restriction_unsupported", "allergy_unmapped"):
                w.append(f"Unsupported: {n.get('value')} ({n.get('type')})")
        if meals is not None:
            s = meals["filtering_summary"]
            if s["recipes_after_time_filter"] == 0 and s["recipes_before_filtering"] > 0:
                w.append("No recipes passed all filters; constraints were NOT relaxed. "
                         "See filtering_summary for the stage that removed candidates.")
            if s["recipes_needs_review"] > 0 and allergies:
                w.append(f"{s['recipes_needs_review']} recipes need ingredient review "
                         f"and are not verified recommendations.")
        return w

    @staticmethod
    def _allergy_status(has_flags: bool, allergies: list, row) -> tuple:
        if not allergies:
            return ("not-checked",
                    "No allergy requested, so no allergy check was performed.")
        if not has_flags:
            return ("unknown",
                    "Catalog has no allergen data; compatibility cannot be established.")
        checked = []
        for a in allergies:
            flag = next((f for sub, f in ALLERGY_TO_FLAG.items() if sub in _norm(a)), None)
            if flag is not None and not bool(row.get(flag, False)):
                checked.append(f"{a} ({flag}=false in source data)")
        if checked:
            return ("verified-compatible",
                    "Excluded by source catalog flags: " + "; ".join(checked) +
                    ". Verified against source flags only, not a safety guarantee.")
        return ("unknown", "Compatibility could not be established from source data.")

    # ---------------- workout ----------------
    def recommend_workout(self, profile: dict) -> dict:
        """Filter + rank workout catalog. No trained classifier (blocker documented).

        `top_n` = TOTAL alternative programs returned = 1 primary plan the user
        follows + up to 3 alternatives to choose from INSTEAD (never all of them).
        """
        if self._workout is None:
            raise FileNotFoundError(
                "Workout catalog not available (workout_catalog.csv missing). "
                "Diet endpoints are unaffected.")
        if not isinstance(profile, dict):
            raise ValueError("profile must be a dict")
        df = self._workout
        goal = _norm(profile.get("goal", ""))
        level = _norm(profile.get("experience_level", profile.get("level", "")))
        equip = [_norm(e) for e in (profile.get("equipment", []) or [])]
        avail = profile.get("available_minutes")
        top_n = int(profile.get("top_n", 1))
        if not 1 <= top_n <= 4:
            raise ValueError("top_n must be between 1 and 4 "
                             "(1 primary plan + up to 3 alternatives)")
        if avail is not None:
            try:
                avail = float(avail)
            except (TypeError, ValueError):
                raise ValueError("available_minutes must be numeric")

        mask = pd.Series(True, index=df.index)
        unmet = []
        if goal:
            hit = df["goal"].fillna("").str.lower().str.contains(goal, na=False)
            if hit.any():
                mask &= hit
            else:
                unmet.append(f"goal={goal!r}: no exact match, ignored")
        if level:
            hit = df["level"].fillna("").str.lower().str.contains(level, na=False)
            if hit.any():
                mask &= hit
            else:
                unmet.append(f"level={level!r}: no exact match, ignored")
        if equip:
            # Hard equipment filter: exact normalized match against the program's
            # listed equipment. Unsupported values are NEVER mapped to another
            # category; incompatible programs are excluded and reported.
            prog_eq = df["equipment"].fillna("").str.strip().str.lower()
            catalog_eq = sorted(e for e in prog_eq.unique().tolist() if e)
            hit = prog_eq.isin(equip)
            unmatched = [e for e in equip if e not in catalog_eq]
            if unmatched:
                unmet.append(f"equipment {unmatched}: not in catalog {catalog_eq}; "
                             f"programs requiring it excluded")
            if hit.any():
                mask &= hit
            else:
                mask &= False
                unmet.append("equipment: no compatible programs; all candidates excluded")
        if avail is not None:
            hit = df["time_per_workout"].fillna(9e9) <= avail + 15
            if hit.any():
                mask &= hit
            else:
                unmet.append(f"available_minutes={avail}: nothing fits, ignored")

        cand = df[mask].copy()
        base = {"method": "catalog_filter_rank (no trained classifier — see meta)",
                "usage": ("Follow ONE plan: the primary plan, or ONE alternative "
                          "instead of it — never all of them."),
                "version": self._meta.get("version")}
        if cand.empty:
            return {**base, "primary": None, "alternatives": [],
                    "unmet": unmet or ["No programs satisfy all constraints."]}
        # Transparent ranking on actual catalog fields: goal hits + level hit +
        # duration fit (fits requested minutes scores higher).
        cand["__score"] = 0.0
        if goal:
            cand["__score"] += cand["goal"].fillna("").str.lower().str.count(goal)
        if level:
            cand["__score"] += cand["level"].fillna("").str.lower().str.contains(level, na=False).astype(float)
        if avail is not None:
            cand["__score"] += (cand["time_per_workout"].fillna(9e9) <= avail).astype(float)
        cand["__score"] -= (cand["time_per_workout"].fillna(60) / 120.0)
        ranked = cand.sort_values("__score", ascending=False)
        plans = []
        for title, grp in ranked.groupby("title", sort=False):
            if len(plans) >= top_n:
                break
            plans.append(self._build_plan(str(title), grp, avail))
        primary, alternatives = plans[0], plans[1:]
        for i, alt in enumerate(alternatives, 1):
            alt["choice_label"] = (f"Alternative {i} — follow INSTEAD of the primary "
                                   f"plan, not as well as it")
        primary["choice_label"] = "Primary plan — follow this one"
        return {**base, "primary": primary, "alternatives": alternatives,
                "n_candidates": int(cand["title"].nunique()),
                "top_n": top_n, "unmet": unmet}

    @staticmethod
    def _build_plan(title: str, grp, avail) -> dict:
        first = grp.iloc[0]
        ex_list = [{"exercise": str(r["exercise_name"]), "sets": _f(r["sets"]),
                    "reps": _f(r["reps"]), "intensity": _f(r["intensity"]),
                    "week": _f(r["week"]), "day": _f(r["day"])}
                   for _, r in grp.head(12).iterrows()]
        est = _f(first["time_per_workout"])
        if avail is None:
            duration_check = {"requested": None, "estimated": est,
                              "fits": None,
                              "note": "No requested duration given; no fit check performed."}
        elif est is None:
            duration_check = {"requested": avail, "estimated": None,
                              "fits": None,
                              "note": "Duration cannot be estimated from the data; no exact match claimed."}
        else:
            duration_check = {"requested": avail, "estimated": est,
                              "fits": bool(est <= avail),
                              "note": ("Fits the requested duration." if est <= avail
                                       else f"Exceeds the requested {avail:g} min by ~{est - avail:g} min.")}
        return {
            "program": title,
            "equipment": None if pd.isna(first["equipment"]) else str(first["equipment"]),
            "level": None if pd.isna(first["level"]) else str(first["level"]),
            "goal": None if pd.isna(first["goal"]) else str(first["goal"]),
            "time_per_workout": est,
            "duration_check": duration_check,
            "n_exercises_listed": int(len(grp)),
            "score": round(float(grp["__score"].max()), 3),
            "score_basis": "goal matches + experience-level match + duration fit (actual catalog fields)",
            "exercises": ex_list,
        }


def _f(v):
    try:
        return None if pd.isna(v) else round(float(v), 3)
    except Exception:
        return None


def _py(v):
    """Convert numpy/pandas scalars to JSON-serializable Python natives."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v
