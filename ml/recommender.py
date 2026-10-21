"""Backend-ready prediction interface. Loads saved artifacts once; no retraining
per request. Informational recommendations only — not medical advice.

Every model here is trained ONLY from the five current datasets/ files:
  workout  RF classifier on smartfit_workout_dataset.csv (8 profile features)
  diet     RF regressor on nutrition_dataset.csv (profile -> macros)
  foods    KNN over Anuvaad_INDB_2024.11.xlsx per-100g catalog
Allergen compatibility comes from ml/allergens.py keyword rules applied to
food and meal-suggestion names (the Anuvaad INDB ships no allergen columns).
The retired boostcamp program catalog is no longer referenced anywhere.
"""
import json
from pathlib import Path

import joblib
import pandas as pd

from .config import (ALLERGY_TO_FLAG, ARTIFACTS_DIR, GOAL_ALIASES,
                     GOAL_NUTRITION_TARGETS, WORKOUT_INJURY_VALUES)
from . import allergens as AL
from . import plan_layout as PL
from .plan_layout import (DEFAULT_DAYS_PER_WEEK, plan_layout)

MEAL_SLOTS = ["Breakfast Suggestion", "Lunch Suggestion",
              "Dinner Suggestion", "Snack Suggestion"]


def _norm(s, default=""):
    return str(s).strip().lower() if s is not None and str(s).strip() else default


def _f(v):
    try:
        return None if pd.isna(v) else round(float(v), 3)
    except Exception:
        return None


def _py(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v


class FitnessRecommender:
    def __init__(self, workout_bundle, knn, food: pd.DataFrame,
                 diet_bundle, meta: dict, diet_meta: dict,
                 artifacts_dir: Path, nutrition: pd.DataFrame,
                 library: pd.DataFrame):
        self._workout_model = workout_bundle
        self._knn = knn
        self._food = food
        self._diet_model = diet_bundle
        self._meta = meta
        self._diet_meta = diet_meta
        self._dir = Path(artifacts_dir)
        self._nutrition = nutrition
        self._library = library

    @classmethod
    def load(cls, artifacts_dir: str | Path = ARTIFACTS_DIR) -> "FitnessRecommender":
        import numpy as np  # noqa: F401  (joblib may need numpy on load path)
        d = Path(artifacts_dir)
        needed = ["workout_model.joblib", "diet_model.joblib", "knn.joblib",
                  "food_catalog.csv", "nutrition_catalog.csv",
                  "exercise_library.json", "meta.json", "diet_meta.json"]
        missing = [f for f in needed if not (d / f).exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing artifacts in {d}: {missing}. Run `python -m ml.train` first.")
        workout_bundle = joblib.load(d / "workout_model.joblib")
        diet_bundle = joblib.load(d / "diet_model.joblib")
        knn = joblib.load(d / "knn.joblib")
        food = pd.read_csv(d / "food_catalog.csv")
        nutrition = pd.read_csv(d / "nutrition_catalog.csv")
        library = json.loads((d / "exercise_library.json").read_text())
        library = pd.DataFrame(library)
        meta = json.loads((d / "meta.json").read_text())
        diet_meta = json.loads((d / "diet_meta.json").read_text())
        return cls(workout_bundle, knn, food, diet_bundle, meta, diet_meta, d,
                   nutrition=nutrition, library=library)

    # ---------------- workout ----------------
    WORKOUT_METHOD = ("RandomForest classifier trained on "
                      "datasets/smartfit_workout_dataset.csv "
                      "(features: Age, Gender, Weight_kg, Height_cm, Goal, "
                      "Equipment, Experience, Injury -> Recommended_Plan)")
    ALLERGEN_DATA_MSG = ("Allergen flags are keyword-derived from Anuvaad food "
                         "names (ml/allergens.py): positive matches are "
                         "excluded, but 'not flagged' is not a certified "
                         "allergen-free guarantee — verify labels.")

    def _workout_X(self, profile: dict) -> pd.DataFrame:
        feats = self._workout_model["features"]
        cols = feats["numeric"] + feats["categorical"]
        row = {
            "Age": profile.get("age"),
            "Gender": profile.get("gender", "unspecified"),
            "Weight_kg": profile.get("weight_kg"),
            "Height_cm": profile.get("height_cm"),
            "Goal": profile.get("goal", "unspecified"),
            "Equipment": profile.get("equipment", "unspecified"),
            "Experience": profile.get("experience_level") or "Unspecified",
            "Injury": profile.get("injury", "None") or "None",
        }
        if row["Injury"] not in WORKOUT_INJURY_VALUES:
            raise ValueError(
                f"injury must be one of: {', '.join(WORKOUT_INJURY_VALUES)}")
        return pd.DataFrame([{c: row[c] for c in cols}])

    def predict_workout_plan(self, profile: dict) -> dict:
        """RF predict with probabilities (no equipment constraint applied)."""
        X = self._workout_X(profile)
        pipe = self._workout_model["pipeline"]
        proba = pipe.predict_proba(X)[0]
        return {"probabilities": {c: round(float(p), 5)
                                  for c, p in zip(pipe.classes_, proba)},
                "inputs": {c: _py(X.iloc[0][c]) for c in X.columns}}

    @staticmethod
    def _plan_order(probabilities: dict, equipment: str | None) -> list:
        """Plan classes sorted by model probability, optionally constrained to
        plans doable with the user's equipment. This is constrained model
        decoding: only the mask is applied, never plan re-scoring."""
        items = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)
        if equipment is not None:
            ok = PL.compatible_plans(equipment)
            items = [(c, p) for c, p in items if c in ok]
        total = sum(p for _, p in items) or 1.0
        return [(c, p / total) for c, p in items]

    def recommend_workout(self, profile: dict) -> dict:
        """Model-driven workout recommendation.

        profile keys: age, gender, weight_kg, height_cm, goal (smartfit value),
        equipment (smartfit value), experience_level (Beginner/Intermediate/
        Advanced), injury (None/Knee/Ankle/Shoulder/Back), available_minutes,
        workout_days_per_week, top_n (1..4).
        """
        if not isinstance(profile, dict):
            raise ValueError("profile must be a dict")
        top_n = int(profile.get("top_n", 1))
        if not 1 <= top_n <= 4:
            raise ValueError("top_n must be between 1 and 4 "
                             "(1 primary plan + up to 3 alternatives)")
        for f in ("age", "weight_kg", "height_cm"):
            if f not in profile:
                raise ValueError(f"{f} is required for the workout model")
        equipment = profile.get("equipment")
        if equipment is not None and equipment not in PL.EQUIPMENT_TO_GROUPS:
            raise ValueError(
                f"equipment must be one of: {', '.join(PL.EQUIPMENT_TO_GROUPS)}")
        goal = profile.get("goal")
        if goal is not None and _norm(goal) not in {g.lower() for g in _goal_values(self._meta)}:
            raise ValueError(f"goal {goal!r} is not a model goal value")

        days = profile.get("workout_days_per_week") or DEFAULT_DAYS_PER_WEEK
        days_note = (None if profile.get("workout_days_per_week")
                     else f"workout_days_per_week not provided; defaulted to {DEFAULT_DAYS_PER_WEEK}")
        raw = self.predict_workout_plan(profile)
        order = self._plan_order(raw["probabilities"], equipment)
        if not order:
            raise ValueError(
                f"no plans compatible with equipment {equipment!r}; pick another option")
        primary, rest = order[0], order[1:]
        plans = [self._build_plan_response(primary, profile, equipment, days,
                                           rank=1)]
        for i, cand in enumerate(rest[: max(0, top_n - 1)], 1):
            alt = self._build_plan_response(cand, profile, equipment, days,
                                            rank=i + 1)
            alt["choice_label"] = (f"Alternative {i} — follow INSTEAD of the "
                                   "primary plan, not as well as it")
            plans.append(alt)
        out = plans[: top_n]
        out[0]["choice_label"] = "Primary plan — follow this one"
        base = {
            "method": self.WORKOUT_METHOD,
            "usage": ("Follow ONE plan: the primary plan, or ONE alternative "
                      "instead of it — never all of them."),
            "equipment_constrained": bool(equipment),
            "model_quality": {
                "test_accuracy": self._meta.get("workout_metrics", {}).get("accuracy"),
                "test_f1_macro": self._meta.get("workout_metrics", {}).get("f1_macro"),
                "dummy_accuracy": self._meta.get("workout_metrics", {}).get("dummy_accuracy"),
            },
            "raw_probabilities": raw["probabilities"],
            "constraints": {"equipment": equipment,
                            "workout_days_per_week": days,
                            **({"note": days_note} if days_note else {})},
            "unmet": [],
            "version": self._meta.get("version")}
        # day-split repeat note
        for p in out:
            if p["layout"]["split_repeats"]:
                note = f"Requested {days} days exceeds the plan's rotation; days repeat."
                p.setdefault("notes", []).append(note)
        return {**base, "primary": out[0], "alternatives": out[1:]}

    def _build_plan_response(self, cand: tuple, profile: dict, equipment: str,
                             days: int, rank: int) -> dict:
        plan_name, prob = cand
        layout = plan_layout(plan_name)
        week = PL.build_week(plan_name, self._library, equipment, days)
        avail = profile.get("available_minutes")
        est = week["estimated_minutes_per_day"]
        if avail is None:
            dc = {"requested": None, "estimated": est, "fits": None,
                  "note": "No requested minutes given; no fit check performed."}
        else:
            dc = {"requested": avail, "estimated": est, "fits": bool(est <= float(avail)),
                  "note": ("Estimated session fits the requested minutes."
                           if est <= float(avail) else
                           f"Estimated session exceeds {float(avail):g} min by ~{est - float(avail):g} min "
                           "(heuristic estimate — trim sets to fit).")}
        return {
            "rank": rank,
            "plan": plan_name,
            "model_probability": round(float(prob), 5),
            "equipment": equipment,
            "goal": profile.get("goal", "unspecified"),
            "experience_level": profile.get("experience_level", "unspecified"),
            "injury": profile.get("injury", "None") or "None",
            "workout_days_per_week": days,
            "style": week["style"],
            "sets": week["sets"],
            "reps": week["reps"],
            "duration_check": dc,
            "layout": week,
            "score_basis": ("RandomForest class probability (equipment-"
                            "constrained). Probabilities are model beliefs, not accuracy."),
        }

    # ---------------- diet ----------------
    DIET_METHOD = ("RandomForest regressor trained on "
                   "datasets/nutrition_dataset.csv "
                   "(features: Age, Gender, Height, Weight, Activity Level, "
                   "Fitness Goal, Dietary Preference -> calorie target + macros)")

    def _diet_X(self, profile: dict) -> pd.DataFrame:
        feats = self._diet_model["features"]
        cols = feats["numeric"] + feats["categorical"]
        row = {
            "Age": profile.get("age"),
            "Height": profile.get("height_cm"),
            "Weight": profile.get("weight_kg"),
            "Gender": profile.get("gender"),
            "Activity Level": profile.get("activity_level"),
            "Fitness Goal": profile.get("fitness_goal"),
            "Dietary Preference": profile.get("dietary_preference"),
        }
        missing = [c for c in cols if row[c] in (None, "")]
        if missing:
            raise ValueError(f"diet model requires fields: {', '.join(missing)}")
        return pd.DataFrame([{c: row[c] for c in cols}])

    def predict_diet_macros(self, profile: dict) -> dict:
        """Model predict: calorie target + protein/carbs/fat from the profile."""
        X = self._diet_X(profile)
        pipe = self._diet_model["pipeline"]
        arr = pipe.predict(X)[0]
        return {"targets": dict(zip(self._diet_model["targets"],
                                    [round(float(a), 1) for a in arr])),
                "inputs": {c: _py(X.iloc[0][c]) for c in X.columns},
                "model_quality": {
                    "mae": {t: m["mae"] for t, m in
                            (self._meta.get("diet_metrics", {}).get("per_target", {})).items()},
                    "r2": {t: m["r2"] for t, m in
                           (self._meta.get("diet_metrics", {}).get("per_target", {})).items()},
                }}

    def _allergy_flags(self, allergies):
        """Map user allergy labels -> derived allergen flags to filter on.

        Unknown labels never silently filter nothing: they are reported in
        notes/unmet. Returns (flags:set[str], notes:list, unmet:list).
        """
        notes, unmet, flags = [], [], set()
        for a in allergies:
            key = _norm(a)
            hit = next((f for sub, f in ALLERGY_TO_FLAG.items()
                        if sub in key), None)
            if hit:
                flags.add(hit)
            else:
                notes.append({"type": "allergy_unmapped", "value": a,
                              "reason": "Label maps to no known allergen "
                                        "flag; no filter was applied for it."})
                unmet.append(f"allergy {a!r} is not mapped to a catalog "
                             "flag — it was NOT screened")
        return flags, notes, unmet

    def _apply_allergy_filter(self, catalog: pd.DataFrame, flags: set):
        """Drop catalog rows whose derived allergen flags intersect the
        user's mapped allergies. Returns (filtered_catalog, excluded_count)."""
        if not flags:
            return catalog, 0
        mask = pd.Series(False, index=catalog.index)
        for flag in flags:
            if flag in catalog.columns:
                mask = mask | catalog[flag].astype(bool)
        filtered = catalog[~mask].reset_index(drop=True)
        return filtered, int(len(catalog) - len(filtered))

    def recommend_diet(self, profile: dict) -> dict:
        """Model-driven diet recommendation: predicted macros + KNN foods +
        meal suggestions retrieved from the nutrition dataset."""
        if not isinstance(profile, dict):
            raise ValueError("profile must be a dict")
        top_k = int(profile.get("top_k", 5))
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        allergies = [str(a) for a in (profile.get("allergies") or []) if str(a).strip()]
        goal = _norm(profile.get("goal", ""), None)
        goal_key = GOAL_ALIASES.get(goal, None)
        target_vec = (GOAL_NUTRITION_TARGETS.get(goal_key)
                      if goal_key else None)

        macros = self.predict_diet_macros(profile)
        flags, a_notes, a_unmet = self._allergy_flags(allergies)
        base = {
            "method": self.DIET_METHOD,
            "predicted": macros["targets"],
            "input_features": macros["inputs"],
            "model_quality_area": macros["model_quality"],
            "food_ranking_method": (
                "KNN ranks the Anuvaad per-100g food catalog by scaled Euclidean "
                "distance to the goal reference nutrient profile. Distance "
                "measures closeness, not suitability." if target_vec else
                "KNN ranks the Anuvaad per-100g catalog at its median nutrient "
                "profile (no goal given)."),
            "meals_method": (
                "Meal suggestions are retrieved from nutrition_dataset.csv rows "
                "matching your dietary preference, screened against the same "
                "keyword-derived allergen rules; none are generated."),
            "catalog_used": {
                "key": "food_catalog.csv (Anuvaad INDB per 100g)",
                "rows": int(len(self._food)),
                "allergen_data": True,
                "allergen_method": (
                    "Derived from food names by keyword rules in ml/allergens.py "
                    "(positive matches only). 'Not flagged' is NOT a guarantee — "
                    "verify ingredient labels.")},
            "version": self._meta.get("version")}
        if not target_vec:
            base["unmet"] = (base.get("unmet", []) +
                             [f"goal={goal!r}: unmapped for food ranking; used median profile"])
        base["unmet"] = base.get("unmet", []) + a_unmet
        # --- KNN food ranking (allergy-filtered) ---
        catalog, items_excluded = self._apply_allergy_filter(self._food, flags)
        n_before = int(len(self._food))
        if allergies:
            base["filter_notes"] = ([n for n in a_notes] + (
                [{"type": "allergy_filtered", "n_rows": items_excluded,
                  "flags": sorted(flags)}] if items_excluded else []))
        if catalog.empty:
            return {**base, "items": [],
                    "allergen_warning": (
                        "No foods remain after applying the mapped allergen "
                        "flags " + (f"{sorted(flags)} " if flags else "") +
                        "to keyword screening — no ranking is possible. "
                        "Keyword rules flag positives only ('not flagged' is "
                        "not a certified allergen-free guarantee)."),
                    "excluded": [{"type": "allergy_excluded_all",
                                  "n_rows": n_before}]}
        if allergies:
            base["allergy_screening"] = {
                "allergies": allergies,
                "flags_applied": sorted(flags),
                "foods_excluded": items_excluded,
                "foods_screened": n_before,
                "basis": ("Keyword-derived allergen flags on Anuvaad food "
                          "names (ml/allergens.py). Positive matches are "
                          "excluded; the residual risk of unlisted "
                          "ingredients remains — verify labels."),
                "disclaimer": ("Keyword screening is NOT a medical guarantee. "
                               "Cross-contamination and compound ingredients "
                               "cannot be detected from names alone.")}

        bundle = self._knn.get("general", self._knn)
        cols = bundle["cols"]
        med = bundle["medians"]
        q = bundle["scaler"].transform(
            pd.DataFrame([{c: (target_vec or med).get(c, med[c]) for c in cols}])
            if target_vec else pd.DataFrame([{c: med[c] for c in cols}]))
        top_k_eff = min(top_k, len(catalog))
        Xe = bundle["scaler"].transform(catalog[cols].fillna(pd.Series(med)))
        _, idx = bundle["nn"].fit(Xe).kneighbors(q, n_neighbors=top_k_eff)
        items = []
        for rank, i in enumerate(idx[0], 1):
            r = catalog.iloc[i]
            missing = [c for c in cols if pd.isna(r.get(c))]
            items.append({
                "rank": rank,
                "product_name": None if pd.isna(r.get("product_name")) else str(r.get("product_name")),
                "energy_kcal": _f(r.get("energy_kcal")),
                "proteins_100g": _f(r.get("proteins_100g")),
                "fat_100g": _f(r.get("fat_100g")),
                "carbs_100g": _f(r.get("carbs_100g")),
                "sugars_100g": _f(r.get("sugars_100g")),
                "fiber_100g": _f(r.get("fiber_100g")),
                "sodium_100g": _f(r.get("sodium_100g")),
                "allergen_flags": AL.flagged(
                    {c: bool(r.get(c, False)) for c in AL.ALLERGEN_FLAGS}),
                "missing_nutrition": missing,
                "rank_reason": (f"KNN rank #{rank} of {len(catalog)} catalog "
                                "foods over scaled per-100g columns "
                                f"{', '.join(cols)}"),
                "serving_basis": "per 100 g (Anuvaad INDB composition table)",
            })
        # --- meal suggestions: retrieved, screened against allergies ---
        meals = self._meal_suggestions(
            profile, macros["targets"].get("Daily Calorie Target"), flags)
        return {**base, "items": items, "meals": meals}

    def _meal_suggestions(self, profile: dict, predicted_calories: float | None,
                          allergy_flags: set) -> dict:
        """Closest-calorie nutrition row; when allergies are mapped, prefer
        the closest row whose suggestion texts screen clean (scan cap 60)."""
        pref = profile.get("dietary_preference")
        df = self._nutrition
        rows = df
        if pref and _norm(pref) != "any":
            rows = rows[rows["Dietary Preference"].str.casefold() == _norm(pref)]
        goal = profile.get("fitness_goal")
        by_goal = rows[rows["Fitness Goal"].str.casefold() == _norm(goal)] if goal else rows.head(0)
        ordered_pools = []
        if predicted_calories is not None:
            for pool in (by_goal, rows):
                if pool.empty:
                    continue
                diff = (pool["Daily Calorie Target"] - float(predicted_calories)).abs()
                ordered_pools.append(pool.loc[diff.sort_values().index])
        if not ordered_pools:
            ordered_pools = [rows] if not rows.empty else []
        row, row_warnings = None, {}
        for pool in ordered_pools:
            if row is not None and not row_warnings:
                break
            for idx in list(pool.index)[:60]:
                cand = self._nutrition.loc[idx]
                warnings = self._row_allergy_warnings(cand, allergy_flags)
                if row is None:
                    row, row_warnings = cand, warnings
                if not warnings:
                    row, row_warnings = cand, {}
                    break
            if row is not None and not row_warnings:
                break
        if row is None and not rows.empty:
            row = rows.iloc[0]
        if row is None:
            return {"matches": 0, "day": None,
                    "note": "No matching rows in nutrition_dataset.csv."}
        by_goal_n = int(len(by_goal))
        out = {
            "matches": int(len(rows)),
            "goal_matched_rows": by_goal_n,
            "selection_basis": ("Row from nutrition_dataset.csv with the calorie "
                                "target closest to the model prediction"
                                + ("; first candidate whose suggestions screen "
                                   "clean against your mapped allergen flags"
                                   if allergy_flags else "")
                                + "; retrieved suggestion, not generated."),
            "row_context": {"Activity Level": row.get("Activity Level"),
                            "Fitness Goal": row.get("Fitness Goal"),
                            "Dietary Preference": row.get("Dietary Preference"),
                            "Daily Calorie Target": _f(row.get("Daily Calorie Target")),
                            "Protein": _f(row.get("Protein")),
                            "Carbohydrates": _f(row.get("Carbohydrates")),
                            "Fat": _f(row.get("Fat"))},
            "suggestions": {slot: row.get(slot) for slot in MEAL_SLOTS},
            "allergy_screening": {
                "screened": bool(allergy_flags),
                "basis": "keyword-derived allergen rules (ml/allergens.py) "
                         "applied to the suggestion texts"
                if allergy_flags else "no mapped allergies — not screened",
                "warnings": row_warnings,
            },
        }
        return out

    @staticmethod
    def _row_allergy_warnings(row: pd.Series, flags: set) -> dict:
        """{slot: [flag,...]} for every meal-suggestion text that trips a
        mapped allergen flag; empty dict when the row screens clean."""
        if not flags:
            return {}
        warnings = {}
        for slot in MEAL_SLOTS:
            text = row.get(slot)
            if text is None or (isinstance(text, float) and pd.isna(text)):
                continue
            hit = AL.flagged({f: (v and f in flags)
                              for f, v in AL.screen_text(str(text)).items()})
            if hit:
                warnings[slot] = hit
        return warnings


def _goal_values(meta: dict) -> set:
    return set((meta.get("values", {}).get("workout", {}) or {}).get("goals", []))
