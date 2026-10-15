# Dataset Audit

Source directory: `/home/arnav_kulkarni/Documents/Aiml cie/datasets`

## programs_detailed_boostcamp_kaggle.csv — **USED**
- rows: 2535325, columns: 16, size: 294.83 MB
- columns: title, description, level, goal, equipment, program_length, time_per_workout, week, day, number_of_exercises, exercise_name, sets, reps, intensity, created, last_edit
- missing% (sample): {'title': 0.0, 'description': 0.0, 'level': 0.0, 'goal': 0.0, 'equipment': 0.0, 'program_length': 0.0, 'time_per_workout': 0.0, 'week': 0.0, 'day': 0.0, 'number_of_exercises': 0.0, 'exercise_name': 0.0, 'sets': 0.0}
- duplicate rows (sample of 5000): 4
- decision: Primary workout/exercise catalog (filter + rank). NOT classifier training data: no defensible supervised target; Gym Members Exercise dataset absent locally.

## program_summary.csv — **ARCHIVED**
- rows: None, columns: None, size: None MB
- columns: 
- missing% (sample): None
- duplicate rows (sample of 5000): None
- decision: Moved to data/archive_unused/: titles fully redundant with detailed data. Only referenced by this audit script (tolerates missing files).

## diet_recommendations_dataset.csv — **USED**
- rows: 1000, columns: 20, size: 0.12 MB
- columns: Patient_ID, Age, Gender, Weight_kg, Height_cm, BMI, Disease_Type, Severity, Physical_Activity_Level, Daily_Caloric_Intake, Cholesterol_mg/dL, Blood_Pressure_mmHg, Glucose_mg/dL, Dietary_Restrictions, Allergies, Preferred_Cuisine, Weekly_Exercise_Hours, Adherence_to_Diet_Plan, Dietary_Nutrient_Imbalance_Score, Diet_Recommendation
- missing% (sample): {'Dietary_Restrictions': 33.4, 'Allergies': 32.3, 'Disease_Type': 20.4, 'Patient_ID': 0.0, 'Age': 0.0, 'Gender': 0.0, 'Weight_kg': 0.0, 'Height_cm': 0.0, 'BMI': 0.0, 'Severity': 0.0, 'Physical_Activity_Level': 0.0, 'Daily_Caloric_Intake': 0.0}
- duplicate rows (sample of 5000): 0
- decision: Diet-category classifier training data. Target Diet_Recommendation (Balanced/Low_Sodium/Low_Carb, n=1000). Patient_ID excluded (ID); Disease_Type excluded (perfect target proxy = leakage).

## foods_health_scores_allergens.csv — **ARCHIVED**
- rows: None, columns: None, size: None MB
- columns: 
- missing% (sample): None
- duplicate rows (sample of 5000): None
- decision: Moved to data/archive_unused/: no usable Indian-food selection (branded only). Excluded from the Indian-food pipeline even as allergy fallback.

## foods_dietary_restrictions.csv — **ARCHIVED**
- rows: None, columns: None, size: None MB
- columns: 
- missing% (sample): None
- duplicate rows (sample of 5000): None
- decision: Moved to data/archive_unused/: derived duplicate, contributes nothing.

## healthy_foods_database.csv — **USED (FILTERED)**
- rows: 9028, columns: 10, size: 0.85 MB
- columns: food_name, food_type, calories, protein_g, fat_g, carbs_g, fiber_g, sugar_g, sodium_mg, health_score
- missing% (sample): {'sugar_g': 17.1, 'fiber_g': 4.7, 'sodium_mg': 1.1, 'carbs_g': 0.2, 'food_name': 0.0, 'food_type': 0.0, 'calories': 0.0, 'protein_g': 0.0, 'fat_g': 0.0, 'health_score': 0.0}
- duplicate rows (sample of 5000): 255
- decision: SOURCE of derived Indian-food catalog (ml/indian_catalog.py, 100 rows). Raw file preserved; see reports/indian_audit.md.

## foods_allergens.csv — **ARCHIVED**
- rows: None, columns: None, size: None MB
- columns: 
- missing% (sample): None
- duplicate rows (sample of 5000): None
- decision: Moved to data/archive_unused/: conflicting allergen labels, no stable key.

## comprehensive_foods_usda.csv — **ARCHIVED**
- rows: None, columns: None, size: None MB
- columns: 
- missing% (sample): None
- duplicate rows (sample of 5000): None
- decision: Moved to data/archive_unused/: redundant 40k superset, no allergen data.

## indian_food.csv — **USED**
- rows: 255, columns: 9, size: 0.03 MB
- columns: name, ingredients, diet, prep_time, cook_time, flavor_profile, course, state, region
- missing% (sample): {'region': 0.4, 'name': 0.0, 'ingredients': 0.0, 'diet': 0.0, 'prep_time': 0.0, 'cook_time': 0.0, 'flavor_profile': 0.0, 'course': 0.0, 'state': 0.0}
- duplicate rows (sample of 5000): 0
- decision: Indian recipe catalog (255 recipes): diet/course/time filtering + deterministic ingredient matching (ml/recipes.py). Never merged into KNN.

## Diet target detail
- class counts: {'Balanced': 426, 'Low_Sodium': 316, 'Low_Carb': 258}
- missing%: {'Patient_ID': 0.0, 'Age': 0.0, 'Gender': 0.0, 'Weight_kg': 0.0, 'Height_cm': 0.0, 'BMI': 0.0, 'Disease_Type': 20.4, 'Severity': 0.0, 'Physical_Activity_Level': 0.0, 'Daily_Caloric_Intake': 0.0, 'Cholesterol_mg/dL': 0.0, 'Blood_Pressure_mmHg': 0.0, 'Glucose_mg/dL': 0.0, 'Dietary_Restrictions': 33.4, 'Allergies': 32.3, 'Preferred_Cuisine': 0.0, 'Weekly_Exercise_Hours': 0.0, 'Adherence_to_Diet_Plan': 0.0, 'Dietary_Nutrient_Imbalance_Score': 0.0, 'Diet_Recommendation': 0.0}
- duplicate rows (full): 0
- leakage note: `Disease_Type` perfectly predicts `Diet_Recommendation` (Diabetes→Low_Carb, Hypertension→Low_Sodium, Obesity/None→Balanced); excluded from features.

## Key integrity notes
- foods_dietary_restrictions vs primary: identical row order, 100% agreement on all shared columns, zero unique columns → derived copy, not merged.
- foods_allergens vs primary on (product_name, brands) keys: flags agree only 89–100% (dairy 88.9%, soy 90.7%, gluten 92.8%) → conflicting labels, not merged.
- program_summary titles == detailed titles (2,598 = 2,598, full overlap) → redundant.
- healthy_foods names ⊂ USDA names (7,571/7,572 overlap) and lack allergen data → excluded.
- Gym Members Exercise dataset: NOT present locally → workout RF classifier BLOCKED.

## Limitations
- Large workout file inspected via chunks/samples; full duplicate count not materialized.
- Allergen flags in primary catalog are complete (0% missing) but sourced from OpenFoodFacts-style data; unknown-ingredient products keep their explicit flag values — never treated as allergen-free when user allergy maps to an uncertain field (see recommender safety rule).