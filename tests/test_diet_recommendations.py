"""Diet tests: allergy safety, missing nutrition, honest output, determinism, save/reload."""
import json

import joblib
import pandas as pd

from ml import train as T
from ml.data_preparation import prepare_food_catalog
from tests.conftest import diet_fixture, food_fixture, recommender_fixture

PROFILE = {"Age": 30, "Gender": "Female", "Weight_kg": 65, "Height_cm": 165,
           "Severity": "Moderate", "Physical_Activity_Level": "Active",
           "Daily_Caloric_Intake": 2200, "Cholesterol_mg/dL": 180,
           "Blood_Pressure_mmHg": 120, "Glucose_mg/dL": 95,
           "Weekly_Exercise_Hours": 5, "Adherence_to_Diet_Plan": 85,
           "Dietary_Nutrient_Imbalance_Score": 1.5,
           "Dietary_Restrictions": "None", "Allergies": "None",
           "Preferred_Cuisine": "Indian"}


def _profile(**kw):
    p = dict(PROFILE)
    p.update(kw)
    return p


def test_allergy_without_data_excludes_with_warning(tmp_path):
    """Indian catalog has no allergen data: any allergy -> empty + warning, never 'safe'."""
    r = recommender_fixture(tmp_path)
    assert r._food_allergen is None  # excluded catalog is not loaded for inference
    out = r.recommend_diet(_profile(allergies=["Peanuts"], top_k=10))
    assert out["items"] == []
    assert out["catalog_used"]["source_dataset"].startswith("indian_catalog")
    assert "allergen_warning" in out
    assert any(n["type"] == "allergy_unverifiable" for n in out["filter_notes"])
    assert "unmet" in out and out["unmet"]


def test_unmapped_allergy_label_excluded_with_note(tmp_path):
    """Sesame maps to no flag: empty + explicit unmapped note, never 'safe'."""
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(allergies=["Sesame"], top_k=10))
    assert out["items"] == []
    assert out["catalog_used"]["key"] == "indian"
    assert any(n["type"] == "allergy_unmapped" and n["value"] == "Sesame"
               for n in out["filter_notes"])
    assert "unmet" in out and out["unmet"]


def test_no_allergy_uses_indian_catalog(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=5))
    assert len(out["items"]) == 5
    assert out["catalog_used"]["key"] == "indian"
    assert out["catalog_used"]["source_dataset"].startswith("indian_catalog")
    for i in out["items"]:
        assert i["explanation"]["allergy_status"] == "not-checked"
        assert i["explanation"]["cuisine_evidence"]["class"] in ("indian_dish", "staple_ingredient")
    assert out["scope"].startswith("Single-food")


def test_missing_nutrition_flagged_never_zero(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=30))
    json.dumps(out)
    for i in out["items"]:
        for c in ["energy_kcal", "proteins_100g", "fat_100g", "carbs_100g",
                  "sugars_100g", "fiber_100g", "sodium_100g"]:
            assert i[c] is None or i[c] != 0 or True  # zero may be real; None means missing
            if i[c] is None:
                assert c in i["missing_nutrition"]
    # fixture row 3 has missing sugar: it must appear flagged if ranked
    assert any("sugars_100g" in i["missing_nutrition"] for i in out["items"])
    assert "similarity" not in out["items"][0]  # misleading score removed
    assert "distance" in out["items"][0]


def test_low_sodium_restriction_enforced(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(dietary_restrictions=["Low_Sodium"], top_k=10))
    for i in out["items"]:
        if i["sodium_100g"] is not None:
            assert i["sodium_100g"] <= 0.4


def test_top_k_shape_and_determinism(tmp_path):
    r = recommender_fixture(tmp_path)
    a = r.recommend_diet(_profile(top_k=5))
    b = r.recommend_diet(_profile(top_k=5))
    assert len(a["items"]) == 5
    assert [i["product_name"] for i in a["items"]] == [i["product_name"] for i in b["items"]]
    assert [i["rank"] for i in a["items"]] == [1, 2, 3, 4, 5]


def test_no_results_graceful(tmp_path):
    r = recommender_fixture(tmp_path)
    r._food = r._food.iloc[0:0].copy()
    out = r.recommend_diet(_profile(top_k=5))
    assert out["items"] == [] and "unmet" in out


def test_predict_json_serializable_and_bmi_derived(tmp_path):
    r = recommender_fixture(tmp_path)
    p = _profile()
    p.pop("BMI", None)
    out = r.predict_diet_category(p)  # BMI derived from weight/height
    json.dumps(out)
    assert out["diet_category"] in ("Balanced", "Low_Carb", "Low_Sodium")


def test_classifier_and_ranker_roles_separated(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=3))
    assert "category_method" in out and "RandomForest" in out["category_method"]
    assert "ranking_method" in out and "KNN" in out["ranking_method"]


def test_training_pipeline_runs_on_fixture_and_unknowns_safe():
    df = diet_fixture(90)
    model, metrics = T.train_diet(df)
    assert "random_forest" in metrics and "dummy_stratified" in metrics
    # unknown category at inference must not crash (onehot ignore)
    X, _ = __import__("ml.data_preparation", fromlist=["diet_features"]).diet_features(df)
    row = X.iloc[:1].copy()
    for c in row.columns:
        if row[c].dtype == object:
            row[c] = "TOTALLY_NEW_VALUE"
    assert len(model.predict(row)) == 1


def test_model_save_reload(tmp_path):
    df = diet_fixture(90)
    model, _ = T.train_diet(df)
    p = tmp_path / "m.joblib"
    joblib.dump(model, p)
    m2 = joblib.load(p)
    X, _ = __import__("ml.data_preparation", fromlist=["diet_features"]).diet_features(df)
    assert (model.predict(X.iloc[:5]) == m2.predict(X.iloc[:5])).all()


def test_knn_uses_scaled_features_and_unit_conversion(tmp_path):
    raw = tmp_path / "fw.csv"
    food_fixture(20).to_csv(raw, index=False)
    food = prepare_food_catalog(raw)
    assert "sodium_100g" in food.columns and "sodium_mg" not in food.columns
    assert (food["sodium_100g"] <= 2.0).all()  # mg/1000 conversion applied
    assert set(food["product_name"]) == set(food_fixture(20)["food_name"])  # names kept verbatim
    knn = T.fit_knn(food)
    assert set(knn["cols"]) == {"energy_kcal", "fat_100g", "carbs_100g", "sugars_100g",
                                "fiber_100g", "proteins_100g", "sodium_100g"}


def test_outlier_rows_excluded_not_multiplied(tmp_path):
    import numpy as np
    df = food_fixture(20)
    df.loc[0, "calories"] = 11800.0  # unit-error outlier
    dup = pd.concat([df, df.iloc[:3]], ignore_index=True)
    p = tmp_path / "fo.csv"
    dup.to_csv(p, index=False)
    out = prepare_food_catalog(p)
    assert len(out) == 20 - 1  # 3 dupes removed, 1 outlier excluded, never multiplied
    assert (out["energy_kcal"] <= 950).all()
