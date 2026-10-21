"""Shared fixtures: tiny synthetic frames + micro-trained real pipelines.

No raw data files are read; every fixture constructs frames with the exact
training schema from ml.config and micro-trains so recommender logic is
tested end-to-end without the large real artifacts.
"""
import json

import numpy as np
import pandas as pd
import pytest

from ml.train import fit_knn, train_diet_regressor, train_workout_classifier
from ml.data_preparation import load_exercise_library
from ml.config import ALLERGEN_FLAG_COLS
from ml.allergens import derive_allergens
from ml.recommender import FitnessRecommender

rng = np.random.default_rng(0)


def workout_frame_fixture(n=160, seed=1):
    """smartfit-workout-schema fixture with a deterministic rule."""
    r = np.random.default_rng(seed)
    goals = ["Muscle Gain", "Weight Loss", "General Health", "Flexibility"]
    equip = ["Bodyweight Only", "Yoga Mat", "Home Dumbbells", "Full Home Gym"]
    inj = ["None", "Knee", "Back"]
    plans = {
        ("Muscle Gain", "Full Home Gym", "None"): "5x5 Compound Lifts",
        ("Weight Loss", "Home Dumbbells", "None"): "Full Body Dumbbell Complex",
        ("Weight Loss", "Bodyweight Only", "Knee"): "Bodyweight Circuit",
        ("Flexibility", "Yoga Mat", "None"): "Yoga & Mobility Flow",
        ("General Health", "Bodyweight Only", "None"): "Bodyweight Circuit",
    }
    rows = []
    ages = r.integers(18, 60, n)
    for i in range(n):
        goal = goals[i % len(goals)]
        eq = equip[i % len(equip)]
        # make equipment/goal pairs deterministic per goal to keep a learnable rule
        eq = "Yoga Mat" if goal == "Flexibility" else ("Full Home Gym" if goal == "Muscle Gain"
                                                      else ("Home Dumbbells" if goal == "Weight Loss"
                                                            else "Bodyweight Only"))
        inj_v = inj[i % len(inj)] if np.random.default_rng(seed + i).random() < 0.3 else "None"
        plan = plans.get((goal, eq, inj_v),
                         plans.get((goal, eq, "None"),
                                   "Bodyweight Circuit"))
        rows.append({
            "Age": int(ages[i]), "Gender": "Male" if i % 2 else "Female",
            "Weight_kg": round(float(r.uniform(55, 100)), 1),
            "Height_cm": int(r.integers(150, 195)),
            "Goal": goal, "Equipment": eq, "Experience": "Beginner",
            "Injury": inj_v,
            "Recommended_Plan": plan,
        })
    return pd.DataFrame(rows)


def nutrition_frame_fixture(n=120, seed=2):
    """nutrition-dataset-schema fixture with a deterministic but noisy rule."""
    r = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        w = r.uniform(55, 95)
        act = r.choice(["Sedentary", "Moderately Active", "Very Active"])
        goal = r.choice(["Weight Loss", "Maintenance", "Muscle Gain"])
        base = 1400 + w * 8 + (0 if act == "Sedentary" else 150 if act == "Moderately Active" else 350)
        if goal == "Weight Loss":
            base -= 200
        elif goal == "Muscle Gain":
            base += 200
        pref = r.choice(["Omnivore", "Vegetarian", "Vegan"])
        rows.append({
            "Age": int(r.integers(18, 60)), "Gender": "Male" if i % 2 else "Female",
            "Height": int(r.integers(150, 195)), "Weight": round(w, 1),
            "Activity Level": act, "Fitness Goal": goal,
            "Dietary Preference": pref,
            "Daily Calorie Target": int(base), "Protein": int(w * 1.2),
            "Carbohydrates": int(base * 0.45 / 4), "Fat": int(base * 0.25 / 9),
            "Breakfast Suggestion": f"breakfast-{pref.lower()}",
            "Lunch Suggestion": f"lunch-{goal.lower()}",
            "Dinner Suggestion": f"dinner-{pref.lower()}",
            "Snack Suggestion": "fruit",
        })
    return pd.DataFrame(rows)


def food_frame_fixture(n=24, seed=3):
    """Anuvaad-schema fixture (canonical per-100g columns + derived allergen
    flags via the real keyword rules)."""
    r = np.random.default_rng(seed)
    names = [f"test food {i}" for i in range(n)]
    names[1] = "peanut chikki bar"
    names[2] = "paneer curry"
    names[3] = "wheat bread slice"
    df = pd.DataFrame({
        "food_code": [f"F{i:04d}" for i in range(n)],
        "product_name": names,
        "energy_kj": r.uniform(50, 2000, n),
        "energy_kcal": r.uniform(20, 400, n),
        "proteins_100g": r.uniform(0, 25, n),
        "fat_100g": r.uniform(0, 20, n),
        "carbs_100g": r.uniform(0, 60, n),
        "sugars_100g": r.uniform(0, 15, n),
        "fiber_100g": r.uniform(0, 8, n),
        "sodium_100g": r.uniform(0.01, 0.6, n),
    })
    df.loc[0, "sugars_100g"] = np.nan  # missing nutrition must be reported, not zeroed
    flags = pd.DataFrame([derive_allergens(nm) for nm in names],
                         index=df.index)
    for c in ALLERGEN_FLAG_COLS:
        df[c] = flags[c].astype(bool)
    return df


def library_fixture():
    """exercise-library-schema fixture: few moves per body part/equipment."""
    rows = [
        {"id": "e1", "name": "Bodyweight Squat", "body_part": "upper legs",
         "equipment": "body weight", "category": "upper legs",
         "instruction_steps": "squat"},
        {"id": "e2", "name": "Goblet Squat", "body_part": "upper legs",
         "equipment": "dumbbell", "category": "upper legs",
         "instruction_steps": "hold bell"},
        {"id": "e3", "name": "Plank", "body_part": "waist", "equipment": "body weight",
         "category": "waist", "instruction_steps": "hold"},
        {"id": "e4", "name": "Push-Up", "body_part": "chest", "equipment": "body weight",
         "category": "chest", "instruction_steps": "push"},
        {"id": "e5", "name": "Dumbbell Press", "body_part": "chest", "equipment": "dumbbell",
         "category": "chest", "instruction_steps": "press"},
        {"id": "e6", "name": "Bench Press", "body_part": "chest", "equipment": "barbell",
         "category": "chest", "instruction_steps": "bench"},
        {"id": "e7", "name": "Jumping Jack", "body_part": "cardio",
         "equipment": "body weight", "category": "cardio", "instruction_steps": "jump"},
        {"id": "e8", "name": "Chest Press Machine", "body_part": "chest",
         "equipment": "leverage machine", "category": "chest",
         "instruction_steps": "press machine"},
    ]
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def micro_bundles():
    wf = workout_frame_fixture()
    nf = nutrition_frame_fixture()
    workout_bundle, workout_metrics = train_workout_classifier(wf)
    diet_bundle, diet_metrics = train_diet_regressor(nf)
    food = food_frame_fixture()
    knn = {"general": fit_knn(food)}
    return {"workout_bundle": workout_bundle, "workout_metrics": workout_metrics,
            "diet_bundle": diet_bundle, "diet_metrics": diet_metrics,
            "food": food, "knn": knn}


@pytest.fixture(scope="session")
def recommender(micro_bundles):
    mb = micro_bundles
    meta = {
        "version": "test",
        "values": {"workout": {"goals": ["Muscle Gain", "Weight Loss",
                                         "General Health", "Flexibility"],
                               "equipment": ["Bodyweight Only", "Yoga Mat",
                                             "Home Dumbbells", "Full Home Gym"],
                               "levels": ["Beginner", "Intermediate", "Advanced"],
                               "injuries": ["None", "Knee", "Back"]},
                   "diet": {}},
        "workout_metrics": {"accuracy": mb["workout_metrics"]["accuracy"],
                            "f1_macro": mb["workout_metrics"]["f1_macro"],
                            "dummy_accuracy": mb["workout_metrics"]["dummy_accuracy"]},
        "diet_metrics": {"per_target": mb["diet_metrics"]["per_target"]},
    }
    diet_meta = {"targets": mb["diet_bundle"]["targets"], "metrics": {}, "disclaimer": "test"}
    return FitnessRecommender(mb["workout_bundle"], mb["knn"], mb["food"],
                              mb["diet_bundle"], meta, diet_meta,
                              "/tmp", nutrition=nutrition_frame_fixture(),
                              library=library_fixture())


@pytest.fixture(scope="session")
def library():
    return library_fixture()


def jsonable(obj, tmp_path):
    """Assert the full response is JSON-serializable (API contract)."""
    out = tmp_path / "out.json"
    out.write_text(json.dumps(obj, default=str))
    return json.loads(out.read_text())
