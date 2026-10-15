"""Indian recipe catalog: cleaning, eligibility, and deterministic matching.

Source: datasets/indian_food.csv (255 rows, NEVER edited). Derived artifact:
artifacts/recipe_catalog.csv (cleaned copy + parse metadata).
Recipe rows are NEVER merged into the KNN food catalog.

Cleaning (reported in reports/indian_recipe_catalog_audit.md):
- prep_time/cook_time < 0 -> unknown (None). Never invented.
- state/region/flavor_profile of '-1'/empty -> None.
- diet/course normalized to lowercase; unexpected values kept verbatim + counted.
- exact duplicate rows removed (count reported).
- names and ingredient strings unchanged.
"""
import pandas as pd

from .config import ARTIFACTS_DIR, DATASETS_DIR
from .recipe_taxonomy import NONVEG, SALT_FAMILY, SWEETENERS, allergen_flags, group_of, normalize

RECIPE_SRC = DATASETS_DIR / "indian_food.csv"

TIME_LIMIT_DEFAULT = None


def parse_ingredients(text: str) -> list:
    """Split free-text ingredients on commas; keep originals verbatim."""
    return [t.strip() for t in str(text).split(",") if t.strip()]


def prepare_recipe_catalog(src=RECIPE_SRC) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(src)
    before = len(df)
    stats = {"rows_before": before, "columns": list(df.columns)}
    required = ["name", "ingredients", "diet", "prep_time", "cook_time",
                "flavor_profile", "course", "state", "region"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"recipe CSV missing columns: {missing_cols}")
    df = df.drop_duplicates().reset_index(drop=True)
    stats["exact_dupes_removed"] = before - len(df)
    for c in ["prep_time", "cook_time"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        bad = int(((df[c].isna()) | (df[c] < 0)).sum())
        stats[f"{c}_unknown"] = bad
        df[c] = df[c].where(df[c] >= 0)  # negatives/NaN -> None
    for c in ["state", "region", "flavor_profile"]:
        vals = df[c].astype(str).str.strip()
        cleaned = []
        for v in vals:
            if v in ("", "-1", "nan", "None", "NaN"):
                cleaned.append(None)
            elif not isinstance(v, str) and bool(pd.isna(v)):
                cleaned.append(None)  # pandas 3 may preserve NaN through astype(str)
            else:
                cleaned.append(v)
        df[c] = pd.Series(cleaned, dtype=object, index=df.index)
        stats[f"{c}_unknown"] = int(pd.Series(list(df[c])).isna().sum())
    for c in ["diet", "course"]:
        df[c] = df[c].astype(str).str.strip().str.lower()
    stats["diet_values"] = sorted(df["diet"].dropna().unique().tolist())
    stats["course_values"] = sorted(df["course"].dropna().unique().tolist())
    stats["rows_after"] = len(df)
    df["parsed_ingredients"] = df["ingredients"].map(parse_ingredients)
    return df, stats


def recipe_total_time(row) -> float | None:
    """Total minutes, or None when either part is unknown/negative.
    Unknown (or sentinel -1) never fits a limit."""
    p, c = _num(row.get("prep_time")), _num(row.get("cook_time"))
    if p is None or c is None or p < 0 or c < 0:
        return None
    return float(p) + float(c)


def evaluate_recipe(row, constraints: dict) -> dict:
    """Evaluate one recipe. Returns status + evidence; never invents data.

    constraints: {diet_preference: 'any'|'vegetarian'|'non vegetarian',
                  course: str|None, max_time_min: float|None,
                  allergies: [labels], low_sugar: bool, low_sodium: bool}
    Status: compatible_with_known_preferences | needs_ingredient_review | excluded
    """
    tokens = parse_ingredients(row["ingredients"])
    normed = [normalize(t) for t in tokens]
    groups = {t: group_of(t) for t in tokens}
    unknown = [t for t in tokens if groups[t] == "unknown"]
    reasons = []
    diet = str(row.get("diet", "")).lower()
    pref = (constraints.get("diet_preference") or "any").lower()

    # diet preference (label AND tokens; tokens win for safety)
    has_nonveg = [t for t in tokens if normalize(t) in NONVEG]
    if pref == "vegetarian":
        if diet != "vegetarian":
            return _out(row, tokens, groups, unknown, "excluded",
                        f"diet label is '{diet}', not vegetarian")
        if has_nonveg:
            return _out(row, tokens, groups, unknown, "excluded",
                        f"vegetarian-labeled but contains {has_nonveg} (label not trusted over ingredients)")
    elif pref == "non vegetarian" and diet != "non vegetarian":
        return _out(row, tokens, groups, unknown, "excluded",
                    f"diet label is '{diet}'")

    # course
    course = constraints.get("course")
    if course and str(row.get("course", "")).lower() != str(course).lower():
        return _out(row, tokens, groups, unknown, "excluded",
                    f"course is '{row.get('course')}', requested '{course}'")

    # allergies: known conflict -> excluded; unknown tokens -> needs review
    allergies = constraints.get("allergies") or []
    if allergies:
        unmapped = [a for a in allergies if not _allergy_key(a)]
        if unmapped:
            return _out(row, tokens, groups, unknown, "excluded",
                        f"allergy label(s) {unmapped} map to no known ingredient set",
                        warnings=["unmapped-allergy"])
        for a in allergies:
            hits = [t for t in tokens if _allergy_key(a) in allergen_flags(t)]
            if hits:
                return _out(row, tokens, groups, unknown, "excluded",
                            f"contains {hits} conflicting with allergy '{a}'")
        if unknown:
            reasons.append(f"unresolved ingredients {unknown}: safety unverifiable")
            return _out(row, tokens, groups, unknown, "needs_ingredient_review",
                        "; ".join(reasons))

    # low sugar: sweetener tokens excluded (explicit list)
    if constraints.get("low_sugar"):
        sweet = [t for t in tokens if normalize(t) in SWEETENERS]
        if sweet:
            return _out(row, tokens, groups, unknown, "excluded",
                        f"contains sweeteners {sweet}")

    # low sodium: salt-family tokens -> review (quantity unknown), not silent pass
    salt = [t for t in tokens if normalize(t) in SALT_FAMILY]
    if constraints.get("low_sodium") and salt:
        reasons.append(f"contains {salt}; sodium quantity unknown")
        return _out(row, tokens, groups, unknown, "needs_ingredient_review",
                    "; ".join(reasons))

    # time: unknown total never fits a limit
    total = recipe_total_time(row)
    limit = constraints.get("max_time_min")
    if limit is not None and (total is None or total > limit):
        return _out(row, tokens, groups, unknown, "excluded",
                    f"total time {total} min does not fit {limit} min limit"
                    if total is not None else
                    "time unknown; unknown times never fit a limit")

    if unknown and allergies:
        reasons.append(f"unresolved ingredients {unknown}")
        return _out(row, tokens, groups, unknown, "needs_ingredient_review",
                    "; ".join(reasons) or "compatible but has unresolved tokens")
    return _out(row, tokens, groups, unknown, "compatible_with_known_preferences",
                "all checks resolved; " + ("no unknown tokens" if not unknown else
                 f"unknown tokens present but no allergy requested: {unknown}"))


def _allergy_key(label: str) -> str | None:
    from .recipe_taxonomy import ALLERGY_SETS
    key = str(label).strip().lower()
    return next((k for k in ALLERGY_SETS if k in key or key in k), None)


def _out(row, tokens, groups, unknown, status, reason, warnings=None):
    total = recipe_total_time(row)
    matched = [t for t in tokens if groups[t] != "unknown"]
    coverage = round(len(matched) / len(tokens), 3) if tokens else 0.0
    return {
        "name": _text(row.get("name")),
        "ingredients": _text(row.get("ingredients")),
        "course": _text(row.get("course")),
        "diet": _text(row.get("diet")),
        "prep_time": _num(row.get("prep_time")),
        "cook_time": _num(row.get("cook_time")),
        "total_time": total,
        "state": _text(row.get("state")),
        "region": _text(row.get("region")),
        "flavor_profile": _text(row.get("flavor_profile")),
        "compatibility_status": status,
        "matched_ingredients": matched,
        "unmatched_ingredients": unknown,
        "ingredient_coverage": coverage,
        "explanation": reason,
        "warnings": warnings or [],
    }


def _num(v):
    try:
        return None if v is None or pd.isna(v) else float(v)
    except Exception:
        return None


def _text(v):
    try:
        return None if v is None or pd.isna(v) else str(v)
    except Exception:
        return None


def rank_compatible(evaluated: list) -> list:
    """Deterministic ranking: coverage desc, valid total time asc, name asc."""
    def key(e):
        t = e["total_time"]
        return (-e["ingredient_coverage"], t if t is not None else float("inf"), str(e["name"]))
    return sorted(evaluated, key=key)


def match_recipes(df: pd.DataFrame, constraints: dict) -> dict:
    """Staged filtering with counts. Returns compatible (ranked), needs_review,
    and a filtering summary. No silent relaxing: empty stays empty."""
    n0 = len(df)
    stage1, n_diet = [], 0
    for _, row in df.iterrows():
        r = row.to_dict()
        if _passes_stage1(r, constraints):
            stage1.append(r)
    n_diet = len(stage1)
    compatible, review, excluded_ingredient = [], [], 0
    no_time = dict(constraints, max_time_min=None)
    for r in stage1:
        ev = evaluate_recipe(r, no_time)  # time applied as its own stage below
        if ev["compatibility_status"] == "compatible_with_known_preferences":
            compatible.append(ev)
        elif ev["compatibility_status"] == "needs_ingredient_review":
            review.append(ev)
        else:
            excluded_ingredient += 1
    n_ing = len(compatible) + len(review)
    time_limited = constraints.get("max_time_min") is not None
    if time_limited:
        kept = [e for e in compatible if e["total_time"] is not None
                and e["total_time"] <= constraints["max_time_min"]]
        time_cut = len(compatible) - len(kept)
        compatible = kept
    else:
        time_cut = 0
    return {
        "compatible": rank_compatible(compatible),
        "needs_review": sorted(review, key=lambda e: str(e["name"])),
        "filtering_summary": {
            "recipes_before_filtering": n0,
            "recipes_after_diet_filter": n_diet,
            "recipes_after_ingredient_checks": n_ing,
            "recipes_needs_review": len(review),
            "recipes_excluded_by_time": time_cut,
            "recipes_after_time_filter": len(compatible),
        },
    }


def _passes_stage1(row: dict, constraints: dict) -> bool:
    diet = str(row.get("diet", "")).lower()
    pref = (constraints.get("diet_preference") or "any").lower()
    if pref == "vegetarian" and diet != "vegetarian":
        return False
    if pref == "non vegetarian" and diet != "non vegetarian":
        return False
    course = constraints.get("course")
    if course and str(row.get("course", "")).lower() != str(course).lower():
        return False
    return True


# Explicit catalog-food grouping for the "Foods you can eat" section.
# Ordered rules on the verbatim product name; first match wins. Reviewed
# against all 100 artifact rows (see test coverage assertion).
FOOD_GROUP_RULES = [
    ("spices", ["spices,"]),
    ("flours", ["flour", "besan", "semolina", "rava", "atta"]),
    ("legumes", ["lentil", "chickpea", "gram", "bean", "peas", "dal", "moong", "sattu", "papad"]),
    ("grains", ["rice", "bread", "naan", "roti", "wheat"]),
    ("nuts_seeds", ["nut", "peanut", "almond", "cashew", "sesame", "poppy"]),
    ("vegetables", ["spinach", "potato", "tomato", "carrot", "cauliflower",
                    "cabbage", "okra", "peas", "onion"]),
    ("fruits", ["guava", "mango", "banana", "papaya", "coconut"]),
    ("sweeteners", ["sugar", "jaggery", "honey"]),
]


def catalog_food_group(product_name: str) -> str:
    n = str(product_name).lower()
    for group, keys in FOOD_GROUP_RULES:
        if any(k in n for k in keys):
            return group
    return "other"
