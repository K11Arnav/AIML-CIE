"""Reproducible data preparation: build consolidated catalogs + diet frame.

Outputs (in artifacts/):
  indian_catalog.csv   - active Indian-food derived catalog
  workout_catalog.csv  - cleaned exercise-level catalog (selected columns)
"""
import ast
from pathlib import Path

import pandas as pd

from .config import (
    ARTIFACTS_DIR, DIET_FILE, FOOD_PRIMARY_FILE, WORKOUT_DETAILED_FILE,
    DIET_TARGET, DIET_ID_COLS, DIET_LEAKAGE_COLS,
)
from .indian_catalog import build_indian_catalog

WORKOUT_KEEP = ["title", "level", "goal", "equipment", "program_length",
                "time_per_workout", "week", "day", "exercise_name", "sets", "reps", "intensity"]


def _parse_list_cell(s):
    """Parse \"['A', 'B']\" style cells -> list of str; plain strings -> [s]."""
    if pd.isna(s):
        return []
    t = str(s).strip()
    if t.startswith("["):
        try:
            v = ast.literal_eval(t)
            return [str(x).strip() for x in v] if isinstance(v, list) else [t]
        except Exception:
            return [t]
    return [t]


def prepare_food_catalog(src: Path = FOOD_PRIMARY_FILE) -> pd.DataFrame:
    """Build the consolidated catalog, normalized to canonical per-100g columns.

    healthy_foods_database adapter (documented unit handling):
      food_name -> product_name (kept verbatim; never renamed/translated)
      calories -> energy_kcal, protein_g -> proteins_100g, fat_g -> fat_100g,
      carbs_g -> carbs_100g, sugar_g -> sugars_100g, fiber_g -> fiber_100g (all per 100g)
      sodium_mg -> sodium_100g  (mg divided by 1000; conversion recorded in manifest)
    Rows with unit-error outliers (calories > 950 per 100g, sodium_mg > 100000)
    are excluded from the active catalog; the source file is untouched.
    No allergen-flag columns are created: absent columns mean "unknown", and the
    recommender must never treat them as allergen-free.
    """
    df = pd.read_csv(src)
    before = len(df)
    n_dupes = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    rename = {"food_name": "product_name", "calories": "energy_kcal",
              "protein_g": "proteins_100g", "fat_g": "fat_100g",
              "carbs_g": "carbs_100g", "sugar_g": "sugars_100g",
              "fiber_g": "fiber_100g"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "sodium_mg" in df.columns:
        df["sodium_100g"] = pd.to_numeric(df["sodium_mg"], errors="coerce") / 1000.0
        df = df.drop(columns=["sodium_mg"])
    for c in ["energy_kcal", "fat_100g", "carbs_100g", "sugars_100g",
              "fiber_100g", "proteins_100g", "sodium_100g"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Normalize boolean flags only if flag columns exist (they don't
    # in the healthy catalog — and must not be invented here).
    for c in [c for c in df.columns if c.startswith("contains_")]:
        df[c] = df[c].map({True: True, False: False, "True": True, "False": False,
                           "true": True, "false": False}).fillna(False).astype(bool)
    bad = (df["energy_kcal"] > 950) | (df["sodium_100g"] > 100)
    n_outliers = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    df.attrs["rows_before"] = before
    df.attrs["n_dupes_removed"] = n_dupes
    df.attrs["n_outliers_excluded"] = n_outliers
    return df


def prepare_indian_catalog(src: Path = FOOD_PRIMARY_FILE) -> pd.DataFrame:
    """Active Indian-food catalog: healthy adapter + documented Indian filter.

    Returns canonical per-100g columns plus cuisine_evidence/evidence_term/
    is_branded metadata. Names kept verbatim. Raw source file untouched.
    """
    food = prepare_food_catalog(src)
    before = len(food)
    indian = build_indian_catalog(food, name_col="product_name")
    indian.attrs["rows_before_indian_filter"] = before
    return indian


def prepare_workout_catalog(src: Path = WORKOUT_DETAILED_FILE) -> pd.DataFrame:
    df = pd.read_csv(src, usecols=WORKOUT_KEEP)
    df = df.drop_duplicates().reset_index(drop=True)  # exact dupes only; keeps distinct sets/reps/day rows
    df["level_list"] = df["level"].map(_parse_list_cell)
    df["goal_list"] = df["goal"].map(_parse_list_cell)
    for c in ["program_length", "time_per_workout", "week", "day", "sets", "reps", "intensity"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def prepare_diet_frame(src: Path = DIET_FILE) -> pd.DataFrame:
    df = pd.read_csv(src)
    if DIET_TARGET not in df.columns:
        raise ValueError(f"Missing required target column {DIET_TARGET!r} in {src}")
    if df[DIET_TARGET].isna().any():
        raise ValueError("Diet target contains missing labels")
    df = df.drop_duplicates().reset_index(drop=True)
    # Missing categoricals -> explicit "None" level (33% missing restrictions/allergies, 20% disease)
    for c in ["Dietary_Restrictions", "Allergies", "Disease_Type"]:
        if c in df.columns:
            df[c] = df[c].fillna("None")
    return df


def diet_features(df: pd.DataFrame):
    """Return (X, y) with IDs and leakage columns excluded. Raises if target missing."""
    drop = [c for c in DIET_ID_COLS + DIET_LEAKAGE_COLS + [DIET_TARGET] if c in df.columns]
    X = df.drop(columns=drop)
    y = df[DIET_TARGET]
    # guard: target/leakage must not be in features
    assert DIET_TARGET not in X.columns and not any(c in X.columns for c in DIET_ID_COLS + DIET_LEAKAGE_COLS)
    return X, y


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    food = prepare_indian_catalog()
    food.to_csv(ARTIFACTS_DIR / "indian_catalog.csv", index=False)
    print(f"indian catalog: {len(food)} rows "
          f"(dishes={(food['cuisine_evidence'] == 'indian_dish').sum()})")
    w = prepare_workout_catalog()
    w.to_csv(ARTIFACTS_DIR / "workout_catalog.csv", index=False)
    print(f"workout catalog: {len(w)} rows, {w['title'].nunique()} programs, {w['exercise_name'].nunique()} exercises")


if __name__ == "__main__":
    main()
