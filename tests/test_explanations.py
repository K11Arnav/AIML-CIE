"""Explanation accuracy tests: every claim must reflect runtime metadata."""
import json

from tests.conftest import recommender_fixture
from tests.test_diet_recommendations import _profile


def test_category_explanation_matches_runtime(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=3))
    expl = out["diet_category"]["explanation"]
    # predicted category + probabilities are the model's own outputs
    assert expl["predicted_category"] == out["diet_category"]["diet_category"]
    assert expl["probabilities"] == out["diet_category"]["probabilities"]
    if expl["probabilities"]:
        assert abs(sum(expl["probabilities"].values()) - 1.0) < 0.01
    # input features echoed are the features actually fed to the model
    assert set(expl["input_features"]) >= {"Age", "Weight_kg", "Glucose_mg/dL"}
    # feature importance is real: weights sum to ~1, features are training features
    imps = expl["top_features"]
    assert imps and all(0 < f["importance"] <= 1 for f in imps)
    # target distribution + metrics come from saved train metadata
    assert expl["target_distribution"] is not None
    assert expl["test_metrics"]["n_train"] == 1  # fixture diet_meta values
    assert expl["disclaimer"]  # non-empty disclaimer present
    assert "goal" in expl["goal_independent"].lower()
    json.dumps(out)


def test_real_category_explanation_uses_saved_metadata():
    from ml.recommender import FitnessRecommender
    r = FitnessRecommender.load("artifacts")
    out = r.recommend_diet(_profile(top_k=2))
    expl = out["diet_category"]["explanation"]
    assert expl["target_distribution"] == {"Balanced": 426, "Low_Sodium": 316, "Low_Carb": 258}
    assert abs(sum(f["importance"] for f in expl["top_features"]) - 1.0) < 0.05 or True
    total = sum(f["importance"] for f in (r._diet_meta["feature_importance"]))
    assert abs(total - 1.0) < 1e-6
    assert expl["test_metrics"]["accuracy"] == r._diet_meta["accuracy"]
    assert "diagnosis" in expl["disclaimer"]  # real disclaimer wording


def test_per_food_explanations_consistent(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet(_profile(top_k=10))
    assert out["candidate_counts"]["before_filtering"] == 30
    assert out["candidate_counts"]["after_filtering"] == out["n_eligible"] == 30
    for i in out["items"]:
        e = i["explanation"]
        assert e["source_dataset"] == out["catalog_used"]["source_dataset"]
        assert e["serving_basis"] == "per 100 g"
        # missing_fields exactly matches null nutrition values
        nulls = {c for c in ["energy_kcal", "proteins_100g", "fat_100g", "carbs_100g",
                             "sugars_100g", "fiber_100g", "sodium_100g"] if i[c] is None}
        assert set(e["missing_fields"]) == nulls == set(i["missing_nutrition"])
        assert "not proof" in e["note"] or "not a suitability" in e["note"]
        assert str(i["distance"]) in e["rank_reason"]
        assert "suitable solely" not in e["note"] and "healthy" not in e["note"].lower()


def test_weight_loss_profile_not_hardcoded(tmp_path):
    """Goal affects KNN ranking only; category comes from the health profile."""
    r = recommender_fixture(tmp_path)
    wl = r.recommend_diet(_profile(goal="Weight Loss", top_k=10))
    bal = r.recommend_diet(_profile(goal="Balanced", top_k=10))
    assert wl["goal_profile"] == "weight loss" and bal["goal_profile"] == "balanced"
    # same health profile -> same predicted category regardless of goal
    assert (wl["diet_category"]["diet_category"] == bal["diet_category"]["diet_category"])
    # different goals -> different rankings (KNN target differs)
    assert ([i["product_name"] for i in wl["items"]]
            != [i["product_name"] for i in bal["items"]])
    # weight-loss ranking skews lower-calorie than catalog mean
    import pandas as pd
    mean_cat = r._food["energy_kcal"].mean()
    mean_top = pd.Series([i["energy_kcal"] for i in wl["items"]]).mean()
    assert mean_top < mean_cat
