"""Source of truth for frontend dropdown/multi-select options.

Values are derived from the actual catalogs and model schemas — never guessed.
Submitted values must be valid per these schemas; labels may be human-friendly.
"""
import ast

import pandas as pd

from .config import ALLERGY_TO_FLAG, GOAL_ALIASES, GOAL_NUTRITION_TARGETS

TOP_N_CHOICES = [3, 5, 10]
DEFAULT_TOP_N = 3
# Workout plans: top_n = TOTAL alternative programs returned = 1 primary plan
# the user follows + up to 3 alternatives to choose from instead. Default UX
# shows the single primary plan.
WORKOUT_TOP_N_CHOICES = [1, 2, 3, 4]
DEFAULT_WORKOUT_TOP_N = 1
MAX_WORKOUT_TOP_N = 4
# Duration choices are thresholds (programs with time <= value + 15 qualify);
# values picked from real catalog durations.
DURATION_CHOICES = [20, 30, 45, 60, 90]
DEFAULT_MINUTES = 60


def _list_tokens(series: pd.Series) -> list:
    out = []
    for cell in series.dropna().unique():
        t = str(cell).strip()
        if t.startswith("["):
            try:
                v = ast.literal_eval(t)
                out.extend(str(x).strip() for x in v)
                continue
            except Exception:
                pass
        out.append(t)
    return sorted(set(out))


def workout_options(workout_df: pd.DataFrame) -> dict:
    goals = _list_tokens(workout_df["goal"])
    levels = _list_tokens(workout_df["level"])
    equipment = sorted(workout_df["equipment"].dropna().unique().tolist())
    return {
        "goals": goals,
        "experience_levels": levels,
        "equipment": equipment,
        "available_minutes": DURATION_CHOICES,
        "top_n_choices": WORKOUT_TOP_N_CHOICES,
        "top_n_meaning": ("Total alternative programs returned = 1 primary plan "
                          "to follow + up to 3 alternatives to choose from instead."),
        "defaults": {
            "goal": "Bodybuilding" if "Bodybuilding" in goals else goals[0],
            "experience_level": "Beginner" if "Beginner" in levels else levels[0],
            # Preferred "Dumbbells"/"Barbell" are NOT catalog values (only
            # Full Gym / Garage Gym / At Home / Dumbbell Only exist) — see notes.
            "equipment": ["Dumbbell Only"] if "Dumbbell Only" in equipment else equipment[:1],
            "available_minutes": DEFAULT_MINUTES,
            "top_n": DEFAULT_WORKOUT_TOP_N,
        },
        "notes": [
            "Equipment 'Dumbbells'/'Barbell' do not exist in the workout catalog; "
            "closest valid default is 'Dumbbell Only'. Equipment is an exact-match "
            "hard filter: incompatible programs are excluded and reported, never "
            "silently remapped.",
            "Goal/level use substring matching; unknown values are reported, not applied.",
            "Follow ONE plan (the primary, or one alternative instead) — not all of them.",
        ],
    }


def diet_options(diet_df: pd.DataFrame) -> dict:
    cuisines = sorted(diet_df["Preferred_Cuisine"].dropna().unique().tolist())
    try:
        from .recipes import prepare_recipe_catalog
        _r, _rs = prepare_recipe_catalog()
        recipe_courses = sorted(_r["course"].dropna().unique().tolist())
        recipe_diets = sorted(_r["diet"].dropna().unique().tolist())
    except Exception:
        recipe_courses, recipe_diets = [], []
    return {
        "goals": sorted(GOAL_NUTRITION_TARGETS),
        "goal_aliases": dict(GOAL_ALIASES),
        "cuisines": cuisines,
        "allergies": ["Gluten", "Peanuts", "Dairy", "Soy", "Eggs", "Fish"],
        "dietary_restrictions": ["Low_Sodium", "Low_Sugar"],
        "severity": sorted(diet_df["Severity"].dropna().unique().tolist()),
        "activity_levels": sorted(diet_df["Physical_Activity_Level"].dropna().unique().tolist()),
        "top_k_choices": [3, 5, 10],
        "recipe_courses": recipe_courses,
        "recipe_diets": recipe_diets,
        "recipe_course_default": "main course",
        "defaults": {"goal": "balanced", "cuisine": "Indian" if "Indian" in cuisines else cuisines[0], "top_k": 5},
        "notes": [
            "Only Low_Sodium/Low_Sugar restrictions have enforced thresholds; "
            "other values are reported as unsupported, not applied.",
            "The food catalog contains NO allergen data: selecting any allergy "
            "excludes all candidates with a warning. Allergen safety can never "
            "be established from this catalog.",
        ],
    }


def allergy_flag_for(label: str) -> str | None:
    key = str(label).strip().lower()
    return next((f for sub, f in ALLERGY_TO_FLAG.items() if sub in key), None)
