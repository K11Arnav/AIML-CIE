"""System evaluation: 8 representative diet profiles against the real pipeline.

Writes reports/metrics/diet_evaluation.json and reports/diet_recommendation_evaluation.md.
Profiles are labeled TEST FIXTURES, not real users. Run: python -m ml.evaluate_diet_system
"""
import json

from .config import ARTIFACTS_DIR, REPORTS_DIR
from .recommender import FitnessRecommender

BASE = {"Severity": "Moderate", "Physical_Activity_Level": "Moderate",
        "Daily_Caloric_Intake": 2200, "Cholesterol_mg/dL": 185,
        "Blood_Pressure_mmHg": 125, "Glucose_mg/dL": 100,
        "Weekly_Exercise_Hours": 4, "Adherence_to_Diet_Plan": 80,
        "Dietary_Nutrient_Imbalance_Score": 2.0,
        "Dietary_Restrictions": "None", "Allergies": "None",
        "Preferred_Cuisine": "Indian"}

PROFILES = {
    "1_weight_loss": {**BASE, "Age": 35, "Gender": "Female", "Weight_kg": 68,
                      "Height_cm": 168, "goal": "Weight Loss", "top_k": 10,
                      "note": "TEST FIXTURE: typical weight-loss seeker"},
    "2_muscle_gain": {**BASE, "Age": 28, "Gender": "Male", "Weight_kg": 80,
                      "Height_cm": 180, "Physical_Activity_Level": "Active",
                      "Weekly_Exercise_Hours": 7, "goal": "Muscle", "top_k": 10,
                      "note": "TEST FIXTURE: muscle-gain seeker"},
    "3_vegetarian": {**BASE, "Age": 30, "Gender": "Female", "Weight_kg": 60,
                     "Height_cm": 165, "goal": "Balanced",
                     "dietary_restrictions": ["Vegetarian"], "top_k": 10,
                     "note": "TEST FIXTURE: vegetarian is NOT a supported restriction"},
    "4_low_sugar": {**BASE, "Age": 45, "Gender": "Male", "Weight_kg": 90,
                    "Height_cm": 175, "Glucose_mg/dL": 190, "goal": "Weight Loss",
                    "dietary_restrictions": ["Low_Sugar"], "top_k": 10,
                    "note": "TEST FIXTURE: low-sugar preference"},
    "5_low_sodium": {**BASE, "Age": 55, "Gender": "Female", "Weight_kg": 72,
                     "Height_cm": 160, "Blood_Pressure_mmHg": 165, "goal": "Balanced",
                     "dietary_restrictions": ["Low_Sodium"], "top_k": 10,
                     "note": "TEST FIXTURE: low-sodium preference"},
    "6_peanut_allergy": {**BASE, "Age": 25, "Gender": "Male", "Weight_kg": 70,
                         "Height_cm": 175, "goal": "Weight Loss",
                         "allergies": ["Peanuts"], "top_k": 10,
                         "note": "TEST FIXTURE: peanut allergy (safety-critical)"},
    "7_multi_constraint": {**BASE, "Age": 50, "Gender": "Female", "Weight_kg": 75,
                           "Height_cm": 162, "goal": "Balanced",
                           "dietary_restrictions": ["Low_Sodium"],
                           "allergies": ["Peanuts", "Sesame"], "top_k": 10,
                           "note": "TEST FIXTURE: restriction + known + unmapped allergy"},
    "8a_minimal": {"goal": "balanced", "top_k": 5,
                   "note": "TEST FIXTURE: nearly empty input (imputation path)"},
}

INVALID = [
    ("8b_top_k_999", {"top_k": 999}),
    ("8c_top_k_0", {"top_k": 0}),
    ("8d_non_dict", "not-a-dict"),
]


def summarize(rec, name, prof):
    prof = {k: v for k, v in prof.items() if k != "note"}
    try:
        r = rec.recommend_diet(dict(prof))
    except Exception as e:
        return {"profile": name, "error": f"{type(e).__name__}: {e}"}
    items = r["items"]
    return {
        "profile": name,
        "predicted_category": r["diet_category"]["diet_category"],
        "probabilities": r["diet_category"]["probabilities"],
        "goal_profile": r["goal_profile"],
        "catalog": r["catalog_used"],
        "counts": r["candidate_counts"],
        "restrictions_enforced": r["restrictions_enforced"],
        "filter_notes": r["filter_notes"],
        "unmet": r.get("unmet"),
        "allergen_warning": r.get("allergen_warning"),
        "items": [{"rank": i["rank"], "name": i["product_name"],
                   "kcal": i["energy_kcal"], "protein": i["proteins_100g"],
                   "carbs": i["carbs_100g"], "fat": i["fat_100g"],
                   "sugar": i["sugars_100g"], "fiber": i["fiber_100g"],
                   "sodium_g": i["sodium_100g"], "missing": i["missing_nutrition"],
                   "distance": i["distance"],
                   "evidence": i["explanation"]["cuisine_evidence"],
                   "allergy": i["explanation"]["allergy_status"]} for i in items],
    }


def main() -> None:
    rec = FitnessRecommender.load(ARTIFACTS_DIR)
    results = [summarize(rec, n, p) for n, p in PROFILES.items()]
    invalid = []
    for n, p in INVALID:
        try:
            rec.recommend_diet(p)
            invalid.append({"case": n, "outcome": "NO ERROR (unexpected)"})
        except (ValueError, TypeError) as e:
            invalid.append({"case": n, "outcome": f"rejected: {e}"})
    # RF sensitivity: same profile, perturbed vitals -> does prediction move?
    base = {k: v for k, v in PROFILES["1_weight_loss"].items() if k != "note"}
    low_risk = {**base, "Cholesterol_mg/dL": 150, "Glucose_mg/dL": 80,
                "Blood_Pressure_mmHg": 110, "BMI": 21.0}
    high_risk = {**base, "Cholesterol_mg/dL": 249, "Glucose_mg/dL": 200,
                 "Blood_Pressure_mmHg": 179, "BMI": 38.0}
    sensitivity = {
        "low_risk_vitals": rec.predict_diet_category(low_risk)["diet_category"],
        "high_risk_vitals": rec.predict_diet_category(high_risk)["diet_category"],
        "note": "Checks the model is not constant; NOT a validity proof.",
    }
    payload = {"profiles": results, "invalid_inputs": invalid,
               "rf_sensitivity": sensitivity,
               "knn_features": rec._knn["general"]["cols"] if isinstance(rec._knn, dict) else rec._knn["cols"]}
    (REPORTS_DIR / "metrics").mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "metrics" / "diet_evaluation.json").write_text(json.dumps(payload, indent=2))
    _write_report(payload)
    print("wrote reports/diet_recommendation_evaluation.md + metrics/diet_evaluation.json")


def _write_report(p: dict) -> None:
    L = ["# Diet Recommendation Evaluation (2026-10-15)",
         "", "Implementation-only audit: no new datasets, no model-target changes.",
         "All profiles are labeled test fixtures.", ""]
    for r in p["profiles"]:
        L += [f"## {r['profile']}", ""]
        if "error" in r:
            L += [f"- ERROR: {r['error']}", ""]
            continue
        L += [f"- RF: **{r['predicted_category']}** {r['probabilities']}",
              f"- goal profile: {r['goal_profile']} | catalog: {r['catalog']['key']} "
              f"({r['catalog']['source_dataset']})",
              f"- candidates: {r['counts']['before_filtering']} -> {r['counts']['after_filtering']}",
              f"- enforced: {r['restrictions_enforced'] or 'none'}",
              f"- notes: {r['filter_notes'] or 'none'}",
              f"- unmet: {r['unmet']}", ""]
        for i in r["items"]:
            L += [f"  {i['rank']}. {i['name']} — {i['kcal']} kcal, P {i['protein']}g, "
                  f"C {i['carbs']}g, F {i['fat']}g, sugar {i['sugar']}, fiber {i['fiber']}, "
                  f"Na {i['sodium_g']}g (per 100 g) | dist {i['distance']} | "
                  f"missing={i['missing'] or 'none'} | {i['evidence']} | allergy={i['allergy']}"]
        L += [""]
    L += ["## Invalid inputs",
          *[f"- {c['case']}: {c['outcome']}" for c in p["invalid_inputs"]], "",
          "## RF sensitivity",
          f"- low-risk vitals -> {p['rf_sensitivity']['low_risk_vitals']}, "
          f"high-risk vitals -> {p['rf_sensitivity']['high_risk_vitals']}",
          f"- {p['rf_sensitivity']['note']}", "",
          f"KNN features: {p['knn_features']}", ""]
    (REPORTS_DIR / "diet_recommendation_evaluation.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
