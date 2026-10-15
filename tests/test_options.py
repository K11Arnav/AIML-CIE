"""Options source-of-truth tests: endpoint values must match real catalog/model schemas."""
import pandas as pd
from fastapi.testclient import TestClient

import ml_service.app as svc
from ml.options import diet_options, workout_options, WORKOUT_TOP_N_CHOICES

client = TestClient(svc.app)


def test_workout_options_match_catalog():
    cat = pd.read_csv("artifacts/workout_catalog.csv", usecols=["goal", "level", "equipment"])
    opts = workout_options(pd.read_csv("artifacts/workout_catalog.csv"))
    assert "Bodybuilding" in opts["goals"] and "Beginner" in opts["experience_levels"]
    assert set(opts["equipment"]) == set(cat["equipment"].dropna().unique())
    assert opts["defaults"]["goal"] in opts["goals"]
    assert opts["defaults"]["experience_level"] in opts["experience_levels"]
    assert all(e in opts["equipment"] for e in opts["defaults"]["equipment"])
    assert opts["defaults"]["top_n"] in WORKOUT_TOP_N_CHOICES
    assert opts["defaults"]["top_n"] == 1  # default UX: single primary plan
    # preferred-but-unsupported values documented, not silently offered
    assert "Barbell" not in opts["equipment"] and "Dumbbells" not in opts["equipment"]
    assert any("Dumbbell" in n for n in opts["notes"])


def test_diet_options_match_schema():
    from ml.data_preparation import prepare_diet_frame
    from ml.config import ALLERGY_TO_FLAG
    opts = diet_options(prepare_diet_frame())
    assert set(opts["cuisines"]) == {"Chinese", "Indian", "Italian", "Mexican"}
    assert set(opts["dietary_restrictions"]) == {"Low_Sodium", "Low_Sugar"}
    for a in ["Gluten", "Peanuts", "Dairy", "Soy", "Eggs", "Fish"]:
        key = a.lower()
        assert any(sub in key for sub in ALLERGY_TO_FLAG), a
    assert opts["defaults"]["cuisine"] in opts["cuisines"]


def test_options_endpoints_live():
    for kind in ["workout", "diet"]:
        r = client.get(f"/options/{kind}")
        assert r.status_code == 200, kind
        body = r.json()
        assert body["success"] is True
        assert "defaults" in body and "notes" in body


def test_option_values_accepted_by_recommender():
    """Every dropdown default must be accepted (no validation error, JSON-serializable)."""
    import json
    from ml.recommender import FitnessRecommender
    rec = FitnessRecommender.load("artifacts")
    w = client.get("/options/workout").json()
    out = rec.recommend_workout({
        "goal": w["defaults"]["goal"],
        "experience_level": w["defaults"]["experience_level"],
        "equipment": w["defaults"]["equipment"],
        "available_minutes": w["defaults"]["available_minutes"],
        "top_n": w["defaults"]["top_n"],
    })
    json.dumps(out)
    assert out["primary"] is not None
    assert 1 + len(out["alternatives"]) <= w["defaults"]["top_n"]
