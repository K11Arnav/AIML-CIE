"""ML service endpoint tests (real artifacts; no network)."""
from fastapi.testclient import TestClient

import ml_service.app as svc
from tests.conftest import diet_fixture  # noqa: F401 (ensures test env parity)

client = TestClient(svc.app)

WORKOUT_PROFILE = {"goal": "Bodybuilding", "experience_level": "Beginner",
                   "equipment": ["Full Gym"], "available_minutes": 60, "top_n": 2}
DIET_PROFILE = {"Age": 30, "Gender": "Female", "Weight_kg": 65, "Height_cm": 165,
                "Severity": "Moderate", "Physical_Activity_Level": "Active",
                "Daily_Caloric_Intake": 2200, "Cholesterol_mg/dL": 180,
                "Blood_Pressure_mmHg": 120, "Glucose_mg/dL": 95,
                "Weekly_Exercise_Hours": 5, "Adherence_to_Diet_Plan": 85,
                "Dietary_Nutrient_Imbalance_Score": 1.5, "goal": "weight loss",
                "allergies": [], "dietary_restrictions": [], "top_k": 3}


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_workout_endpoint_real_results():
    r = client.post("/recommendations/workout", json=WORKOUT_PROFILE)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["primary"] is not None
    assert "exercise" in body["primary"]["exercises"][0]
    assert 1 + len(body["alternatives"]) <= 2  # top_n caps total plans
    assert "ONE plan" in body["usage"]


def test_diet_endpoint_real_results():
    r = client.post("/recommendations/diet", json=DIET_PROFILE)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["diet_category"]["diet_category"] in ("Balanced", "Low_Carb", "Low_Sodium")
    assert len(body["items"]) == 3
    assert body["allergen_data"] == "unavailable"
    assert "missing_nutrition" in body["items"][0]


def test_diet_allergy_empty_with_warning():
    """Indian catalog has no allergen data: no fallback to branded products."""
    prof = dict(DIET_PROFILE, allergies=["Peanuts"])
    r = client.post("/recommendations/diet", json=prof)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["items"] == []
    assert "allergen_warning" in body
    assert body["catalog_used"]["source_dataset"].startswith("indian_catalog")


def test_invalid_input_400_not_500():
    r = client.post("/recommendations/diet", json={"top_k": 999})
    assert r.status_code == 400
    assert r.json()["success"] is False
    r = client.post("/recommendations/workout", json={"top_n": 0})
    assert r.status_code == 400


def test_non_object_body_400():
    r = client.post("/recommendations/diet", json=[1, 2, 3])
    assert r.status_code == 400


def test_missing_artifacts_503(monkeypatch, tmp_path):
    import ml_service.app as app_mod
    monkeypatch.setattr(app_mod, "_recommender", None)
    monkeypatch.setattr(app_mod, "_load_error", None)
    monkeypatch.setattr(app_mod, "ARTIFACTS_DIR", tmp_path)
    r = client.get("/health")
    assert r.status_code == 503
    assert r.json()["status"] == "unavailable"
    # restore for other tests
    monkeypatch.setattr(app_mod, "ARTIFACTS_DIR",
                        __import__("pathlib").Path("artifacts").resolve())
    app_mod._recommender = None
    app_mod._load_error = None
