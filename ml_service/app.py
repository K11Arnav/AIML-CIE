"""FastAPI ML service: thin HTTP wrapper over ml.recommender (no logic duplication).

Run:  uvicorn ml_service.app:app --port 8000
Env:  ARTIFACTS_DIR (default: <repo>/artifacts)
"""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

ARTIFACTS_DIR = Path(os.environ.get("ARTIFACTS_DIR", Path(__file__).resolve().parent.parent / "artifacts"))

app = FastAPI(title="Fitness ML Service")
_recommender = None
_load_error = None
_options_cache = None


def get_recommender():
    global _recommender, _load_error
    if _recommender is None and _load_error is None:
        try:
            from ml.recommender import FitnessRecommender
            _recommender = FitnessRecommender.load(ARTIFACTS_DIR)
        except Exception as e:  # missing artifacts -> fail clearly, never fake results
            _load_error = f"{type(e).__name__}: {e}"
    return _recommender


@app.get("/health")
def health():
    rec = get_recommender()
    if rec is None:
        return JSONResponse({"status": "unavailable", "reason": _load_error}, status_code=503)
    return {"status": "ok", "version": rec._meta.get("version")}


def _require_model():
    rec = get_recommender()
    if rec is None:
        return None, JSONResponse(
            {"success": False, "error": "ML artifacts unavailable", "detail": _load_error},
            status_code=503)
    return rec, None


@app.get("/options/workout")
def options_workout():
    rec, err = _require_model()
    if err is not None:
        return err
    global _options_cache
    try:
        from ml.options import workout_options
        if _options_cache is None:
            _options_cache = {}
        if "workout" not in _options_cache:
            _options_cache["workout"] = workout_options(rec._meta, rec._workout_model)
        return {"success": True, **_options_cache["workout"]}
    except Exception:
        return JSONResponse({"success": False, "error": "Could not build options"}, status_code=500)


@app.get("/options/diet")
def options_diet():
    rec, err = _require_model()
    if err is not None:
        return err
    global _options_cache
    try:
        from ml.options import diet_options
        if _options_cache is None:
            _options_cache = {}
        if "diet" not in _options_cache:
            _options_cache["diet"] = diet_options(rec._nutrition, rec._meta)
        return {"success": True, **_options_cache["diet"]}
    except Exception:
        return JSONResponse({"success": False, "error": "Could not build options"}, status_code=500)


@app.get("/options/unified")
def options_unified():
    rec, err = _require_model()
    if err is not None:
        return err
    try:
        from ml.options import workout_options, diet_options
        from ml.unified import (GOALS, DIET_GOAL_MAP, GENDERS, FITNESS_LEVELS,
                                ACTIVITY_LEVELS, INJURIES, DIET_PREFERENCES,
                                SAFETY_NOTE)
        global _options_cache
        if _options_cache is None:
            _options_cache = {}
        if "workout" not in _options_cache:
            _options_cache["workout"] = workout_options(rec._meta, rec._workout_model)
        if "diet" not in _options_cache:
            _options_cache["diet"] = diet_options(rec._nutrition, rec._meta)
        d = {"goals": list(GOALS),
             "goal_diet_keys": DIET_GOAL_MAP,
             "genders": list(GENDERS),
             "allergies": _options_cache["diet"]["allergies"],
             "dietary_preferences": list(DIET_PREFERENCES)}
        return {"success": True,
                "goals": list(GOALS),
                "equipment": _options_cache["workout"]["equipment"],
                "fitness_levels": list(FITNESS_LEVELS),
                "activity_levels": list(ACTIVITY_LEVELS),
                "injuries": _options_cache["workout"]["injuries"],
                "dietary_preferences": list(DIET_PREFERENCES),
                "defaults": {
                    "goal": "Muscle Gain",
                    "genders": list(GENDERS),
                    "fitness_level": "beginner",
                    "activity_level": "moderately active",
                    "injuries": "none",
                    "dietary_preference": "any",
                    "available_minutes": _options_cache["workout"]["defaults"]["available_minutes"],
                    "days_per_week": 4,
                },
                "safety_note": SAFETY_NOTE,
                "workout": _options_cache["workout"],
                "diet": d}
    except Exception:
        return JSONResponse({"success": False, "error": "Could not build options"}, status_code=500)


@app.post("/recommendations/unified")
async def unified(request: Request):
    rec, err = _require_model()
    if err is not None:
        return err
    try:
        profile = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Request body must be JSON"}, status_code=400)
    if not isinstance(profile, dict):
        return JSONResponse({"success": False, "error": "Request body must be a JSON object"}, status_code=400)
    try:
        from ml.unified import recommend_unified
        return recommend_unified(rec, profile)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    except Exception:
        return JSONResponse({"success": False, "error": "Recommendation failed"}, status_code=500)


@app.post("/recommendations/workout")
async def workout(request: Request):
    rec, err = _require_model()
    if err is not None:
        return err
    try:
        profile = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Request body must be JSON"}, status_code=400)
    if not isinstance(profile, dict):
        return JSONResponse({"success": False, "error": "Request body must be a JSON object"}, status_code=400)
    try:
        result = rec.recommend_workout(profile)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    except FileNotFoundError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=503)
    except Exception:
        return JSONResponse({"success": False, "error": "Recommendation failed"}, status_code=500)
    return {"success": True, "recommendation_type": "workout", **result}


@app.post("/recommendations/diet")
async def diet(request: Request):
    rec, err = _require_model()
    if err is not None:
        return err
    try:
        profile = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "Request body must be JSON"}, status_code=400)
    if not isinstance(profile, dict):
        return JSONResponse({"success": False, "error": "Request body must be a JSON object"}, status_code=400)
    try:
        result = rec.recommend_diet(profile)
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)
    except Exception:
        return JSONResponse({"success": False, "error": "Recommendation failed"}, status_code=500)
    return {"success": True, "recommendation_type": "diet", **result}
