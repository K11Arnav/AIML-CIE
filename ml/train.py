"""Train entry point: prepare data, train diet RF (+baseline), fit KNN, save artifacts, report.

Usage:  python -m ml.train
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import (ARTIFACTS_DIR, REPORTS_DIR, RANDOM_STATE, TEST_SIZE,
                     DIET_NUMERIC, DIET_CATEGORICAL, DIET_TARGET, KNN_NUTRITION_COLS)
from .data_preparation import (prepare_diet_frame, prepare_food_catalog,
                               prepare_indian_catalog, prepare_workout_catalog,
                               diet_features)
from .evaluation import classification_metrics


def build_diet_pipeline(num_cols, cat_cols) -> Pipeline:
    num = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    pre = ColumnTransformer([("num", num, num_cols), ("cat", cat, cat_cols)])
    clf = RandomForestClassifier(n_estimators=200, max_depth=None, min_samples_leaf=2,
                                 class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)
    return Pipeline([("preprocess", pre), ("clf", clf)])


def train_diet(df: pd.DataFrame):
    X, y = diet_features(df)
    num_cols = [c for c in DIET_NUMERIC if c in X.columns]
    cat_cols = [c for c in DIET_CATEGORICAL if c in X.columns]
    strat = y if y.value_counts().min() >= 2 else None
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=TEST_SIZE,
                                          random_state=RANDOM_STATE, stratify=strat)
    model = build_diet_pipeline(num_cols, cat_cols)
    model.fit(Xtr, ytr)
    dummy = Pipeline([("preprocess", build_diet_pipeline(num_cols, cat_cols).named_steps["preprocess"]),
                      ("clf", DummyClassifier(strategy="stratified", random_state=RANDOM_STATE))])
    dummy.fit(Xtr, ytr)
    labels = sorted(y.unique().tolist())
    m_rf = classification_metrics(yte, model.predict(Xte), labels)
    m_du = classification_metrics(yte, dummy.predict(Xte), labels)
    info = {"random_forest": m_rf, "dummy_stratified": m_du,
            "n_train": len(Xtr), "n_test": len(Xte),
            "features_numeric": num_cols, "features_categorical": cat_cols,
            "excluded": ["Patient_ID", "Disease_Type (target proxy)"],
            "target_distribution": y.value_counts().to_dict(),
            "feature_importance": _aggregate_importance(model, num_cols, cat_cols)}
    return model, info


def _aggregate_importance(model: Pipeline, num_cols, cat_cols) -> list:
    """Real RF importances, aggregated from one-hot back to base columns."""
    try:
        names = model.named_steps["preprocess"].get_feature_names_out()
        imps = model.named_steps["clf"].feature_importances_
    except Exception:
        return []
    agg = {}
    for name, imp in zip(names, imps):
        # names look like 'num__Age' or 'cat__Gender_Female'
        base = str(name).split("__", 1)[-1]
        for c in cat_cols:
            if base == c or base.startswith(c + "_"):
                base = c
                break
        agg[base] = agg.get(base, 0.0) + float(imp)
    total = sum(agg.values()) or 1.0
    return [{"feature": k, "importance": v / total}
            for k, v in sorted(agg.items(), key=lambda kv: -kv[1])]


def fit_knn(food: pd.DataFrame):
    cols = [c for c in KNN_NUTRITION_COLS if c in food.columns]
    Xn = food[cols].copy()
    medians = Xn.median()
    Xn = Xn.fillna(medians)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(Xn)
    nn = NearestNeighbors(n_neighbors=min(50, len(food)), metric="euclidean")
    nn.fit(Xs)
    return {"scaler": scaler, "nn": nn, "cols": cols, "medians": medians.to_dict()}


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics").mkdir(parents=True, exist_ok=True)

    # --- diet classifier ---
    diet_df = prepare_diet_frame()
    diet_model, diet_metrics = train_diet(diet_df)
    joblib.dump(diet_model, ARTIFACTS_DIR / "diet_model.joblib")
    (REPORTS_DIR / "metrics" / "diet_metrics.json").write_text(json.dumps(diet_metrics, indent=2))
    diet_meta = {
        "target": DIET_TARGET,
        "target_distribution": diet_metrics["target_distribution"],
        "accuracy": diet_metrics["random_forest"]["accuracy"],
        "f1_macro": diet_metrics["random_forest"]["f1_macro"],
        "f1_weighted": diet_metrics["random_forest"]["f1_weighted"],
        "dummy_accuracy": diet_metrics["dummy_stratified"]["accuracy"],
        "n_train": diet_metrics["n_train"], "n_test": diet_metrics["n_test"],
        "features_numeric": diet_metrics["features_numeric"],
        "features_categorical": diet_metrics["features_categorical"],
        "excluded": diet_metrics["excluded"],
        "feature_importance": diet_metrics["feature_importance"],
        "goal_is_not_a_feature": True,
        "disclaimer": ("Predicted category is a model output, not a medical diagnosis; "
                       "it is predicted from the health profile only, not the user's goal."),
    }
    (ARTIFACTS_DIR / "diet_meta.json").write_text(json.dumps(diet_meta, indent=2))

    # --- Indian-food catalog + KNN (single active catalog) ---
    full = prepare_food_catalog()
    food = prepare_indian_catalog()
    food.to_csv(ARTIFACTS_DIR / "indian_catalog.csv", index=False)
    knn = {"general": fit_knn(food)}
    joblib.dump(knn, ARTIFACTS_DIR / "knn.joblib")
    print(f"indian catalog: {len(food)} rows "
          f"(from {len(full)} after documented filter; "
          f"dishes={(food['cuisine_evidence'] == 'indian_dish').sum()})")
    # nutrition/health-score baseline reference (for recommender comparison)
    baseline_info = {"method": "health_score rank desc, then proteins_100g desc",
                     "n_items": len(food),
                     "limitation": "health_score is near-constant (76% equal 60)"}

    # --- recipe catalog (cleaned copy; text only, no nutrition merged in) ---
    from .recipes import prepare_recipe_catalog
    recipes, recipe_stats = prepare_recipe_catalog()
    recipes.drop(columns=["parsed_ingredients"]).to_csv(
        ARTIFACTS_DIR / "recipe_catalog.csv", index=False)
    (REPORTS_DIR / "metrics" / "recipe_stats.json").write_text(
        json.dumps(recipe_stats, indent=2))
    print(f"recipes: {recipe_stats['rows_after']} rows "
          f"(dupes removed {recipe_stats['exact_dupes_removed']})")

    # --- workout catalog (no classifier: no valid target; Gym Members data absent) ---
    workout = prepare_workout_catalog()
    workout.to_csv(ARTIFACTS_DIR / "workout_catalog.csv", index=False)

    meta = {"version": "1.2", "random_state": RANDOM_STATE,
            "diet_target": DIET_TARGET,
            "workout_classifier": "BLOCKED: no defensible target (Gym Members dataset absent; "
                                  "program titles are catalog entries, not outcome labels)",
            "food_catalog": {"file": "indian_catalog.csv",
                             "source": "healthy_foods_database.csv (filtered, see ml/indian_catalog.py)",
                             "rows": len(food),
                             "indian_dishes": int((food["cuisine_evidence"] == "indian_dish").sum()),
                             "staple_ingredients": int((food["cuisine_evidence"] == "staple_ingredient").sum()),
                             "allergen_data": False,
                             "use": "sole active food catalog: Indian-food-only recommendations"},
            "knn_features": knn["general"]["cols"]}
    (ARTIFACTS_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

    rf, du = diet_metrics["random_forest"], diet_metrics["dummy_stratified"]
    report = f"""# Evaluation Report

## Diet-category prediction (target `{DIET_TARGET}`, n=1000, test n={diet_metrics['n_test']})
Excluded from features: Patient_ID (identifier), Disease_Type (perfect target proxy/leakage).
Single stratified 80/20 split, seed {RANDOM_STATE}. Small dataset — generalization limits apply.

| model | accuracy | F1 macro | F1 weighted |
|---|---|---|---|
| RandomForest (200 trees, balanced) | {rf['accuracy']} | {rf['f1_macro']} | {rf['f1_weighted']} |
| Dummy (stratified) | {du['accuracy']} | {du['f1_macro']} | {du['f1_weighted']} |

Confusion matrix (RF, classes {rf['classes']}):
{rf['confusion_matrix']}

Note: RF barely beats the stratified dummy baseline because the perfectly
predictive Disease_Type column was excluded as leakage; remaining features carry
weak signal. Treat as informational triage, not diagnosis.

## Workout recommendation
No supervised classifier: Gym Members Exercise dataset absent locally and program
titles/goals are catalog attributes, not outcome labels. Workout output = hard-constraint
filtering + transparent ranking over the 605k-row exercise catalog (2,598 programs).
Offline checks: constraint-satisfaction rate, valid-result rate, empty-result handling
(see tests).

## KNN food ranking
Features (scaled): {knn['general']['cols']}. Sole active catalog: Indian-food derived
catalog ({len(food)} rows from healthy_foods_database via ml/indian_catalog.py).
Hard dietary/allergy filters applied BEFORE ranking; the Indian catalog has no
allergen data, so any requested allergy excludes all candidates with a warning.
No relevance ground truth exists → no Precision@K/NDCG claimed; offline checks cover
constraint satisfaction, top-K shape, determinism, and baseline comparison vs {baseline_info['method']}
({baseline_info['limitation']}).
"""
    (REPORTS_DIR / "evaluation_report.md").write_text(report)
    print(report)
    print(f"Saved artifacts to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
