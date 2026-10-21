"""Data-preparation unit tests (synthetic files; cleaning rules)."""
import pandas as pd
import pytest

from ml.data_preparation import (prepare_food_catalog, load_exercise_library,
                                 prepare_nutrition_frame,
                                 prepare_workout_frame)


def write_csv(df, path):
    df.to_csv(path, index=False)


def test_workout_frame_dedupe_and_injury_fill(tmp_path):
    base = pd.DataFrame({
        "Age": [30, 30], "Gender": ["Male", "Male"], "Weight_kg": [80, 80],
        "Height_cm": [180, 180], "Goal": ["Strength", "Strength"],
        "Equipment": ["Gym Membership", "Gym Membership"],
        "Experience": ["Beginner", "Beginner"], "Injury": [None, None],
        "Recommended_Plan": ["5x5 Compound Lifts", "5x5 Compound Lifts"],
    })
    p = tmp_path / "w.csv"
    write_csv(base, p)
    df = prepare_workout_frame(p)
    assert df.attrs["exact_dupes_removed"] == 1
    assert df.attrs["injury_nan_to_None"] == 1
    assert df["Injury"].tolist() == ["None"]


def test_nutrition_frame_drops_junk_and_merges_maintenance(tmp_path):
    df = pd.DataFrame({
        "Age": [25, 30, 30, 40], "Gender": ["Male", "Age", "Male", "Female"],
        "Height": [180, "Height", 180, 170], "Weight": [80, "Weight", 80, 60],
        "Activity Level": ["Sedentary", "Activity Level", "Sedentary", "Very Active"],
        "Fitness Goal": ["Weight Loss", "Weight Loss", "Weight Maintenance", "Maintenance"],
        "Dietary Preference": ["Omnivore", "Dietary Preference", "Vegan", "Vegan"],
        "Daily Calorie Target": [2000, 2000, 2000, 2200], "Protein": [100, 100, 100, 90],
        "Carbohydrates": [220, 220, 220, 240], "Fat": [60, 60, 60, 65],
    })
    p = tmp_path / "n.csv"
    write_csv(df, p)
    out = prepare_nutrition_frame(p)
    assert out.attrs["junk_header_rows_removed"] == 1  # repeated header row
    assert out.attrs["weight_maintenance_merged"] == 1
    assert set(out["Fitness Goal"]) == {"Weight Loss", "Maintenance"}
    assert out.attrs["rows_after"] == 3


def test_nutrition_frame_drops_nonpositive_targets(tmp_path):
    df = pd.DataFrame({
        "Age": [25, 30], "Gender": ["M", "F"], "Height": [180, 170],
        "Weight": [80, 60], "Activity Level": ["Sedentary", "Sedentary"],
        "Fitness Goal": ["Weight Loss", "Weight Loss"],
        "Dietary Preference": ["Omnivore", "Omnivore"],
        "Daily Calorie Target": [0, 2000], "Protein": [100, 100],
        "Carbohydrates": [220, 220], "Fat": [60, 60],
    })
    p = tmp_path / "n2.csv"
    write_csv(df, p)
    out = prepare_nutrition_frame(p)
    assert out.attrs["nonpositive_missing_dropped"] == 1
    assert out["Daily Calorie Target"].tolist() == [2000]


def test_exercise_library_loader(tmp_path):
    lib = [
        {"id": "0001", "name": "Sit-up", "body_part": "waist",
         "equipment": "body weight", "category": "waist",
         "instructions": {"en": "curl up"}},
    ]
    p = tmp_path / "ex.json"
    p.write_text(__import__("json").dumps(lib))
    df = load_exercise_library(p)
    assert len(df) == 1
    assert df.iloc[0]["instruction_steps"] == "curl up"
    assert df.iloc[0]["equipment"] == "body weight"


def test_food_catalog_adapter_renames_and_outliers(tmp_path):
    import openpyxl
    df = pd.DataFrame({
        "food_code": ["A001", "A002"],
        "food_name": ["Test dal", "Test ghee"],
        "primarysource": ["asc_manual", "asc_manual"],
        "energy_kj": [500, 1500], "energy_kcal": [100, 1200],
        "carb_g": [20, 1], "protein_g": [5, 1], "fat_g": [1, 12],
        "freesugar_g": [2, 0], "fibre_g": [3, 0], "sodium_mg": [200, 500],
    })
    p = tmp_path / "f.xlsx"
    df.to_excel(p, index=False)
    out = prepare_food_catalog(p)
    assert out.attrs["n_outliers_excluded"] == 1  # 1200 kcal/100g excluded
    assert list(out.columns) >= []
    assert "product_name" in out.columns and "sodium_100g" in out.columns
    row = out.iloc[0]
    # sodium converted mg -> g
    assert row["sodium_100g"] == pytest.approx(0.2)
    assert row["proteins_100g"] == pytest.approx(5.0)


def test_real_dataset_files_exist_and_have_schema():
    """Integration: the five active datasets must exist with model columns."""
    from ml.config import (WORKOUT_DATA_FILE, NUTRITION_DATA_FILE,
                           FOOD_DB_FILE, EXERCISES_FILE)
    for f in (WORKOUT_DATA_FILE, NUTRITION_DATA_FILE, FOOD_DB_FILE):
        assert f.exists(), f"missing active dataset: {f}"
    import json
    ex = json.loads(EXERCISES_FILE.read_text())
    assert len(ex) > 1000 and "body_part" in ex[0] and "equipment" in ex[0]
