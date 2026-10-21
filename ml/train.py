"""Train all models from the five current datasets/ files only. No other data.

Outputs (artifacts/):
  workout_model.joblib   RF classifier: 8 profile features -> plan class
  diet_model.joblib      RF regressor: profile -> calorie target + macros
  knn.joblib             scaled KNN bundle over the Anuvaad food catalog
  food_catalog.csv       Anuvaad per-100g catalog
  nutrition_catalog.csv  cleaned nutrition rows (macros + meal suggestions)
  exercise_library.json  slim exercise library from exercises.json
  meta.json / diet_meta.json

Every materialized number (rows, cleaning counts, metrics, baselines) is
written to reports/ so results are auditable. Old boostcamp program data and
the missing diet/healthy-foods files are fully retired.
"""
import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error,
                             r2_score)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (ARTIFACTS_DIR, REPORTS_DIR, RANDOM_STATE, TEST_SIZE,
                     DIET_FEATURE_CATEGORICAL, DIET_FEATURE_NUMERIC,
                     DIET_TARGETS, KNN_NUTRITION_COLS,
                     WORKOUT_FEATURE_CATEGORICAL, WORKOUT_FEATURE_NUMERIC,
                     WORKOUT_TARGET)
from .data_preparation import (load_exercise_library, prepare_food_catalog,
                               prepare_nutrition_frame, prepare_workout_frame,
                               survey_values)
from .evaluation import classification_metrics
from .plan_layout import PLAN_LAYOUTS

WORKOUT_PREPROCESS = ColumnTransformer(
    [("num", "passthrough", WORKOUT_FEATURE_NUMERIC),
     ("cat", OneHotEncoder(handle_unknown="ignore"), WORKOUT_FEATURE_CATEGORICAL)])
DIET_PREPROCESS = ColumnTransformer(
    [("num", "passthrough", DIET_FEATURE_NUMERIC),
     ("cat", OneHotEncoder(handle_unknown="ignore"), DIET_FEATURE_CATEGORICAL)])


def train_workout_classifier(df: pd.DataFrame) -> tuple[dict, dict]:
    """RF classifier on smartfit_workout_dataset.csv (profile -> plan)."""
    X, y = df[WORKOUT_FEATURE_NUMERIC + WORKOUT_FEATURE_CATEGORICAL], df[WORKOUT_TARGET]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE,
                                          random_state=RANDOM_STATE, stratify=y)
    pipe = Pipeline([("preprocess", WORKOUT_PREPROCESS),
                     ("rf", RandomForestClassifier(n_estimators=80, max_depth=12,
                                                   random_state=RANDOM_STATE,
                                                   n_jobs=-1))])
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    metrics = classification_metrics(yte, pred, labels=sorted(y.unique()))
    dummy = DummyClassifier(strategy="most_frequent").fit(Xtr, ytr)
    metrics["dummy_accuracy"] = round(float(accuracy_score(
        yte, dummy.predict(Xte))), 4)
    classes = sorted(y.unique().tolist())
    covered = set(classes) - set(PLAN_LAYOUTS)
    if covered:
        raise ValueError(f"PLAN_LAYOUTS missing layout for plan classes: {covered}")
    bundle = {"pipeline": pipe, "classes": classes, "target": WORKOUT_TARGET,
              "features": {"numeric": WORKOUT_FEATURE_NUMERIC,
                           "categorical": WORKOUT_FEATURE_CATEGORICAL},
              "train_rows": int(len(Xtr)), "test_rows": int(len(Xte))}
    return bundle, metrics


def train_diet_regressor(df: pd.DataFrame) -> tuple[dict, dict]:
    """RF regressor on nutrition_dataset.csv (profile -> calorie target + macros)."""
    X = df[DIET_FEATURE_NUMERIC + DIET_FEATURE_CATEGORICAL].copy()
    y = df[DIET_TARGETS].copy()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE,
                                          random_state=RANDOM_STATE)
    pipe = Pipeline([("preprocess", DIET_PREPROCESS),
                     ("rf", RandomForestRegressor(n_estimators=80, max_depth=12,
                                                  random_state=RANDOM_STATE,
                                                  n_jobs=-1))])
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    dummy_pred = DummyRegressor(strategy="mean").fit(Xtr, ytr).predict(Xte)
    metrics = {"targets": DIET_TARGETS, "per_target": {}}
    for i, c in enumerate(DIET_TARGETS):
        y_true_i, y_pred_i, y_base_i = (yte.values[:, i], pred[:, i], dummy_pred[:, i])
        metrics["per_target"][c] = {
            "mae": round(float(mean_absolute_error(y_true_i, y_pred_i)), 3),
            "r2": round(float(r2_score(y_true_i, y_pred_i)), 3),
            "baseline_mae": round(float(mean_absolute_error(y_true_i, y_base_i)), 3),
        }
    bundle = {"pipeline": pipe, "targets": DIET_TARGETS,
              "features": {"numeric": DIET_FEATURE_NUMERIC,
                           "categorical": DIET_FEATURE_CATEGORICAL},
              "train_rows": int(len(Xtr)), "test_rows": int(len(Xte))}
    return bundle, metrics


def fit_knn(food: pd.DataFrame) -> dict:
    """Scaled KNN over the Anuvaad per-100g catalog (same policy as before)."""
    cols = KNN_NUTRITION_COLS
    X = food[cols].fillna(0.0)
    scaler = StandardScaler().fit(X)
    nn = NearestNeighbors(n_neighbors=min(30, len(food))).fit(scaler.transform(X))
    medians = {c: float(food[c].median()) for c in cols}
    return {"cols": cols, "scaler": scaler, "nn": nn, "medians": medians}


def main() -> None:
    for d in (ARTIFACTS_DIR, REPORTS_DIR / "metrics"):
        d.mkdir(parents=True, exist_ok=True)

    # --- workout classifier (smartfit) ---
    workout = prepare_workout_frame()
    print(f"workout frame: {workout.attrs['rows_before']} rows -> "
          f"{workout.attrs['rows_after']} (dupes {workout.attrs['exact_dupes_removed']})")
    workout_bundle, workout_metrics = train_workout_classifier(workout)
    print(f"workout RF: acc={workout_metrics['accuracy']} "
          f"f1_macro={workout_metrics['f1_macro']} "
          f"dummy={workout_metrics['dummy_accuracy']}")

    # --- diet macro regressor (nutrition_dataset) ---
    nutrition = prepare_nutrition_frame()
    print(f"nutrition frame: {nutrition.attrs['rows_before']} -> "
          f"{nutrition.attrs['rows_after']} "
          f"(junk {nutrition.attrs['junk_header_rows_removed']}, "
          f"merged {nutrition.attrs['weight_maintenance_merged']}, "
          f"bad {nutrition.attrs['nonpositive_missing_dropped']})")
    diet_bundle, diet_metrics = train_diet_regressor(nutrition)
    for target, m in diet_metrics["per_target"].items():
        print(f"diet RF {target}: MAE={m['mae']} (baseline {m['baseline_mae']}) "
              f"R2={m['r2']}")

    # --- food catalog (Anuvaad INDB) + KNN bundle ---
    food = prepare_food_catalog()
    print(f"food catalog: {food.attrs['rows_before']} -> {food.attrs['rows_after']} "
          f"(dupes {food.attrs['exact_dupes_removed']}, "
          f"outliers {food.attrs['n_outliers_excluded']})")
    knn = {"general": fit_knn(food)}
    print(f"knn bundle: {len(food)} foods over {KNN_NUTRITION_COLS}")

    # --- exercise library ---
    library = load_exercise_library()
    print(f"exercise library: {library.attrs['rows']} exercises")

    # --- persist artifacts ---
    workout = workout.reset_index(drop=True)
    nutrition = nutrition.reset_index(drop=True)
    food = food.reset_index(drop=True)
    library = library.reset_index(drop=True)
    workout.to_csv(ARTIFACTS_DIR / "workout_training_frame.csv", index=False)
    nutrition.to_csv(ARTIFACTS_DIR / "nutrition_catalog.csv", index=False)
    food.to_csv(ARTIFACTS_DIR / "food_catalog.csv", index=False)
    library.to_json(ARTIFACTS_DIR / "exercise_library.json", orient="records")
    import joblib
    joblib.dump(workout_bundle, ARTIFACTS_DIR / "workout_model.joblib")
    joblib.dump(diet_bundle, ARTIFACTS_DIR / "diet_model.joblib")
    joblib.dump(knn, ARTIFACTS_DIR / "knn.joblib")

    survey = survey_values()
    # survey_values runs prep again (cheap, deterministic); keep the same frame
    provenance = {
        "workout_training_frame.csv": {
            "source": "datasets/smartfit_workout_dataset.csv", **workout.attrs},
        "nutrition_catalog.csv": {
            "source": "datasets/nutrition_dataset.csv", **nutrition.attrs},
        "food_catalog.csv": {
            "source": "datasets/Anuvaad_INDB_2024.11.xlsx", **food.attrs},
        "exercise_library.json": {
            "source": "datasets/exercises.json", **library.attrs},
    }
    meta = {
        "version": "2.0",
        "random_state": RANDOM_STATE, "test_size": TEST_SIZE,
        "data": provenance,
        "readable": {
            "workout": f"RF classifier on smartfit_workout_dataset.csv: "
                       f"features={WORKOUT_FEATURE_NUMERIC + WORKOUT_FEATURE_CATEGORICAL}, "
                       f"target={WORKOUT_TARGET}, {len(workout_bundle['classes'])} plan classes",
            "diet": f"RF regressor on nutrition_dataset.csv: "
                    f"features={DIET_FEATURE_NUMERIC + DIET_FEATURE_CATEGORICAL}, "
                    f"targets={DIET_TARGETS}",
            "food_knn": "scaled KNN over Anuvaad per-100g columns "
                        f"{KNN_NUTRITION_COLS} (goal reference vectors)",
        },
        "workout_metrics": workout_metrics,
        "diet_metrics": diet_metrics,
        "values": survey,
        "allergen_policy": ("The Anuvaad food DB has NO allergen flags: any "
                            "requested allergy fails closed (all foods excluded "
                            "with a warning). Compatibility is never assumed."),
        "notes": [
            "Trained ONLY from the five datasets/ files present now; the old "
            "boostcamp program catalog, diet_recommendations_dataset.csv, "
            "healthy_foods_database.csv and indian_food.csv are retired.",
            "Compact RFs (80 trees, max_depth 12) chosen deliberately: test "
            "metrics identical to larger configs with ~10x smaller artifacts.",
            "Workout plan layout uses datasets/exercises.json via the "
            "documented mapping in ml/plan_layout.py.",
            "Duration estimates are heuristics: no per-plan durations exist "
            "in any training dataset.",
            "Informational only — not medical advice.",
        ],
    }
    (ARTIFACTS_DIR / "meta.json").write_text(json.dumps(meta, indent=2))
    diet_meta = {
        "targets": DIET_TARGETS,
        "features": {"numeric": DIET_FEATURE_NUMERIC,
                     "categorical": DIET_FEATURE_CATEGORICAL},
        "metrics": diet_metrics["per_target"],
        "train_rows": diet_bundle["train_rows"], "test_rows": diet_bundle["test_rows"],
        "data_source": "datasets/nutrition_dataset.csv",
        "disclaimer": ("Model prediction from profile only — informational, "
                       "not medical advice."),
    }
    (ARTIFACTS_DIR / "diet_meta.json").write_text(json.dumps(diet_meta, indent=2))
    (REPORTS_DIR / "metrics" / "workout_metrics.json").write_text(
        json.dumps({"data": workout.attrs, **workout_metrics}, indent=2))
    (REPORTS_DIR / "metrics" / "diet_metrics.json").write_text(
        json.dumps({"data": nutrition.attrs, **diet_metrics}, indent=2))
    (REPORTS_DIR / "metrics" / "food_knn.json").write_text(
        json.dumps({"rows": int(len(food)), "cols": KNN_NUTRITION_COLS,
                    "goal_targets": "config.GOAL_NUTRITION_TARGETS"}, indent=2))
    print("training complete -> artifacts/ updated")


if __name__ == "__main__":
    main()
