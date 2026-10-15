# Dataset Transparency: Diet Recommendation Pipeline

All figures verified against the implementation (`ml/config.py`, `ml/data_preparation.py`,
`ml/train.py`, `ml/recommender.py`). A column is listed only if code actually reads it.

## Datasets in use

### 1. `diet_recommendations_dataset.csv` — Random Forest training data
- Rows/cols before: 1000 × 20. After: 1000 × 20 (0 exact duplicates; no labels missing).
- Target column: `Diet_Recommendation` → predicts `Balanced` (426), `Low_Sodium` (316), `Low_Carb` (258).
- RF input columns (17): numeric `Age, Weight_kg, Height_cm, BMI, Daily_Caloric_Intake,
  Cholesterol_mg/dL, Blood_Pressure_mmHg, Glucose_mg/dL, Weekly_Exercise_Hours,
  Adherence_to_Diet_Plan, Dietary_Nutrient_Imbalance_Score` (median-imputed);
  categorical `Gender, Severity, Physical_Activity_Level, Dietary_Restrictions,
  Allergies, Preferred_Cuisine` (most-frequent-imputed, one-hot, unknown-ignored).
- Excluded: `Patient_ID` (identifier), `Disease_Type` (perfect target proxy =
  leakage: Diabetes→Low_Carb, Hypertension→Low_Sodium, else Balanced).
- Missing: `Dietary_Restrictions` 33.4%, `Allergies` 32.3%, `Disease_Type` 20.4%
  → filled with `"None"` level. The user's `goal` is NOT a feature.
- Train/test: stratified 80/20, seed 42. Test accuracy 0.39 vs dummy 0.38
  (F1-macro 0.37 vs 0.35) — weak signal, honestly reported.

### 2. `healthy_foods_database.csv` — general food catalog (default KNN ranking)
- Rows/cols before: 9028 × 10. After: **8178** active (559 exact dupes removed,
  ~291 unit-error rows excluded: calories > 950/100g or sodium > 100 g/100g).
- Columns used for KNN (all per 100 g): `energy_kcal, fat_100g, carbs_100g,
  sugars_100g, fiber_100g, proteins_100g, sodium_100g` (sodium converted mg→g, ÷1000).
- Columns used for display: `product_name` (verbatim), `food_type`, `health_score`.
- Columns used for dietary filtering: `sodium_100g` (Low_Sodium ≤ 0.4 g),
  `sugars_100g` (Low_Sugar ≤ 5.0 g).
- Allergen columns: NONE — allergy compatibility can never be established here.
- Missing: sugar 11.1%, fiber 3.9%, sodium 0.8%, protein 0.08%, fat 0.16%,
  carbs 0.29% → median-imputed for KNN distance, reported per item in
  `missing_nutrition`, displayed as "–", never zero.
- Limitation: `health_score` is near-constant (76% equal 60); names mix general
  foods with some US branded items (kept verbatim).

### 3. `foods_health_scores_allergens.csv` — allergen-annotated catalog (allergy path only)
- Rows/cols before: 4997 × 24. After: **4959** active (38 exact dupes removed).
- Same 7 KNN nutrition columns (per 100 g, natively; fiber 30.1% missing).
- Allergy filtering columns: `contains_gluten, contains_dairy, contains_nuts,
  contains_soy, contains_eggs, contains_fish` (0% missing).
- Flag reliability (measured, not assumed): allergen-text mentions agree with
  flags 100% (milk n=1492, peanut n=154, gluten n=1599, soy n=847, egg n=318);
  only 1 product with "peanut" in its name has `contains_nuts=false`.
- Limitation: branded packaged products, less recognizable; used ONLY when
  allergy filtering is requested, and the response names its source dataset.

## Merges: none
No datasets were merged. `foods_dietary_restrictions.csv` is a byte-identical
derived copy (0 new columns) — not merged. `foods_allergens.csv` conflicts with
the annotated catalog on 1–11% of overlapping flag values — not merged.
`comprehensive_foods_usda.csv` (40k rows) is a redundant superset with no
allergen data — not merged. `program_summary.csv` duplicates detailed titles —
not merged. Join keys were never invented; index/order merges were refused.

## Excluded datasets and reasons
| file | reason |
|---|---|
| `foods_dietary_restrictions.csv` | derived duplicate, contributes nothing |
| `foods_allergens.csv` | conflicting allergen labels, no stable key |
| `comprehensive_foods_usda.csv` | redundant superset, no allergen data, 4.4× larger |
| `program_summary.csv` | titles fully overlap detailed workout data |
| Gym Members Exercise dataset | absent locally → workout classifier blocked (no fabricated labels) |
