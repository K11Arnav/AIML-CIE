"""Source of truth for frontend dropdown/multi-select options.

Values are derived from the actual trained model and dataset vocabularies —
never guessed. Submitted values must be valid per these schemas.
"""
import pandas as pd

from .config import GOAL_NUTRITION_TARGETS

TOP_K_CHOICES = [3, 5, 10]
DEFAULT_TOP_K = 5
# Plans: top_n = TOTAL plans returned = 1 primary plan the user follows +
# up to 3 alternatives to choose from INSTEAD (never all of them).
WORKOUT_TOP_N_CHOICES = [1, 2, 3, 4]
DEFAULT_WORKOUT_TOP_N = 1
MAX_WORKOUT_TOP_N = 4
DURATION_CHOICES = [20, 30, 45, 60, 75, 90]
DEFAULT_MINUTES = 45


def workout_options(meta: dict, model_bundle: dict) -> dict:
    """Options straight from the trained classifier / smartfit vocabulary."""
    values = (meta.get("values", {}).get("workout", {}))
    goals = values.get("goals") or sorted(model_bundle.get("goal_values", []))
    return {
        "goals": goals,
        "fitness_levels": ["beginner", "intermediate", "advanced"],
        "injuries": ["none", "knee", "ankle", "shoulder", "back"],
        "equipment": [
            {"value": "bodyweight only", "label": "Bodyweight / no equipment"},
            {"value": "yoga mat", "label": "Yoga mat (mobility, floor work)"},
            {"value": "home dumbbells", "label": "Home dumbbells / kettlebell"},
            {"value": "full home gym", "label": "Full home gym (barbell + rack)"},
            {"value": "gym membership", "label": "Gym membership (machines, cables, barbell)"},
        ],
        "available_minutes": DURATION_CHOICES,
        "days_per_week": list(range(1, 8)),
        "top_n_choices": WORKOUT_TOP_N_CHOICES,
        "top_n_meaning": ("Total plans returned = 1 primary plan to follow "
                          "+ up to 3 alternatives to choose from instead."),
        "defaults": {
            "goal": "Muscle Gain" if "Muscle Gain" in goals else (goals[0] if goals else None),
            "fitness_level": "beginner",
            "injuries": "none",
            "equipment": "home dumbbells",
            "available_minutes": DEFAULT_MINUTES,
            "top_n": DEFAULT_WORKOUT_TOP_N,
        },
        "notes": [
            "Goals/equipment/levels are exact values the workout model was trained on.",
            "Plan predictions are equipment-constrained: the model cannot return "
            "a plan your selected equipment cannot do.",
            "Session minutes are a documented heuristic; no per-plan durations "
            "exist in the training data.",
            "Follow ONE plan (primary or one alternative instead) — not all of them.",
        ],
    }


def diet_options(nutrition_df: pd.DataFrame, meta: dict) -> dict:
    return {
        "goals": sorted(GOAL_NUTRITION_TARGETS),
        "dietary_preferences": sorted(
            nutrition_df["Dietary Preference"].dropna().unique().tolist()) or ["Omnivore"],
        "activity_levels": ["sedentary", "lightly active", "moderately active", "very active"],
        "allergies": ["Gluten", "Peanuts", "Dairy", "Soy", "Eggs", "Fish"],
        "top_k_choices": TOP_K_CHOICES,
        "defaults": {"goal": "balanced", "top_k": DEFAULT_TOP_K,
                     "dietary_preference": "Omnivore"},
        "notes": [
            "The Anuvaad food catalog has NO allergen flags: selecting any "
            "allergy excludes all foods (fail-closed) with a warning. Meal "
            "suggestions are retrieved suggestions — never allergy-screened.",
            "Macro/calorie predictions come from the nutrition_dataset RF "
            "regressor; predicted target ≠ medical advice.",
        ],
    }
