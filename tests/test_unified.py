"""Unified profile tests: one submit feeds both recommenders with the same profile."""
import pytest

from ml.unified import (DIET_GOAL_MAP, EQUIPMENT_MAP, WORKOUT_GOAL_MAP,
                        injury_warning, normalize_unified, recommend_unified,
                        to_diet_profile, to_workout_profile, validate_unified)
from tests.conftest import recommender_fixture


def _raw(**kw):
    p = {"age": 30, "height_cm": 165, "weight_kg": 65, "gender": "Female",
         "goal": "weight loss", "equipment": "dumbbells",
         "workout_duration_minutes": 45}
    p.update(kw)
    return p


# --- contract / validation ---

def test_valid_minimal_profile():
    assert validate_unified(_raw()) is None
    u = normalize_unified(_raw())
    assert u["goal"] == "weight loss" and u["dietary_preference"] == "any"


def test_optional_fields_truly_optional():
    u = normalize_unified(_raw())
    assert u["fitness_level"] is None and u["allergies"] == []
    assert u["workout_days_per_week"] is None


def test_invalid_inputs_rejected():
    assert validate_unified([]) is not None
    assert validate_unified(_raw(age=-3)) is not None
    assert validate_unified(_raw(age=200)) is not None
    assert validate_unified(_raw(height_cm=20)) is not None
    assert validate_unified(_raw(gender="Other")) is not None
    assert validate_unified(_raw(goal="marathon")) is not None
    assert validate_unified(_raw(equipment="barbell")) is not None
    assert validate_unified(_raw(workout_duration_minutes=0)) is not None
    assert validate_unified(_raw(workout_days_per_week=8)) is not None
    assert validate_unified(_raw(allergies="Peanuts")) is not None
    with pytest.raises(ValueError):
        normalize_unified(_raw(age=-3))


def test_goal_and_equipment_maps_cover_catalog_values():
    assert set(DIET_GOAL_MAP) == {"weight loss", "muscle gain", "general fitness"}
    assert set(EQUIPMENT_MAP) == {"bodyweight", "dumbbells", "full gym"}
    assert all(v in ("weight loss", "muscle", "balanced") for v in DIET_GOAL_MAP.values())
    # every mapped equipment value is a real Boostcamp catalog value
    assert {e for v in EQUIPMENT_MAP.values() for e in v} <= {
        "At Home", "Dumbbell Only", "Full Gym", "Garage Gym"}


# --- mapping ---

def test_same_profile_reaches_both_recommenders(tmp_path):
    r = recommender_fixture(tmp_path)
    u = normalize_unified(_raw(fitness_level="beginner", activity_level="active"))
    d, w = to_diet_profile(u), to_workout_profile(u)
    assert (d["Age"], d["Weight_kg"], d["Height_cm"]) == (30, 65, 165)
    assert w["equipment"] == ["Dumbbell Only"] and w["experience_level"] == "Beginner"
    # fixture catalog: Prog A (Full Gym/Beginner), Prog B (At Home/Advanced).
    # general fitness applies no goal filter, so bodyweight+advanced -> Prog B.
    out = recommend_unified(r, _raw(equipment="bodyweight", goal="general fitness",
                                    fitness_level="advanced"))
    assert out["success"] and out["recommendation_type"] == "unified"
    assert out["diet"]["items"] and out["workout"]["primary"]
    assert out["workout"]["primary"]["equipment"] == "At Home"
    assert out["profile"]["bmi"] == pytest.approx(65 / 1.65 ** 2, abs=0.1)


def test_diet_features_match_model_inputs_no_leakage(tmp_path):
    """Every mapped diet field must be a real RF feature; macro/post-outcome cols excluded."""
    r = recommender_fixture(tmp_path)
    feats = set(r._diet_model.named_steps["preprocess"].get_feature_names_out())
    text = " ".join(feats)
    for f in ("Age", "Gender", "Weight_kg", "Height_cm", "Physical_Activity_Level"):
        assert f in text
    d = to_diet_profile(normalize_unified(_raw(activity_level="active")))
    for leaked in ("Protein", "Carbohydrates", "Fat", "Patient_ID", "Disease_Type"):
        assert leaked not in d
    # unknown categories do not crash inference (onehot ignore + imputers)
    cat = r.predict_diet_category({**d, "Preferred_Cuisine": "Martian"})
    assert cat["diet_category"]


def test_workout_equipment_hard_filter(tmp_path):
    r = recommender_fixture(tmp_path)
    out = recommend_unified(r, _raw(equipment="bodyweight"))
    assert out["workout"]["primary"]["equipment"] == "At Home"
    assert to_workout_profile(normalize_unified(_raw(equipment="full gym")))["equipment"] == ["Full Gym"]
    # unknown equipment never silently remaps: recommender reports + excludes
    w = r.recommend_workout({"equipment": ["Barbell"], "top_n": 1})
    assert w["primary"] is None and any("Barbell" in u or "barbell" in u for u in w["unmet"])


def test_injury_handling_conservative(tmp_path):
    assert injury_warning({"injuries_or_limitations": "none"}) is None
    assert injury_warning({"injuries_or_limitations": ""}) is None
    r = recommender_fixture(tmp_path)
    out = recommend_unified(r, _raw(injuries_or_limitations="bad knee"))
    assert any("bad knee" in u and "NOT adjusted or certified safe" in u
               for u in out["workout"]["unmet"])


def test_allergy_fail_closed_and_diet_pref_filter(tmp_path):
    r = recommender_fixture(tmp_path)
    out = recommend_unified(r, _raw(allergies=["Peanuts"]))
    assert out["diet"]["items"] == []  # no allergen data -> exclude all, never 'safe'
    assert out["diet"].get("allergen_warning")
    veg = recommend_unified(r, _raw(dietary_preference="vegetarian"))
    assert veg["diet"]["recipes"]
    assert all(x["diet"] != "non vegetarian" for x in veg["diet"]["recipes"])


def test_empty_candidates_handled(tmp_path):
    r = recommender_fixture(tmp_path)
    out = recommend_unified(r, _raw(allergies=["Peanuts", "Dairy"]))
    assert out["diet"]["items"] == [] and out["diet"]["unmet"]
