"""Central configuration: paths, seeds, feature lists. No personal machine paths.

SOURCE OF TRUTH for all training data: the five files currently present in
datasets/. No other dataset exists in this repo; nothing outside datasets/ is
read for training. programs_detailed_boostcamp_kaggle.csv,
diet_recommendations_dataset.csv, healthy_foods_database.csv and
indian_food.csv are GONE — any pipeline referencing them is retired.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = PROJECT_ROOT / "reports"

RANDOM_STATE = 42
TEST_SIZE = 0.2

# --- the five active dataset files (verified present in datasets/) ---
WORKOUT_DATA_FILE = DATASETS_DIR / "smartfit_workout_dataset.csv"   # profile -> plan
NUTRITION_DATA_FILE = DATASETS_DIR / "nutrition_dataset.csv"        # profile -> macros + meals
FOOD_DB_FILE = DATASETS_DIR / "Anuvaad_INDB_2024.11.xlsx"           # Indian food composition
EXERCISES_FILE = DATASETS_DIR / "exercises.json"                    # exercise library

# --- workout classifier (smartfit) ---
WORKOUT_TARGET = "Recommended_Plan"
WORKOUT_FEATURE_CATEGORICAL = ["Gender", "Goal", "Equipment", "Experience", "Injury"]
WORKOUT_FEATURE_NUMERIC = ["Age", "Weight_kg", "Height_cm"]
WORKOUT_FEATURES = WORKOUT_FEATURE_NUMERIC + WORKOUT_FEATURE_CATEGORICAL
WORKOUT_INJURY_VALUES = ["None", "Knee", "Ankle", "Shoulder", "Back"]

# --- diet macro regressor (nutrition_dataset) ---
DIET_TARGETS = ["Daily Calorie Target", "Protein", "Carbohydrates", "Fat"]
DIET_FEATURE_CATEGORICAL = ["Gender", "Activity Level", "Fitness Goal",
                            "Dietary Preference"]
DIET_FEATURE_NUMERIC = ["Age", "Height", "Weight"]
DIET_FEATURES = DIET_FEATURE_NUMERIC + DIET_FEATURE_CATEGORICAL

# --- KNN food ranking: Anuvaad per-100g nutrition columns with consistent units.
# sodium_mg is converted to g (÷1000) during preparation and recorded in meta.
KNN_NUTRITION_COLS = [
    "energy_kcal", "fat_100g", "carbs_100g", "sugars_100g",
    "fiber_100g", "proteins_100g", "sodium_100g",
]

# Allergen flags are DERIVED from food names by keyword rules in
# ml/allergens.py (the Anuvaad INDB ships nutrients only). Flags are positive
# matches only; "not flagged" is never claimed to be certified allergen-free.
ALLERGEN_FLAG_COLS = [
    "contains_gluten", "contains_dairy", "contains_nuts", "contains_peanuts",
    "contains_soy", "contains_eggs", "contains_fish",
]
ALLERGY_TO_FLAG = {
    "gluten": "contains_gluten", "wheat": "contains_gluten", "celiac": "contains_gluten",
    "dairy": "contains_dairy", "milk": "contains_dairy", "lactose": "contains_dairy",
    "peanut": "contains_peanuts", "peanuts": "contains_peanuts",
    "groundnut": "contains_peanuts", "arachide": "contains_peanuts",
    "nut": "contains_nuts", "nuts": "contains_nuts", "tree nut": "contains_nuts",
    "almond": "contains_nuts", "cashew": "contains_nuts", "hazelnut": "contains_nuts",
    "walnut": "contains_nuts", "pistachio": "contains_nuts",
    "soy": "contains_soy", "soya": "contains_soy", "soybean": "contains_soy",
    "egg": "contains_eggs", "eggs": "contains_eggs",
    "fish": "contains_fish", "seafood": "contains_fish",
    "shellfish": "contains_fish", "shell fish": "contains_fish",
    "prawn": "contains_fish", "shrimp": "contains_fish", "crab": "contains_fish",
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
# workout goal (smartfit value) -> KNN diet goal key
GOAL_TO_DIET_KEY = {
    "Weight Loss": "weight loss", "Tone Up": "weight loss", "Endurance": "weight loss",
    "Marathon Training": "weight loss",
    "Muscle Gain": "muscle", "Strength": "muscle", "Powerlifting": "muscle",
    "CrossFit": "muscle",
    "General Health": "balanced", "Athletic Performance": "balanced",
    "Flexibility": "balanced",
}
GOAL_ALIASES = {
    "weight loss": "weight loss", "fat loss": "weight loss", "lose weight": "weight loss",
    "muscle": "muscle", "muscle gain": "muscle", "bodybuilding": "muscle",
    "strength": "muscle", "powerlifting": "muscle", "crossfit": "muscle",
    "balanced": "balanced", "maintenance": "balanced", "general": "balanced",
    "general health": "balanced", "athletic performance": "balanced",
    "endurance": "weight loss", "marathon training": "weight loss",
    "tone up": "weight loss", "flexibility": "balanced",
}
