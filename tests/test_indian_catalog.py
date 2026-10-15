"""Indian-catalog tests: documented filter, membership, no invented foods."""
import pandas as pd

from ml.data_preparation import prepare_food_catalog, prepare_indian_catalog
from ml.indian_catalog import build_indian_catalog, classify
from tests.conftest import food_fixture


def test_classify_false_friends():
    assert classify("Cheese, cottage, creamed")[0] is None  # not paneer
    assert classify("Soybean, curd cheese")[0] is None  # tofu, not dahi
    assert classify("Groundcherries, (cape-gooseberries or poha), raw")[0] is None
    assert classify("Poulet roti")[0] is None
    assert classify("Thai green curry paste")[0] is None
    assert classify("Bread, chapati or roti, plain")[0] == "indian_dish"
    assert classify("Chickpea flour (besan)")[0] == "indian_dish"
    assert classify("Lentils, raw")[0] == "staple_ingredient"
    assert classify("Snacks, potato chips")[0] is None
    assert classify("Fast foods, nachos")[0] is None


def test_fixture_filter_keeps_all_and_marks_evidence(tmp_path):
    p = tmp_path / "f.csv"
    food_fixture(30).to_csv(p, index=False)
    out = prepare_indian_catalog(p)
    assert len(out) == 30
    assert set(out["cuisine_evidence"].unique()) <= {"indian_dish", "staple_ingredient"}
    assert out["evidence_term"].notna().all()


def test_junk_excluded(tmp_path):
    df = pd.DataFrame({
        "food_name": ["Lentils, raw", "Vanilla Flavour Quark",
                      "Fast foods, nachos", "Spices, turmeric, ground"],
        "food_type": ["Grains"] * 4, "calories": [100.0] * 4,
        "protein_g": [5.0] * 4, "fat_g": [1.0] * 4, "carbs_g": [20.0] * 4,
        "fiber_g": [2.0] * 4, "sugar_g": [1.0] * 4, "sodium_mg": [10.0] * 4,
        "health_score": [65] * 4,
    })
    p = tmp_path / "j.csv"
    df.to_csv(p, index=False)
    out = prepare_indian_catalog(p)
    assert out["product_name"].tolist() == ["Lentils, raw", "Spices, turmeric, ground"]


def test_real_artifact_membership_and_no_invention():
    """Every active catalog row satisfies the filter; every name exists in source."""
    from ml.data_preparation import prepare_food_catalog as _prep
    indian = pd.read_csv("artifacts/indian_catalog.csv")
    src = pd.read_csv("datasets/healthy_foods_database.csv")
    assert len(indian) > 50  # meaningful size
    assert set(indian["product_name"]) <= set(src["food_name"])  # nothing invented
    # idempotent on the prepared (deduped, unit-cleaned) frame
    redo = build_indian_catalog(_prep(), name_col="product_name")
    assert set(redo["product_name"]) == set(indian["product_name"])
    assert set(indian["cuisine_evidence"].unique()) <= {"indian_dish", "staple_ingredient"}
    assert (indian["cuisine_evidence"] == "indian_dish").sum() >= 5


def test_off_catalog_not_used_for_inference(tmp_path):
    from tests.conftest import recommender_fixture
    from tests.test_diet_recommendations import _profile
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=5))
    assert "foods_health_scores_allergens" not in out["catalog_used"]["source_dataset"]
    assert out["catalog_used"]["source_dataset"].startswith("indian_catalog")


def test_pipeline_never_rewrites_nutrition_values():
    """Anti-fabrication: every artifact row matches a real source row exactly
    (same name may appear twice with different values — both kept verbatim)."""
    indian = pd.read_csv("artifacts/indian_catalog.csv")
    src = pd.read_csv("datasets/healthy_foods_database.csv")
    cols = [("calories", "energy_kcal", 1.0), ("protein_g", "proteins_100g", 1.0),
            ("fat_g", "fat_100g", 1.0), ("carbs_g", "carbs_100g", 1.0),
            ("sugar_g", "sugars_100g", 1.0), ("fiber_g", "fiber_100g", 1.0),
            ("sodium_mg", "sodium_100g", 0.001)]
    for _, r in indian.iterrows():
        cand = src[src["food_name"] == r["product_name"]]
        assert len(cand) >= 1, r["product_name"]
        ok = False
        for _, s in cand.iterrows():
            match = True
            for cs, ca, sc in cols:
                a, b = r[ca], s[cs] * sc
                if pd.isna(a) and pd.isna(b):
                    continue
                if pd.isna(a) or pd.isna(b) or abs(a - b) > 1e-9:
                    match = False
                    break
            if match:
                ok = True
                break
        assert ok, f"no source row matches {r['product_name']}"


def test_load_requires_indian_catalog(tmp_path):
    from ml.recommender import FitnessRecommender
    with __import__("pytest").raises(FileNotFoundError):
        FitnessRecommender.load(tmp_path)


def test_diet_works_without_workout_catalog(tmp_path):
    """Collaborator flow: diet endpoints run without the 120 MB workout file."""
    import shutil
    from ml.recommender import FitnessRecommender
    from tests.test_diet_recommendations import _profile
    for f in ["diet_model.joblib", "knn.joblib", "indian_catalog.csv",
              "recipe_catalog.csv", "meta.json", "diet_meta.json"]:
        shutil.copy(f"artifacts/{f}", tmp_path / f)
    r = FitnessRecommender.load(tmp_path)
    out = r.recommend_diet(_profile(top_k=2))
    assert len(out["items"]) == 2 and len(out["recipes"]) > 0
    with __import__("pytest").raises(FileNotFoundError):
        r.recommend_workout({"top_n": 1})


def test_vegetarian_unsupported_but_unfiltered(tmp_path):
    from tests.conftest import recommender_fixture
    from tests.test_diet_recommendations import _profile
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(dietary_restrictions=["Vegetarian"], top_k=5))
    assert any(n["type"] == "restriction_unsupported" for n in out["filter_notes"])
    assert out["candidate_counts"] == {"before_filtering": 30, "after_filtering": 30}


def test_minimal_profile_uses_imputation_path(tmp_path):
    from tests.conftest import recommender_fixture
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet({})
    assert len(out["items"]) == 10  # top_k default; all-missing features imputed
    assert out["diet_category"]["diet_category"] in ("Balanced", "Low_Carb", "Low_Sodium")
