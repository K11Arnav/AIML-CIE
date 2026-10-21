"""ML service route tests: options from model artifacts, unified flow."""
from fastapi.testclient import TestClient

import ml_service.app as svc


def _client(recommender):
    svc._recommender = recommender
    svc._load_error = None
    return TestClient(svc.app)


RAW = {"age": 30, "height_cm": 165, "weight_kg": 65, "gender": "Female",
       "goal": "Muscle Gain", "equipment": "home dumbbells",
       "workout_duration_minutes": 45, "fitness_level": "beginner",
       "activity_level": "moderately active", "workout_days_per_week": 4,
       "injuries_or_limitations": "none", "dietary_preference": "any",
       "allergies": []}


def test_health_ok(recommender):
    c = _client(recommender)
    r = c.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_options_content(recommender):
    c = _client(recommender)
    o = c.get("/options/unified").json()
    assert o["success"] is True
    assert "Muscle Gain" in o["goals"]
    assert {eq["value"] for eq in o["equipment"]} == \
        {"bodyweight only", "yoga mat", "home dumbbells", "full home gym", "gym membership"}
    assert set(o["injuries"]) == {"none", "knee", "ankle", "shoulder", "back"}
    assert len(o["activity_levels"]) == 4


def test_unified_success(recommender):
    c = _client(recommender)
    r = c.post("/recommendations/unified", json=RAW)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["workout"]["primary"]["plan"]
    assert body["diet"]["predicted"]["Daily Calorie Target"] > 0


def test_unified_invalid_backend_400(recommender):
    c = _client(recommender)
    r = c.post("/recommendations/unified", json={**RAW, "goal": "bogus goal"})
    assert r.status_code == 400
    assert "goal" in r.json()["error"].lower()


def test_unified_non_object_400(recommender):
    c = _client(recommender)
    r = c.post("/recommendations/unified", json=[1, 2])
    assert r.status_code == 400


def test_load_failure_reported(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path / "nonexistent"))
    import importlib
    importlib.reload(svc)
    c = TestClient(svc.app)
    r = c.get("/health")
    assert r.status_code == 503
    assert "Missing artifacts" in r.json()["reason"]
