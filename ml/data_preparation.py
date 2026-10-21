"""Reproducible data preparation from the five current datasets/ files only.

Outputs consumed by ml/train.py (and ultimately artifacts/):
  workout frame   <- datasets/smartfit_workout_dataset.csv
  nutrition frame <- datasets/nutrition_dataset.csv
  food catalog    <- datasets/Anuvaad_INDB_2024.11.xlsx (per-100g, Indian DB)
  exercise library<- datasets/exercises.json

Rules:
- Raw source files are NEVER edited; cleaning happens here and every removed
  row/badged value is counted in the returned .attrs so training logs it.
- The old boostcamp program catalog (program_summary.csv), the missing diet/
  healthy-foods files, and indian_food.csv are RETIRED and not referenced.
"""
import json
from pathlib import Path

import pandas as pd

from .config import (
    WORKOUT_DATA_FILE, NUTRITION_DATA_FILE, FOOD_DB_FILE, EXERCISES_FILE,
    WORKOUT_TARGET, WORKOUT_FEATURES, DIET_TARGETS, DIET_FEATURES,
    ALLERGEN_FLAG_COLS,
)
from .allergens import derive_allergens


def prepare_workout_frame(src: Path = WORKOUT_DATA_FILE) -> pd.DataFrame:
    """Cleaned training frame for the workout RF classifier.

    Cleaning: exact-duplicate rows dropped (counted); Injury NaN -> "None"
    (the smartfit file encodes "no injury" as NaN); required columns asserted.
    """
    df = pd.read_csv(src)
    before = len(df)
    required = WORKOUT_FEATURES + [WORKOUT_TARGET]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"workout dataset missing columns: {missing}")
    n_dupes = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    n_no_injury = int(df["Injury"].isna().sum())
    df["Injury"] = df["Injury"].fillna("None")
    # Experience is optional upstream too (20 raw NaNs): explicit training value
    # 'Unspecified' keeps missing as a real model category (NaN -> 'unspecified'
    # in code is worse: it encodes junk text into a categorical).
    n_no_exp = int(df["Experience"].isna().sum())
    df["Experience"] = df["Experience"].fillna("Unspecified")
    for c in WORKOUT_FEATURES:
        df[c] = df[c].astype(str).str.strip()
    bad = int(df[WORKOUT_TARGET].isna().sum())
    df = df[df[WORKOUT_TARGET].notna()].reset_index(drop=True)
    df.attrs.update(rows_before=before, exact_dupes_removed=n_dupes,
                    injury_nan_to_None=n_no_injury,
                    experience_nan_to_Unspecified=n_no_exp,
                    target_nan_dropped=bad, rows_after=len(df))
    return df


def prepare_nutrition_frame(src: Path = NUTRITION_DATA_FILE) -> pd.DataFrame:
    """Cleaned training frame for the diet macro RF regressor + meal picker.

    Cleaning (all counted): rows whose first cell repeats the header (junk
    header-duplicate row) dropped; 'Weight Maintenance' folded into
    'Maintenance' (same meaning, counted); target columns coerced numeric and
    non-positive/missing rows dropped (never invented).
    """
    df = pd.read_csv(src)
    before = len(df)
    required = DIET_FEATURES + DIET_TARGETS
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"nutrition dataset missing columns: {missing}")
    # Junk rows: literal header repeated as data (first col == 'Dietary Preference' etc.)
    junk = df["Dietary Preference"].astype(str).str.strip() == "Dietary Preference"
    n_junk = int(junk.sum())
    df = df[~junk].reset_index(drop=True)
    n_wm = int((df["Fitness Goal"] == "Weight Maintenance").sum())
    df["Fitness Goal"] = df["Fitness Goal"].replace({"Weight Maintenance": "Maintenance"})
    for c in DIET_FEATURES:
        df[c] = df[c].astype(str).str.strip()
    for c in DIET_TARGETS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad = df[DIET_TARGETS].isna().any(axis=1) | (df["Daily Calorie Target"] <= 0)
    n_bad = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    df.attrs.update(rows_before=before, junk_header_rows_removed=n_junk,
                    weight_maintenance_merged=n_wm, nonpositive_missing_dropped=n_bad,
                    rows_after=len(df))
    return df


def prepare_food_catalog(src: Path = FOOD_DB_FILE) -> pd.DataFrame:
    """Anuvaad INDB adapter -> canonical per-100g food catalog.

    ANUVAAD_INDB values are per 100 g (Indian food composition database).
    Adapter (documented unit handling):
      food_name -> product_name (kept verbatim; never renamed/translated)
      energy_kcal stays, protein_g -> proteins_100g, fat_g -> fat_100g,
      carb_g -> carbs_100g, freesugar_g -> sugars_100g, fibre_g -> fiber_100g
      sodium_mg -> sodium_100g (mg divided by 1000; recorded in meta)
    Unit-error outliers (energy > 950 kcal/100 g or sodium > 100 g/100 g)
    are excluded from the active catalog; count recorded in attrs.
    Allergen flags (ALLERGEN_FLAG_COLS) are DERIVED from the food name by
    keyword rules in ml/allergens.py: positive keyword -> True, no match ->
    False ("not flagged", never "certified allergen-free"). Per-flag match
    counts are recorded in attrs.
    """
    df = pd.read_excel(src)
    before = len(df)
    n_dupes = int(df["food_code"].duplicated().sum())
    df = df.drop_duplicates(subset=["food_code"]).reset_index(drop=True)
    rename = {"food_name": "product_name", "protein_g": "proteins_100g",
              "fat_g": "fat_100g", "carb_g": "carbs_100g",
              "freesugar_g": "sugars_100g", "fibre_g": "fiber_100g"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df["sodium_100g"] = pd.to_numeric(df.pop("sodium_mg"), errors="coerce") / 1000.0
    for c in ["energy_kcal", "fat_100g", "carbs_100g", "sugars_100g",
              "fiber_100g", "proteins_100g", "sodium_100g", "energy_kj"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad = (df["energy_kcal"] > 950) | (df["sodium_100g"] > 100)
    n_outliers = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    keep = ["food_code", "product_name", "energy_kj"] + [
        c for c in ["energy_kcal", "proteins_100g", "fat_100g", "carbs_100g",
                    "sugars_100g", "fiber_100g", "sodium_100g"] if c in df.columns]
    out = df[keep].copy()
    # keyword-derived allergen flags (positive matches only)
    flag_frames = pd.DataFrame(
        [derive_allergens(n) for n in out["product_name"].astype(str)],
        index=out.index)
    for c in ALLERGEN_FLAG_COLS:
        out[c] = flag_frames[c].astype(bool)
    out.attrs.update(rows_before=before, exact_dupes_removed=n_dupes,
                     n_outliers_excluded=n_outliers, rows_after=len(out),
                     allergen_flag_counts={c: int(out[c].sum())
                                           for c in ALLERGEN_FLAG_COLS})
    return out


def load_exercise_library(src: Path = EXERCISES_FILE) -> pd.DataFrame:
    """Fixed-BC exercise library -> slim deterministic serving frame.

    Kept fields: id, name, body_part, equipment, category, instructions (en).
    Order is preserved from the source file; layout code depends on stable id
    order, never on dict iteration quirks.
    """
    raw = json.loads(Path(src).read_text())
    rows = []
    for i, e in enumerate(raw):
        instr = (e.get("instructions") or {}).get("en") or ""
        rows.append({"order": i,
                     "id": e.get("id"),
                     "name": e.get("name"),
                     "body_part": (e.get("body_part") or "").strip().lower(),
                     "equipment": (e.get("equipment") or "").strip().lower(),
                     "category": (e.get("category") or "").strip().lower(),
                     "instruction_steps": instr})
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["name"]).reset_index(drop=True)
    df.attrs.update(rows=len(df), source=src.name)
    return df


def fitness_missing_mask(df: pd.DataFrame, cols: list) -> pd.Series:
    """Per-row boolean: True if any requested nutrition column is missing."""
    return df[cols].isna().any(axis=1)


def survey_values() -> dict:
    """All distinct categorical values the models were trained on.

    Used by options endpoints so the UI can only submit values the model
    actually understands (never guessed).
    """
    w = prepare_workout_frame()
    n = prepare_nutrition_frame()
    return {
        "workout": {
            "goals": sorted(w["Goal"].unique().tolist()),
            "equipment": sorted(w["Equipment"].unique().tolist()),
            "levels": sorted(w["Experience"].unique().tolist()),
            "injuries": sorted(w["Injury"].unique().tolist()),
            "plans": sorted(w[WORKOUT_TARGET].unique().tolist()),
        },
        "diet": {
            "activity_levels": sorted(n["Activity Level"].unique().tolist()),
            "fitness_goals": sorted(n["Fitness Goal"].unique().tolist()),
            "dietary_preferences": sorted(n["Dietary Preference"].unique().tolist()),
        },
    }
