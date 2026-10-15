# Evaluation Report

## Diet-category prediction (target `Diet_Recommendation`, n=1000, test n=200)
Excluded from features: Patient_ID (identifier), Disease_Type (perfect target proxy/leakage).
Single stratified 80/20 split, seed 42. Small dataset — generalization limits apply.

| model | accuracy | F1 macro | F1 weighted |
|---|---|---|---|
| RandomForest (200 trees, balanced) | 0.39 | 0.3682 | 0.3865 |
| Dummy (stratified) | 0.38 | 0.3473 | 0.3691 |

Confusion matrix (RF, classes ['Balanced', 'Low_Carb', 'Low_Sodium']):
[[42, 23, 20], [24, 12, 16], [27, 12, 24]]

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
Features (scaled): ['energy_kcal', 'fat_100g', 'carbs_100g', 'sugars_100g', 'fiber_100g', 'proteins_100g', 'sodium_100g']. Sole active catalog: Indian-food derived
catalog (100 rows from healthy_foods_database via ml/indian_catalog.py).
Hard dietary/allergy filters applied BEFORE ranking; the Indian catalog has no
allergen data, so any requested allergy excludes all candidates with a warning.
No relevance ground truth exists → no Precision@K/NDCG claimed; offline checks cover
constraint satisfaction, top-K shape, determinism, and baseline comparison vs health_score rank desc, then proteins_100g desc
(health_score is near-constant (76% equal 60)).
