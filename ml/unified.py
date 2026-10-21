"""Canonical unified profile: one form, one submit, both models.

The UI collects a single profile; this module validates/normalizes it and maps
it to the recommender inputs. No ML logic here.

Every field the frontend sends is consumed below (no dead fields):
  age, height_cm, weight_kg, gender  -> BOTH models (workout RF + diet RF)
  goal                               -> workout RF feature + diet KNN key
  equipment                          -> workout RF feature + layout constraint
  fitness_level                      -> workout RF experience_level feature
  workout_duration_minutes           -> workout duration check (heuristic)
  workout_days_per_week              -> workout weekly split (default 4)
  injuries_or_limitations            -> workout RF Injury feature + safety note
  activity_level                     -> diet RF feature (+ formula context)
  dietary_preference                 -> diet RF feature + meal retrieval
  allergies                          -> food ranking fail-closed exclusion

Values below are the EXACT training values from the current datasets
(smartfit goals/equipment/levels; nutrition activity levels/preferences).
"""
from .calories import estimate_daily_calories

VERSION = "2.0"

GOALS = ("Weight Loss", "Muscle Gain", "General Health", "Strength",
         "Endurance", "Tone Up", "Powerlifting", "Flexibility",
         "CrossFit", "Athletic Performance", "Marathon Training")
DIET_GOAL_MAP = {  # workout goal -> diet KNN reference key
    "Weight Loss": "weight loss", "Tone Up": "weight loss",
    "Endurance": "weight loss", "Marathon Training": "weight loss",
    "Muscle Gain": "muscle", "Strength": "muscle", "Powerlifting": "muscle",
    "CrossFit": "muscle",
    "General Health": "balanced", "Athletic Performance": "balanced",
    "Flexibility": "balanced",
}
DIET_FITNESS_GOAL_LABELS = {  # diet RF `Fitness Goal` feature vocabulary (nutrition_dataset value Families)
    "Weight Loss": "Weight Loss", "Muscle Gain": "Muscle Gain",
    "Maintenance": "Maintenance", "General Health": "Maintenance",
    "Strength": "Maintenance", "Powerlifting": "Muscle Gain",
    "CrossFit": "Weight Loss", "Athletic Performance": "Maintenance",
    "Endurance": "Weight Loss", "Marathon Training": "Weight Loss",
    "Tone Up": "Weight Loss", "Flexibility": "Maintenance",
}

EQUIPMENT_MAP = {  # form key -> smartfit Equipment value
    "bodyweight only": "Bodyweight Only",
    "yoga mat": "Yoga Mat",
    "home dumbbells": "Home Dumbbells",
    "full home gym": "Full Home Gym",
    "gym membership": "Gym Membership",
}
EQUIPMENT_LABELS = {k: v for k, v in {
    "bodyweight only": "Bodyweight / no equipment",
    "yoga mat": "Yoga mat (mobility, floor work)",
    "home dumbbells": "Home dumbbells / kettlebell",
    "full home gym": "Full home gym (barbell + rack)",
    "gym membership": "Gym membership (machines, cables, barbell)",
}.items()}

GENDERS = ("female", "male")
FITNESS_LEVELS = ("beginner", "intermediate", "advanced")
LEVEL_MAP = {"beginner": "Beginner", "intermediate": "Intermediate",
             "advanced": "Advanced"}
ACTIVITY_LEVELS = ("sedentary", "lightly active", "moderately active", "very active")
ACTIVITY_MAP = {  # form value -> nutrition_dataset `Activity Level` value
    "sedentary": "Sedentary", "lightly active": "Lightly Active",
    "moderately active": "Moderately Active", "very active": "Very Active",
}
FORM_ACTIVITY_FACTORS = {  # Mifflin-St Jeor factor per form value (ml/calories.py)
    "sedentary": 1.2, "lightly active": 1.375,
    "moderately active": 1.55, "very active": 1.725,
}
INJURIES = ("none", "knee", "ankle", "shoulder", "back")
INJURY_MAP = {"none": "None", "knee": "Knee", "ankle": "Ankle",
              "shoulder": "Shoulder", "back": "Back"}
DIET_PREFERENCES = ("any", "omnivore", "vegetarian", "vegan")
PREFERENCE_MAP = {"omnivore": "Omnivore", "vegetarian": "Vegetarian",
                  "vegan": "Vegan"}

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
    if _norm(p.get("goal")) not in {g.lower() for g in GOALS}:
        return f"goal must be one of: {', '.join(GOALS)}"
    if _norm(p.get("equipment")) not in EQUIPMENT_MAP:
        return f"equipment must be one of: {', '.join(EQUIPMENT_LABELS)}"
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
    if _norm(p.get("injuries_or_limitations"), "none") not in INJURIES:
        return f"injuries_or_limitations must be one of: none, knee, ankle, shoulder, back"
    if p.get("dietary_preference") is not None and _norm(p.get("dietary_preference")) not in DIET_PREFERENCES:
        return f"dietary_preference must be one of: {', '.join(DIET_PREFERENCES)}"
    if p.get("allergies") is not None and not isinstance(p.get("allergies"), list):
        return "allergies must be an array"
    return None


def normalize_unified(p: dict) -> dict:
    """Validate + normalize + map to model vocabularies. Raises ValueError."""
    err = validate_unified(p)
    if err:
        raise ValueError(err)
    goal = str(p["goal"]).strip().lower()
    goal_label = next(g for g in GOALS if g.lower() == goal)
    return {
        "age": float(p["age"]),
        "height_cm": float(p["height_cm"]),
        "weight_kg": float(p["weight_kg"]),
        "gender": _norm(p.get("gender")).capitalize(),  # Female/Male (both models)
        "goal": goal_label,                              # smartfit value
        "equipment": EQUIPMENT_MAP[_norm(p.get("equipment"))],   # smartfit value
        "workout_duration_minutes": float(p["workout_duration_minutes"]),
        "fitness_level": _norm(p.get("fitness_level")) or None,
        "activity_level": _norm(p.get("activity_level")) or None,
        "workout_days_per_week": p.get("workout_days_per_week"),
        "injuries_or_limitations": INJURY_MAP[_norm(p.get("injuries_or_limitations"), "none")],
        "dietary_preference": _norm(p.get("dietary_preference")) or "any",
        "allergies": [str(a) for a in (p.get("allergies") or []) if str(a).strip()],
    }


def to_workout_profile(u: dict) -> dict:
    """Map the normalized profile onto the workout RF + layout inputs."""
    prof = {
        "age": u["age"], "gender": u["gender"],
        "weight_kg": u["weight_kg"], "height_cm": u["height_cm"],
        "goal": u["goal"],                    # exact smartfit value
        "equipment": u["equipment"],          # exact smartfit value
        "available_minutes": u["workout_duration_minutes"],
        "top_n": 1,
    }
    if u["fitness_level"]:
        prof["experience_level"] = LEVEL_MAP[u["fitness_level"]]
    prof["injury"] = u["injuries_or_limitations"]      # None/Knee/Ankle/Shoulder/Back
    if u["workout_days_per_week"]:
        prof["workout_days_per_week"] = u["workout_days_per_week"]
    return prof


def to_diet_profile(u: dict) -> dict:
    """Map the normalized profile onto the diet RF + KNN + meals inputs."""
    pref = u["dietary_preference"]
    diet_pref = PREFERENCE_MAP.get(pref, "Omnivore")  # 'any' -> majority class
    pref_any = pref == "any"
    act = ACTIVITY_MAP[u["activity_level"]] if u["activity_level"] else "Moderately Active"
    act_assumed = u["activity_level"] is None
    return {
        "age": u["age"], "gender": u["gender"],
        "height_cm": u["height_cm"], "weight_kg": u["weight_kg"],
        "activity_level": act,
        "activity_level_assumed": act_assumed,
        "fitness_goal": DIET_FITNESS_GOAL_LABELS[u["goal"]],  # diet RF feature value
        "dietary_preference": diet_pref,
        "dietary_preference_any": pref_any,      # meals: 'any' shows all preferences
        "goal": DIET_GOAL_MAP[u["goal"]],        # KNN reference key
        "allergies": list(u["allergies"]),
        "top_k": 5,
    }


def injury_warning(u: dict) -> str | None:
    """Any reported limitation always yields a warning — never a safety claim."""
    if u["injuries_or_limitations"] == "None":
        return None
    return (f"You reported a {u['injuries_or_limitations'].lower()} injury. The model "
            "was trained on this single injury dimension and the exercise "
            "library has no injury-safety data, so this plan is NOT certified "
            "safe for it — train conservatively and consult a professional.")


def recommend_unified(rec, raw: dict) -> dict:
    """Run both models on the same normalized profile (single submit)."""
    u = normalize_unified(raw)
    workout = rec.recommend_workout(to_workout_profile(u))
    diet = rec.recommend_diet(to_diet_profile(u))
    warn = injury_warning(u)
    if warn:
        workout = {**workout,
                   "unmet": [*workout.get("unmet", []), warn]}
    return {
        "success": True,
        "recommendation_type": "unified",
        "profile": {k: (round(v, 1) if isinstance(v, float) and v == int(v) else v)
                    for k, v in {**u, "bmi": round(u["weight_kg"] / (u["height_cm"] / 100) ** 2, 1)}.items()},
        "safety_note": SAFETY_NOTE,
        "diet_goal": DIET_GOAL_MAP[u["goal"]],
        "daily_calorie_target_formula": estimate_daily_calories(
            u["age"], u["height_cm"], u["weight_kg"], u["gender"], u["activity_level"]),
        "diet": diet,
        "workout": workout,
        "version": VERSION,
    }
