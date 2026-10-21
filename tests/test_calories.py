"""Daily calorie target: Mifflin-St Jeor estimate is correct, labeled, and wired
into the unified response. No model artifact exists, so no prediction is claimed."""
from pathlib import Path

import pytest

from ml.calories import (ACTIVITY_FACTORS, DEFAULT_ACTIVITY,
                         estimate_daily_calories)
from ml.unified import recommend_unified
from tests.conftest import recommender_fixture


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


def test_unified_response_carries_estimate_not_fact(tmp_path):
    r = recommender_fixture(tmp_path)
    out = recommend_unified(r, {"age": 30, "height_cm": 165, "weight_kg": 65,
                                "gender": "Female", "goal": "weight loss",
                                "equipment": "bodyweight",
                                "workout_duration_minutes": 30})
    t = out["daily_calorie_target"]
    assert t["kcal_per_day"] == 2124  # matches formula, not a measurement
    assert t["source"] == "calculation" and t["activity_assumed"] is True
    assert "workout" in out and "diet" in out  # one submit still returns both


def test_legacy_diet_ui_removed_from_frontend():
    """Source-level guard: legacy diet output must not render; new cards must."""
    src = Path("frontend/src/App.jsx").read_text()
    for legacy in ("Predicted category", "goal_profile", "filtering_summary",
                   "recipes_needs_review", "eligible_foods", "excluded_foods",
                   "Top foods (by nutrient closeness)",
                   "No foods satisfy all constraints",
                   "relax restrictions", "Indian recipes you can consider",
                   "prep_time", "cook_time", "total_time",
                   "diet.warnings", "Allergy check:",
                   "all checks resolved"):
        assert legacy not in src, f"legacy diet UI still present: {legacy}"
    for required in ("Daily calorie target", "daily_calorie_target",
                     "Daily calorie target unavailable",
                     "Foods you can eat",
                     "No matching foods are available for the selected preferences and restrictions.",
                     "kcal", "per 100 g", "Ingredients:",
                     "Nutrition: unavailable",
                     "Workout plan", "duration_check"):
        assert required in src, f"new diet UI missing: {required}"
    assert "per serving" not in src.lower(), "per-100-g data must not be labeled per-serving"
    assert src.count("allergen_warning") <= 1, "at most one allergy warning site"
