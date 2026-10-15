"""Shared synthetic fixtures (no raw data, no network)."""
import numpy as np
import pandas as pd


def food_fixture(n=30, seed=0):
    """Healthy-catalog schema with Indian-evidence names (dishes + staples)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    names = ["Test dal bukhara", "Test chapati", "Test besan mix", "Test papad",
             "Lentils, test red", "Rice, brown test", "Spinach, test", "Peanuts, test raw"]
    names = [f"{names[i % 8]} {i}" for i in range(n)]
    df = pd.DataFrame({
        "food_name": names,
        "food_type": (["Grains", "Vegetables", "Dairy"] * (n // 3 + 1))[:n],
        "calories": rng.uniform(20, 500, n),
        "protein_g": rng.uniform(0, 40, n),
        "fat_g": rng.uniform(0, 30, n),
        "carbs_g": rng.uniform(0, 60, n),
        "fiber_g": rng.uniform(0, 10, n),
        "sugar_g": rng.uniform(0, 30, n),
        "sodium_mg": rng.uniform(0, 2000, n),
        "health_score": rng.integers(60, 76, n),
    })
    df.loc[3, "sugar_g"] = np.nan
    df.loc[7, "fiber_g"] = np.nan
    return df


def workout_fixture():
    return pd.DataFrame({
        "title": ["Prog A", "Prog A", "Prog B"],
        "level": ["['Beginner']", "['Beginner']", "['Advanced']"],
        "goal": ["['Bodybuilding']", "['Bodybuilding']", "['Athletics']"],
        "equipment": ["Full Gym", "Full Gym", "At Home"],
        "program_length": [8, 8, 6], "time_per_workout": [45, 45, 30],
        "week": [1, 1, 1], "day": [1, 2, 1],
        "exercise_name": ["Squat", "Bench", "Sprint"],
        "sets": [3, 3, 5], "reps": [10, 10, 5], "intensity": [7, 7, 9],
    })


def diet_fixture(n=60, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "Patient_ID": [f"P{i:04d}" for i in range(n)],
        "Age": rng.integers(18, 70, n),
        "Gender": rng.choice(["Male", "Female"], n),
        "Weight_kg": rng.uniform(55, 110, n),
        "Height_cm": rng.integers(155, 195, n),
        "BMI": rng.uniform(18, 38, n),
        "Disease_Type": rng.choice(["Obesity", "Diabetes", "Hypertension", "None"], n),
        "Severity": rng.choice(["Mild", "Moderate", "Severe"], n),
        "Physical_Activity_Level": rng.choice(["Sedentary", "Moderate", "Active"], n),
        "Daily_Caloric_Intake": rng.integers(1600, 3400, n),
        "Cholesterol_mg/dL": rng.uniform(150, 250, n),
        "Blood_Pressure_mmHg": rng.integers(110, 180, n),
        "Glucose_mg/dL": rng.uniform(70, 200, n),
        "Dietary_Restrictions": rng.choice(["Low_Sodium", "Low_Sugar", "None"], n),
        "Allergies": rng.choice(["Gluten", "Peanuts", "None"], n),
        "Preferred_Cuisine": rng.choice(["Indian", "Chinese"], n),
        "Weekly_Exercise_Hours": rng.uniform(0, 10, n),
        "Adherence_to_Diet_Plan": rng.uniform(50, 100, n),
        "Dietary_Nutrient_Imbalance_Score": rng.uniform(0, 5, n),
        "Diet_Recommendation": rng.choice(["Balanced", "Low_Carb", "Low_Sodium"], n),
    })
    return df


def recommender_fixture(tmp_path):
    """FitnessRecommender with prepared Indian catalog + recipe fixture."""
    import joblib
    import pandas as pd
    from ml import train as T
    from ml.data_preparation import prepare_food_catalog, prepare_indian_catalog
    from ml.recommender import FitnessRecommender
    raw = tmp_path / "food_raw.csv"
    food_fixture().to_csv(raw, index=False)
    base = prepare_food_catalog(raw)
    food = prepare_indian_catalog(raw)
    assert len(food) == len(base) == 30  # all fixture names carry Indian evidence
    knn = {"general": T.fit_knn(food)}
    recipes = pd.DataFrame([
        {"name": "Test dal", "ingredients": "lentils, turmeric, salt",
         "diet": "vegetarian", "prep_time": 10, "cook_time": 20,
         "flavor_profile": "spicy", "course": "main course",
         "state": "Test", "region": "Test"},
        {"name": "Test peanut sweet", "ingredients": "peanuts, sugar",
         "diet": "vegetarian", "prep_time": 5, "cook_time": 10,
         "flavor_profile": "sweet", "course": "dessert",
         "state": "Test", "region": "Test"},
        {"name": "Test chicken curry", "ingredients": "chicken, yogurt, salt",
         "diet": "non vegetarian", "prep_time": 15, "cook_time": 30,
         "flavor_profile": "spicy", "course": "main course",
         "state": "Test", "region": "Test"},
    ])
    workout = workout_fixture()
    diet_model = joblib.load("artifacts/diet_model.joblib")
    diet_meta = {"target_distribution": {"Balanced": 1, "Low_Carb": 1, "Low_Sodium": 1},
                 "accuracy": 0.0, "f1_macro": 0.0, "f1_weighted": 0.0,
                 "dummy_accuracy": 0.0, "n_train": 1, "n_test": 1,
                 "feature_importance": [{"feature": "Age", "importance": 1.0}],
                 "disclaimer": "test"}
    return FitnessRecommender(diet_model, knn, food, workout,
                              {"version": "test"}, diet_meta, tmp_path,
                              recipes=recipes)
