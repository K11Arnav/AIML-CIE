"""Central configuration: paths, seeds, feature lists. No personal machine paths."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = PROJECT_ROOT / "reports"

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Raw dataset filenames (discovered locally)
DIET_FILE = DATASETS_DIR / "diet_recommendations_dataset.csv"
# Active food catalog: Indian-food derived catalog built from healthy_foods
# (see ml/indian_catalog.py). NOTE: it has NO allergen/dietary-flag columns, so
# allergy compatibility can never be established (see recommender safety rule).
# The OFF allergen-annotated catalog is EXCLUDED: it has no usable Indian-food
# selection (only branded basmati/lentil-chip products), so it cannot serve an
# Indian-food experience even as an allergy fallback.
FOOD_PRIMARY_FILE = DATASETS_DIR / "healthy_foods_database.csv"
WORKOUT_DETAILED_FILE = DATASETS_DIR / "programs_detailed_boostcamp_kaggle.csv"

# Diet classifier
DIET_TARGET = "Diet_Recommendation"
DIET_ID_COLS = ["Patient_ID"]
# Disease_Type perfectly predicts the target (Diabetes->Low_Carb,
# Hypertension->Low_Sodium, else Balanced) -> excluded as target proxy/leakage.
DIET_LEAKAGE_COLS = ["Disease_Type"]
DIET_NUMERIC = [
    "Age", "Weight_kg", "Height_cm", "BMI", "Daily_Caloric_Intake",
    "Cholesterol_mg/dL", "Blood_Pressure_mmHg", "Glucose_mg/dL",
    "Weekly_Exercise_Hours", "Adherence_to_Diet_Plan",
    "Dietary_Nutrient_Imbalance_Score",
]
DIET_CATEGORICAL = [
    "Gender", "Severity", "Physical_Activity_Level",
    "Dietary_Restrictions", "Allergies", "Preferred_Cuisine",
]

# KNN food ranking: per-100g nutrition columns with consistent units.
KNN_NUTRITION_COLS = [
    "energy_kcal", "fat_100g", "carbs_100g", "sugars_100g",
    "fiber_100g", "proteins_100g", "sodium_100g",
]
ALLERGEN_FLAG_COLS = [
    "contains_gluten", "contains_dairy", "contains_nuts",
    "contains_soy", "contains_eggs", "contains_fish",
]

# Allergy label -> flag mapping (case-insensitive substring match on user input)
ALLERGY_TO_FLAG = {
    "gluten": "contains_gluten",
    "wheat": "contains_gluten",
    "dairy": "contains_dairy",
    "milk": "contains_dairy",
    "lactose": "contains_dairy",
    "peanut": "contains_nuts",
    "nut": "contains_nuts",
    "soy": "contains_soy",
    "egg": "contains_eggs",
    "fish": "contains_fish",
}

# Explicit goal -> target per-100g nutrition profile used as KNN query vector.
# Values are modest per-100g reference points, documented and testable.
GOAL_NUTRITION_TARGETS = {
    "weight loss": {"energy_kcal": 80.0, "fat_100g": 2.0, "carbs_100g": 10.0,
                    "sugars_100g": 3.0, "fiber_100g": 5.0, "proteins_100g": 12.0,
                    "sodium_100g": 0.2},
    "muscle": {"energy_kcal": 250.0, "fat_100g": 8.0, "carbs_100g": 25.0,
               "sugars_100g": 5.0, "fiber_100g": 4.0, "proteins_100g": 25.0,
               "sodium_100g": 0.4},
    "balanced": {"energy_kcal": 150.0, "fat_100g": 5.0, "carbs_100g": 18.0,
                 "sugars_100g": 6.0, "fiber_100g": 3.5, "proteins_100g": 10.0,
                 "sodium_100g": 0.3},
}
# Normalize user goal strings to the above keys
GOAL_ALIASES = {
    "weight loss": "weight loss", "fat loss": "weight loss", "lose weight": "weight loss",
    "muscle": "muscle", "muscle gain": "muscle", "bodybuilding": "muscle",
    "muscle & sculpting": "muscle", "strength": "muscle",
    "balanced": "balanced", "maintenance": "balanced", "general": "balanced",
}
