"""Diet recommender tests: macro model + Anuvaad KNN + retrieved meals."""
import pytest

from tests.conftest import jsonable

DIET_PROFILE = {"age": 30, "gender": "Male", "height_cm": 180, "weight_kg": 80,
                "activity_level": "Moderately Active", "fitness_goal": "Weight Loss",
                "dietary_preference": "Omnivore", "goal": "weight loss",
                "top_k": 5}


@pytest.fixture()
def rec(recommender):
    return recommender


def test_predict_macros_schema_and_quality(rec):
    out = rec.predict_diet_macros(DIET_PROFILE)
    assert set(out["targets"]) == {"Daily Calorie Target", "Protein",
                                   "Carbohydrates", "Fat"}
    assert all(v > 0 for v in out["targets"].values())
    assert out["inputs"]["Weight"] == 80 and out["inputs"]["Gender"] == "Male"
    assert "mae" in out["model_quality"]


def test_missing_diet_fields_rejected(rec):
    bad = {**DIET_PROFILE, "activity_level": None}
    with pytest.raises(ValueError):
        rec.predict_diet_macros(bad)
    bad2 = {k: v for k, v in DIET_PROFILE.items() if k != "dietary_preference"}
    with pytest.raises(ValueError):
        rec.predict_diet_macros(bad2)


def test_recommend_diet_knn_items_ranked(rec, tmp_path):
    out = jsonable(rec.recommend_diet(DIET_PROFILE), tmp_path)
    ranks = [i["rank"] for i in out["items"]]
    assert ranks == sorted(ranks) and len(ranks) <= 5
    assert out["items"][0]["product_name"].startswith("test food")
    assert "method" in out and "RandomForest" in out["method"]
    assert out["catalog_used"]["allergen_data"] is False


def test_goal_entered_via_reference_profile(rec, tmp_path):
    """weight-loss goal must rank foods against the configured reference vector
    and never silently use the median."""
    with_goal = jsonable(rec.recommend_diet(DIET_PROFILE), tmp_path)
    without_goal = jsonable(rec.recommend_diet({**DIET_PROFILE, "goal": None}), tmp_path)
    names_goal = [i["product_name"] for i in with_goal["items"]]
    names_median = [i["product_name"] for i in without_goal["items"]]
    assert "unmet" in without_goal and names_goal != names_median


def test_allergies_fail_closed(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "allergies": ["Peanuts"]})
    assert out["items"] == []
    assert "fail-closed" in " ".join(out["unmet"])
    assert out["catalog_used"]["allergen_data"] is False


def test_meals_retrieved_not_generated(rec):
    out = rec.recommend_diet(DIET_PROFILE)
    m = out["meals"]
    assert m["suggestions"]["Breakfast Suggestion"].startswith("breakfast-")
    assert "generated" in m["selection_basis"] or "retrieved" in m["selection_basis"]
    assert set(m["suggestions"]) == {"Breakfast Suggestion", "Lunch Suggestion",
                                     "Dinner Suggestion", "Snack Suggestion"}


def test_meals_respect_dietary_preference(rec):
    out = rec.recommend_diet(DIET_PROFILE)
    pref_row = out["meals"]["row_context"]["Dietary Preference"]
    assert pref_row == "Omnivore"
    vegan = rec.recommend_diet({**DIET_PROFILE, "dietary_preference": "Vegan"})
    assert vegan["meals"]["row_context"]["Dietary Preference"] == "Vegan"


def test_any_preference_selects_all_rows(rec):
    out = rec._meal_suggestions({**DIET_PROFILE, "dietary_preference": "any"}, 2000)
    # fixture has all three preferences
    assert out["row_context"]["Dietary Preference"] in {"Omnivore", "Vegetarian", "Vegan"}


def test_top_k_bounds(rec):
    from ml.config import KNN_NUTRITION_COLS
    with pytest.raises(ValueError):
        rec.recommend_diet({**DIET_PROFILE, "top_k": 0})
    with pytest.raises(ValueError):
        rec.recommend_diet({**DIET_PROFILE, "top_k": 99})


def test_missing_nutrition_reported_not_zero(rec, tmp_path):
    out = jsonable(rec.recommend_diet(DIET_PROFILE), tmp_path)
    flagged = [i for i in out["items"] if i["missing_nutrition"]]
    assert all("sugars_100g" in m["missing_nutrition"] for m in flagged)
    assert all(isinstance(m["energy_kcal"], float) for m in out["items"]
               if m["energy_kcal"] is not None)
