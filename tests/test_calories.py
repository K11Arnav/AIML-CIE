"""Daily calorie target: Mifflin-St Jeor estimate is correct, labeled, and wired
into the unified response (as a formula estimate, separate from the RF prediction)."""
from pathlib import Path

import pytest

from ml.calories import (ACTIVITY_FACTORS, DEFAULT_ACTIVITY,
                         estimate_daily_calories)
from ml.unified import recommend_unified
from tests.conftest import recommender as rec_fixture


@pytest.fixture()
def rec(request):
    return request.getfixturevalue("recommender")


def test_mifflin_known_values():
    # male 30y/180cm/80kg sedentary: BMR 1780 x 1.2
    out = estimate_daily_calories(30, 180, 80, "Male", "sedentary")
    assert out["kcal_per_day"] == 2136
    # female 30y/165cm/65kg moderate: BMR 1370.25 x 1.55 -> 2124
    out = estimate_daily_calories(30, 165, 65, "Female", "moderate")
    assert out["kcal_per_day"] == 2124
    assert out["source"] == "calculation"
    assert "Mifflin-St Jeor" in out["method"] and "goal-neutral" in out["method"]
    assert "not clinical advice" in out["disclaimer"].lower()


def test_activity_defaults_documented_not_silent():
    out = estimate_daily_calories(30, 165, 65, "Female", None)
    assert out["activity_assumed"] is True
    assert out["activity_level_used"] == DEFAULT_ACTIVITY == "moderate"
    out2 = estimate_daily_calories(30, 165, 65, "Female", "active")
    assert out2["activity_assumed"] is False
    assert out2["kcal_per_day"] > out["kcal_per_day"]


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        estimate_daily_calories(-30, 165, 65, "Female", "moderate")
    with pytest.raises(ValueError):
        estimate_daily_calories(30, 165, 65, "Other", "moderate")
    with pytest.raises(ValueError):
        estimate_daily_calories(30, 165, 65, "Female", "extreme")


def test_unified_response_carries_formula_estimate(recommender, tmp_path):
    out = recommend_unified(recommender, {
        "age": 30, "height_cm": 165, "weight_kg": 65, "gender": "Female",
        "goal": "Flexibility", "equipment": "yoga mat",
        "workout_duration_minutes": 30, "activity_level": "moderately active",
        "dietary_preference": "any"})
    t = out["daily_calorie_target_formula"]
    assert t["kcal_per_day"] == 2124  # matches formula, not a measurement
    assert t["source"] == "calculation"
    assert "workout" in out and "diet" in out  # one submit still returns both


def test_new_diet_ui_present_old_removed():
    """Source-level guard: only the new cards render; retired UI is gone."""
    src = Path("frontend/src/App.jsx").read_text()
    for legacy in ("Predicted category", "goal_profile", "filtering_summary",
                   "recipes_needs_review", "eligible_foods", "excluded_foods",
                   "Indian recipes you can consider", "prep_time", "cook_time",
                   "compatible programs", "Primary plan — follow this one</h3>"):
        assert legacy not in src, f"retired UI still present: {legacy}"
    for required in ("Model-predicted targets", "daily_calorie_target_formula",
                     "kcal", "per 100 g", "MealsCard", "Workout plan",
                     "duration_check", "layout", "model_probability"):
        assert required in src, f"new UI missing: {required}"
