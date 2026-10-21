"""Workout recommender tests: model-driven, equipment-constrained, honest."""
import pytest

from tests.conftest import jsonable
from tests.conftest import recommender as rec_fixture


@pytest.fixture()
def rec(recommender):
    return recommender


PROFILE = {"age": 28, "gender": "Male", "weight_kg": 80, "height_cm": 180,
           "goal": "Muscle Gain", "equipment": "Full Home Gym",
           "experience_level": "Beginner", "injury": "None",
           "available_minutes": 45, "workout_days_per_week": 4}


def test_full_profile_consumed_by_model(rec):
    """Every profile field must reach the model inputs."""
    out = rec.predict_workout_plan(PROFILE)
    inputs = out["inputs"]
    for key in ["Age", "Gender", "Weight_kg", "Height_cm", "Goal",
                "Equipment", "Experience", "Injury"]:
        assert key in inputs

    assert inputs["Gender"] == "Male" and inputs["Age"] == 28
    assert inputs["Goal"] == "Muscle Gain" and inputs["Equipment"] == "Full Home Gym"


def test_primary_plan_and_alternatives(rec, tmp_path):
    out = jsonable(rec.recommend_workout({**PROFILE, "top_n": 3}), tmp_path)
    assert out["primary"]["choice_label"].startswith("Primary plan")
    assert 1 <= 1 + len(out["alternatives"]) <= 3
    all_labeled = [out["primary"]] + out["alternatives"]
    assert any(a["plan"] != out["primary"]["plan"] for a in out["alternatives"])
    for p in all_labeled:
        assert p["plan"] and "model_probability" in p
    assert out["raw_probabilities"]


def test_no_protocolless_alternatives_when_top_n_1(rec):
    out = rec.recommend_workout(PROFILE)
    assert out["alternatives"] == []


def test_top_n_validation(rec):
    for bad in (0, 5):
        with pytest.raises(ValueError):
            rec.recommend_workout({**PROFILE, "top_n": bad})
    with pytest.raises(ValueError):
        rec.recommend_workout("not-a-dict")


def test_equipment_constraint(rec):
    """Yoga-equipment profiles can never get gym-only plans."""
    out = rec.recommend_workout({**PROFILE, "equipment": "Yoga Mat"})
    assert out["constraints"]["equipment"] == "Yoga Mat"
    from ml.plan_layout import compatible_plans
    ok = compatible_plans("Yoga Mat")
    assert out["primary"]["plan"] in ok


def test_duration_check_present(rec):
    out = rec.recommend_workout({**PROFILE, "available_minutes": 10})
    dc = out["primary"]["duration_check"]
    assert dc["requested"] == 10 and dc["estimated"] is not None
    assert isinstance(dc["fits"], bool)


def test_duration_none_states_no_check(rec):
    out = rec.recommend_workout({k: v for k, v in PROFILE.items()
                                 if k != "available_minutes"})
    dc = out["primary"]["duration_check"]
    assert dc["fits"] is None and "no fit check" in dc["note"].lower()


def test_days_default_note(rec):
    out = rec.recommend_workout({k: v for k, v in PROFILE.items()
                                 if k != "workout_days_per_week"})
    assert out["constraints"]["workout_days_per_week"] == 4  # documented default
    assert "defaulted" in (out["constraints"].get("note") or "")


def test_invalid_injury_rejected(rec):
    with pytest.raises(ValueError):
        rec.recommend_workout({**PROFILE, "injury": "hip"})


def test_invalid_equipment_rejected(rec):
    with pytest.raises(ValueError):
        rec.recommend_workout({**PROFILE, "equipment": "BARBELL"})


def test_invalid_goal_rejected(rec):
    with pytest.raises(ValueError):
        rec.recommend_workout({**PROFILE, "goal": "Walk to Strength Door"})


def test_exercises_come_from_library(rec):
    lib_names = set(rec._library["name"])
    out = rec.recommend_workout({**PROFILE})
    for day in out["primary"]["layout"]["days"]:
        for ex in day["exercises"]:
            assert ex["name"] in lib_names


def test_model_quality_reported_not_hidden(rec):
    out = rec.recommend_workout({**PROFILE})
    assert "test_accuracy" in out["model_quality"]
