"""Unified profile tests: every field validated, mapped, and consumed."""
import pytest

from ml.unified import (GOALS, recommend_unified, normalize_unified,
                        to_diet_profile, to_workout_profile,
                        validate_unified)
from ml.calories import estimate_daily_calories
from tests.conftest import jsonable

RAW = {"age": 30, "height_cm": 165, "weight_kg": 65, "gender": "Female",
       "goal": "Muscle Gain", "equipment": "home dumbbells",
       "workout_duration_minutes": 45, "fitness_level": "beginner",
       "activity_level": "moderately active", "workout_days_per_week": 4,
       "injuries_or_limitations": "none", "dietary_preference": "any",
       "allergies": []}


def _raw(**over):
    p = dict(RAW)
    p.update(over)
    return p


def test_validate_accepts_full_profile():
    assert validate_unified(_raw()) is None


def test_goal_values_are_subset_of_workout_training_vocabulary(recommender):
    vals = set(recommender._meta["values"]["workout"]["goals"])
    assert {"Muscle Gain", "Weight Loss", "Flexibility", "General Health"} <= vals


def test_normalize_maps_all_frontend_fields():
    u = normalize_unified(_raw(injuries_or_limitations="knee"))
    assert u["goal"] == "Muscle Gain"          # smartfit exact value
    assert u["equipment"] == "Home Dumbbells"  # smartfit exact value
    assert u["injuries_or_limitations"] == "Knee"
    assert u["dietary_preference"] == "any"


def test_validation_failures():
    for bad in (_raw(age=3),
                _raw(height_cm=300),
                _raw(weight_kg=10),
                _raw(gender="other"),
                _raw(goal="bulk apart"),
                _raw(equipment="treadmill"),
                _raw(activity_level="hyper"),
                _raw(workout_duration_minutes=0),
                _raw(injuries_or_limitations="hip"),
                _raw(allergies="nuts")):
        assert validate_unified(bad) is not None, bad


def test_to_workout_profile_uses_dataset_vocabulary():
    p = to_workout_profile(normalize_unified(
        _raw(goal="Weight Loss", equipment="yoga mat",
             fitness_level="advanced", injuries_or_limitations="back")))
    assert p["goal"] == "Weight Loss"
    assert p["equipment"] == "Yoga Mat"
    assert p["experience_level"] == "Advanced"
    assert p["injury"] == "Back"
    assert p["available_minutes"] == 45


def test_to_diet_profile_maps_preference_and_goal():
    d = to_diet_profile(normalize_unified(_raw()))
    assert d["dietary_preference"] == "Omnivore"       # 'any' -> majority, documented
    assert d["dietary_preference_any"] is True
    assert d["activity_level"] == "Moderately Active"
    assert d["fitness_goal"] in {"Weight Loss", "Muscle Gain", "Maintenance"}
    d2 = to_diet_profile(normalize_unified(_raw(dietary_preference="vegan")))
    assert d2["dietary_preference"] == "Vegan"


def test_recommend_unified_end_to_end(recommender, tmp_path):
    out = jsonable(recommend_unified(recommender, _raw()), tmp_path)
    assert out["success"] is True
    assert set(out["workout"]["raw_probabilities"])     # model ran with all features
    assert out["diet"]["predicted"]["Protein"] > 0
    assert out["daily_calorie_target_formula"]["kcal_per_day"] > 0
    # no injury -> no injury warning
    assert out["workout"]["unmet"] == []


def test_injury_selected_flows_to_model_and_warning(recommender, tmp_path):
    out = jsonable(recommend_unified(
        recommender, _raw(injuries_or_limitations="knee")), tmp_path)
    assert out["profile"]["injuries_or_limitations"] == "Knee"
    primary_injury = out["workout"]["primary"]["injury"]
    assert primary_injury == "Knee"
    assert any("knee" in w.lower() for w in out["workout"]["unmet"])


def test_calorie_formula_4_levels():
    base_args = (30, 165, 65, "Female")
    assert 1300 <= estimate_daily_calories(*base_args)["kcal_per_day"] <= 2400
    assert estimate_daily_calories(*base_args, "lightly active")["kcal_per_day"] == \
        estimate_daily_calories(*base_args, "Lightly Active")["kcal_per_day"]
    with pytest.raises(ValueError):
        estimate_daily_calories(*base_args, "energetic")
