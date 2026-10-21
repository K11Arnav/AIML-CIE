"""Canonical unified profile: one form, one submit, both recommenders.

The UI collects a single profile; this module validates/normalizes it and maps
it to the existing diet and workout recommender inputs. No ML logic here, no
retraining, no new dependencies.

Canonical fields (explicit units in names):
  required: age (years), height_cm, weight_kg, gender, goal, equipment,
            workout_duration_minutes
  optional: fitness_level, activity_level, workout_days_per_week,
            injuries_or_limitations, dietary_preference, allergies

Downstream use of every field (fields with no consumer are omitted by design):
  age/height_cm/weight_kg/gender -> diet RF features (BMI derived); workout unused
  goal -> diet KNN target + workout goal filter (via documented maps)
  equipment -> workout hard filter (exact catalog match, never remapped)
  workout_duration_minutes -> workout duration filter
  fitness_level -> workout experience_level filter
  activity_level -> diet Physical_Activity_Level feature
  workout_days_per_week -> echoed schedule context only (no scheduling claims)
  injuries_or_limitations -> conservative safety warning (never claimed safe)
  dietary_preference -> recipe diet filter
  allergies -> hard food/recipe exclusion (fail-closed)
"""
from .calories import estimate_daily_calories

VERSION = "1.0"

# Unified goals presented by the form. Each maps to a diet KNN key and a
# workout catalog substring (None = no goal filter, rank all programs).
GOALS = ("weight loss", "muscle gain", "general fitness")
DIET_GOAL_MAP = {"weight loss": "weight loss", "muscle gain": "muscle", "general fitness": "balanced"}
WORKOUT_GOAL_MAP = {
    "weight loss": "Bodyweight Fitness",  # closest catalog goal; substring-matched
    "muscle gain": "Bodybuilding",        # closest catalog goal; substring-matched
    "general fitness": None,              # no filter: rank all programs
}

# Unified equipment labels shown in the form -> exact workout catalog values.
# Single-select on the form; values ARE catalog values so the hard filter stays exact.
EQUIPMENT_MAP = {
    "bodyweight": ["At Home"],
    "dumbbells": ["Dumbbell Only"],
    "full gym": ["Full Gym"],
}
EQUIPMENT_LABELS = {
    "bodyweight": "Bodyweight / no equipment (At Home)",
    "dumbbells": "Dumbbells / basic equipment (Dumbbell Only)",
    "full gym": "Full gym (Full Gym)",
}

GENDERS = ("female", "male")
FITNESS_LEVELS = ("beginner", "intermediate", "advanced")
LEVEL_MAP = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced"}
ACTIVITY_LEVELS = ("sedentary", "moderate", "active")
ACTIVITY_MAP = {"sedentary": "Sedentary", "moderate": "Moderate", "active": "Active"}
DIET_PREFERENCES = ("any", "vegetarian", "non vegetarian")

SAFETY_NOTE = ("Informational only — not medical advice. Stop and consult a "
               "professional if anything hurts.")


def _norm(s, default=""):
    return str(s).strip().lower() if s is not None and str(s).strip() else default


def validate_unified(p: dict) -> str | None:
    """Return an error string, or None when the profile is valid."""
    if not isinstance(p, dict) or isinstance(p, list):
        return "Request body must be a JSON object"
    for f in ("age", "height_cm", "weight_kg"):
        v = p.get(f)
        if v is None or not isinstance(v, (int, float)) or not (v > 0):
            return f"{f} must be a positive number"
    if not 5 <= float(p["age"]) <= 100:
        return "age must be between 5 and 100"
    if not 50 <= float(p["height_cm"]) <= 250:
        return "height_cm must be between 50 and 250"
    if not 20 <= float(p["weight_kg"]) <= 300:
        return "weight_kg must be between 20 and 300"
    if _norm(p.get("gender")) not in GENDERS:
        return "gender must be one of: Female, Male"
    if _norm(p.get("goal")) not in GOALS:
        return f"goal must be one of: {', '.join(GOALS)}"
    if _norm(p.get("equipment")) not in EQUIPMENT_MAP:
        return f"equipment must be one of: {', '.join(EQUIPMENT_MAP)}"
    dur = p.get("workout_duration_minutes")
    if dur is None or not isinstance(dur, (int, float)) or not (dur > 0):
        return "workout_duration_minutes must be a positive number"
    if p.get("fitness_level") is not None and _norm(p.get("fitness_level")) not in FITNESS_LEVELS:
        return f"fitness_level must be one of: {', '.join(FITNESS_LEVELS)}"
    if p.get("activity_level") is not None and _norm(p.get("activity_level")) not in ACTIVITY_LEVELS:
        return f"activity_level must be one of: {', '.join(ACTIVITY_LEVELS)}"
    if p.get("workout_days_per_week") is not None:
        d = p["workout_days_per_week"]
        if not isinstance(d, int) or isinstance(d, bool) or not 1 <= d <= 7:
            return "workout_days_per_week must be an integer between 1 and 7"
    if p.get("dietary_preference") is not None and _norm(p.get("dietary_preference")) not in DIET_PREFERENCES:
        return f"dietary_preference must be one of: {', '.join(DIET_PREFERENCES)}"
    for f in ("allergies",):
        if p.get(f) is not None and not isinstance(p.get(f), list):
            return f"{f} must be an array"
    if p.get("injuries_or_limitations") is not None and not isinstance(p.get("injuries_or_limitations"), str):
        return "injuries_or_limitations must be a string"
    return None


def normalize_unified(p: dict) -> dict:
    """Validate + normalize. Raises ValueError on invalid input."""
    err = validate_unified(p)
    if err:
        raise ValueError(err)
    out = {
        "age": float(p["age"]),
        "height_cm": float(p["height_cm"]),
        "weight_kg": float(p["weight_kg"]),
        "gender": _norm(p.get("gender")).capitalize(),  # Female/Male (RF schema)
        "goal": _norm(p.get("goal")),
        "equipment": _norm(p.get("equipment")),
        "workout_duration_minutes": float(p["workout_duration_minutes"]),
        "fitness_level": _norm(p.get("fitness_level")) or None,
        "activity_level": _norm(p.get("activity_level")) or None,
        "workout_days_per_week": p.get("workout_days_per_week"),
        "injuries_or_limitations": (p.get("injuries_or_limitations") or "").strip() or None,
        "dietary_preference": _norm(p.get("dietary_preference")) or "any",
        "allergies": [str(a) for a in (p.get("allergies") or []) if str(a).strip()],
    }
    return out


def to_diet_profile(u: dict) -> dict:
    """Map a normalized unified profile to the diet recommender input.

    Only fields the diet pipeline consumes are set; the RF imputes the rest
    (clinical fields the form intentionally does not collect).
    """
    goal_key = DIET_GOAL_MAP[u["goal"]]
    assert goal_key in ("weight loss", "muscle", "balanced"), goal_key
    profile = {
        "Age": u["age"],
        "Gender": u["gender"],
        "Weight_kg": u["weight_kg"],
        "Height_cm": u["height_cm"],
        "Preferred_Cuisine": "Indian",
        "goal": goal_key,
        "allergies": list(u["allergies"]),
        "dietary_restrictions": [],
        "diet_preference": u["dietary_preference"],
        "course": "main course",
        "top_k": 5,
    }
    if u["activity_level"]:
        profile["Physical_Activity_Level"] = ACTIVITY_MAP[u["activity_level"]]
    return profile


def to_workout_profile(u: dict) -> dict:
    """Map a normalized unified profile to the workout recommender input."""
    profile = {
        "equipment": list(EQUIPMENT_MAP[u["equipment"]]),
        "available_minutes": u["workout_duration_minutes"],
        "top_n": 1,
    }
    goal_sub = WORKOUT_GOAL_MAP[u["goal"]]
    if goal_sub:
        profile["goal"] = goal_sub
    if u["fitness_level"]:
        profile["experience_level"] = LEVEL_MAP[u["fitness_level"]]
    return profile


def injury_warning(u: dict) -> str | None:
    """Conservative injury handling: the catalog has no injury/muscle-safety
    data, so any limitation beyond 'none' yields a warning, never a safety claim."""
    raw = (u.get("injuries_or_limitations") or "").strip()
    if not raw or raw.lower() in ("none", "no", "n/a", "na"):
        return None
    return ("You reported a limitation/injury ('%s'). The exercise catalog has no "
            "injury-safety data, so this plan is NOT adjusted or certified safe for "
            "it — train conservatively and consult a professional." % raw)


def recommend_unified(rec, raw: dict) -> dict:
    """Run both recommenders on the same normalized profile (single submit)."""
    u = normalize_unified(raw)
    diet = rec.recommend_diet(to_diet_profile(u))
    workout = rec.recommend_workout(to_workout_profile(u))
    warn = injury_warning(u)
    if warn:
        workout = {**workout, "unmet": [*workout.get("unmet", []), warn]}
    return {
        "success": True,
        "recommendation_type": "unified",
        "profile": {**u, "bmi": round(u["weight_kg"] / (u["height_cm"] / 100) ** 2, 1)},
        "safety_note": SAFETY_NOTE,
        "diet_goal": DIET_GOAL_MAP[u["goal"]],
        "workout_goal_filter": WORKOUT_GOAL_MAP[u["goal"]],
        "daily_calorie_target": estimate_daily_calories(
            u["age"], u["height_cm"], u["weight_kg"], u["gender"], u["activity_level"]),
        "diet": diet,
        "workout": workout,
        "version": VERSION,
    }
