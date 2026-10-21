"""Diet card contract tests: serving bases, no invented values, ingredient display,
missing-nutrition honesty, allergy-before-display for recipes.

Payload keeps prep_time/cook_time keys (contract + max_time_min filtering for direct
API callers); the UI must never render them — these tests pin the data facts the
cards rely on (per-100 g foods, nutrition-less recipes, fail-closed allergies).
"""
import re

import pytest

from ml.unified import recommend_unified
from tests.conftest import recommender_fixture

BASE = {"age": 30, "height_cm": 165, "weight_kg": 65, "gender": "Female",
        "goal": "weight loss", "equipment": "bodyweight",
        "workout_duration_minutes": 45}


def _diet(tmp_path, **kw):
    r = recommender_fixture(tmp_path)
    p = dict(BASE)
    p.update(kw)
    return r, recommend_unified(r, p)["diet"]


def test_food_items_state_per100g_basis_no_invented_servings(tmp_path):
    r, diet = _diet(tmp_path)
    assert diet["items"]
    for it in diet["items"]:
        assert it["explanation"]["serving_basis"] == "per 100 g"
        for invented in ("serving_size", "serving_g", "portion", "servings",
                         "calories_per_serving", "ingredients"):
            assert invented not in it
        # value equals the catalog per-100 g value (3-decimal display rounding only):
        # no serving conversion or rescaling math happened
        row = r._food[r._food["product_name"] == it["product_name"]].iloc[0]
        assert it["energy_kcal"] == pytest.approx(round(float(row["energy_kcal"]), 3))


def test_food_suitability_names_the_goal(tmp_path):
    _, diet = _diet(tmp_path)
    assert diet["items"]
    for it in diet["items"]:
        assert diet["goal_profile"] in it["why"]


def test_missing_nutrients_are_none_never_zero(tmp_path):
    _, diet = _diet(tmp_path, goal="general fitness")
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet({"Age": 30, "Gender": "Female", "Weight_kg": 65,
                            "Height_cm": 165, "goal": "balanced", "top_k": 30})
    flagged = [it for it in out["items"] if it["missing_nutrition"]]
    assert flagged, "fixture should surface at least one food with missing nutrients"
    for it in flagged:
        for col in it["missing_nutrition"]:
            assert it[col] is None and it[col] != 0


def test_recipes_carry_real_ingredients_no_nutrients(tmp_path):
    _, diet = _diet(tmp_path, goal="general fitness",
                    fitness_level="advanced", dietary_preference="any")
    assert diet["recipes"], "fixture main-course recipes should match"
    for rec in diet["recipes"]:
        assert rec["ingredients"] and isinstance(rec["ingredients"], str)
        assert rec["diet"] in ("vegetarian", "non vegetarian")
        for nutrient in ("energy_kcal", "proteins_100g", "fat_100g",
                         "carbs_100g", "fiber_100g", "sodium_100g"):
            assert nutrient not in rec, "recipes have no nutrient data: UI must show unavailable"


def test_recipe_diet_label_matches_data_and_tokens(tmp_path):
    _, diet = _diet(tmp_path, goal="general fitness", fitness_level="advanced",
                    dietary_preference="vegetarian")
    assert diet["recipes"]
    assert all(r["diet"] == "vegetarian" for r in diet["recipes"])


def test_allergy_recipes_never_compatible(tmp_path):
    """Peanut recipe excluded; any compatible recipe is fully resolved (no unknowns)."""
    r = recommender_fixture(tmp_path)
    out = r.recommend_diet({"Age": 30, "Gender": "Female", "Weight_kg": 65,
                            "Height_cm": 165, "goal": "balanced",
                            "allergies": ["Peanuts"], "course": "any",
                            "diet_preference": "any", "top_k": 5})
    names = [x["name"] for x in out["recipes"]]
    assert "Test peanut sweet" not in names
    for x in out["recipes"]:
        assert x["unmatched_ingredients"] == [], f"{x['name']} unresolved yet compatible"
        assert "safe" not in x["explanation"].lower()


def test_no_duration_values_in_unified_recipe_text(tmp_path):
    """Unified path sets no time limit, so no recipe text may carry durations to display."""
    _, diet = _diet(tmp_path, goal="general fitness", fitness_level="advanced")
    texts = [x["explanation"] for x in diet["recipes"]] + \
            [x["explanation"] for x in diet.get("recipes_needs_review", [])]
    assert texts
    for t in texts:
        assert not re.search(r"\b\d+(\.\d+)?\s*min\b", t), t
