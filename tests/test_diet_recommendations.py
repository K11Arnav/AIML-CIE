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
    assert out["items"][0]["product_name"] is not None
    assert isinstance(out["items"][0]["allergen_flags"], list)
    assert "method" in out and "RandomForest" in out["method"]
    assert out["catalog_used"]["allergen_data"] is True


def test_goal_entered_via_reference_profile(rec, tmp_path):
    """weight-loss goal must rank foods against the configured reference vector
    and never silently use the median."""
    with_goal = jsonable(rec.recommend_diet(DIET_PROFILE), tmp_path)
    without_goal = jsonable(rec.recommend_diet({**DIET_PROFILE, "goal": None}), tmp_path)
    names_goal = [i["product_name"] for i in with_goal["items"]]
    names_median = [i["product_name"] for i in without_goal["items"]]
    assert "unmet" in without_goal and names_goal != names_median


def test_allergies_screened_not_fail_closed(rec):
    """Allergen flags (keyword-derived) now filter the ranking instead of
    returning an empty list."""
    out = rec.recommend_diet({**DIET_PROFILE, "allergies": ["Peanuts"]})
    screening = out["allergy_screening"]
    assert screening["allergies"] == ["Peanuts"]
    assert screening["flags_applied"] == ["contains_peanuts"]
    assert screening["foods_excluded"] == 1  # 'peanut chikki bar'
    assert "peanut" not in " ".join(i["product_name"] or "" for i in out["items"]).lower()
    for item in out["items"]:
        assert "contains_peanuts" not in item["allergen_flags"]


def test_dairy_allergy_excludes_paneer(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "allergies": ["Dairy"]})
    names = " ".join(i["product_name"] or "" for i in out["items"]).lower()
    assert "paneer" not in names
    assert "contains_dairy" not in [f for i in out["items"] for f in i["allergen_flags"]]


def test_vegetarian_excludes_meat_fish_eggs(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "dietary_preference": "Vegetarian"})
    names = " ".join(i["product_name"] or "" for i in out["items"]).lower()
    assert "chicken" not in names and "beef" not in names and "fish" not in names
    ps = out["preference_screening"]
    assert ps["preference"] == "vegetarian" and ps["foods_excluded"] >= 2
    assert any(rt["type"] == "diet_preference_excluded"
               for rt in out["filter_notes"])


def test_vegan_excludes_dairy_and_honey(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "dietary_preference": "Vegan"})
    names = " ".join(i["product_name"] or "" for i in out["items"]).lower()
    assert "paneer" not in names
    assert out["preference_screening"]["preference"] == "vegan"


def test_omnivore_no_preference_filtering(rec):
    out = rec.recommend_diet(DIET_PROFILE)
    assert "preference_screening" not in out
    assert not any(rt["type"] == "diet_preference_excluded"
                   for rt in out.get("filter_notes", []))


def test_meals_screened_when_allergies_mapped(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "allergies": ["Peanuts"]})
    ms = out["meals"]["allergy_screening"]
    assert ms["screened"] is True
    assert ms["basis"] and "keyword" in ms["basis"]
    assert isinstance(ms["warnings"], dict)


def test_unknown_allergy_reported_not_silent(rec):
    out = rec.recommend_diet({**DIET_PROFILE, "allergies": ["Dragon dander"]})
    assert any("Dragon dander" in u for u in out["unmet"])
    assert any(n["type"] == "allergy_unmapped"
               for n in out.get("filter_notes", []))


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
    out = rec._meal_suggestions(
        {**DIET_PROFILE, "dietary_preference": "any"}, 2000, set())
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
