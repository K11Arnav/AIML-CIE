# Diet Recommendation Evaluation (2026-10-15)

Implementation-only audit: no new datasets, no model-target changes.
All profiles are labeled test fixtures.

## 1_weight_loss

- RF: **Balanced** {'Balanced': 0.4013, 'Low_Carb': 0.3172, 'Low_Sodium': 0.2815}
- goal profile: weight loss | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 100
- enforced: none
- notes: none
- unmet: None

  1. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, solids and liquids, low sodium — 88.0 kcal, P 4.92g, C 13.5g, F 1.95g, sugar 2.59, fiber 4.4, Na 0.132g (per 100 g) | dist 0.8731 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  2. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 0.8741 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  3. Lentils, mature seeds, cooked, boiled, without salt — 116.0 kcal, P 9.02g, C 20.1g, F 0.38g, sugar 1.8, fiber 7.9, Na 0.002g (per 100 g) | dist 1.0628 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Lentils', 'branded': False} | allergy=not-checked
  4. Peas and onions, frozen, unprepared — 70.0 kcal, P 3.98g, C 13.5g, F 0.32g, sugar None, fiber 3.5, Na 0.061g (per 100 g) | dist 1.1035 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Peas and onions', 'branded': False} | allergy=not-checked
  5. Potatoes, boiled, cooked in skin, skin, with salt — 78.0 kcal, P 2.86g, C 17.2g, F 0.1g, sugar None, fiber 3.3, Na 0.25g (per 100 g) | dist 1.1273 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Potatoes', 'branded': False} | allergy=not-checked
  6. Peas and carrots, frozen, unprepared — 53.0 kcal, P 3.4g, C 11.2g, F 0.47g, sugar None, fiber 3.4, Na 0.079g (per 100 g) | dist 1.1289 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked
  7. Cauliflower, green, cooked, with salt — 136.0 kcal, P 3.04g, C 6.28g, F 0.31g, sugar None, fiber 3.3, Na 0.259g (per 100 g) | dist 1.129 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked
  8. Spinach, frozen, chopped or leaf, cooked, boiled, drained, without salt — 143.0 kcal, P 4.01g, C 4.8g, F 0.87g, sugar 0.51, fiber 3.7, Na 0.097g (per 100 g) | dist 1.1787 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Spinach', 'branded': False} | allergy=not-checked
  9. Spinach, frozen, chopped or leaf, cooked, boiled, drained, with salt — 34.0 kcal, P 4.01g, C 4.8g, F 0.87g, sugar 0.51, fiber 3.7, Na 0.322g (per 100 g) | dist 1.1847 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Spinach', 'branded': False} | allergy=not-checked
  10. Peas and carrots, frozen, cooked, boiled, drained, without salt — 48.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.068g (per 100 g) | dist 1.2132 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked

## 2_muscle_gain

- RF: **Balanced** {'Balanced': 0.3831, 'Low_Carb': 0.2832, 'Low_Sodium': 0.3337}
- goal profile: muscle | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 100
- enforced: none
- notes: none
- unmet: None

  1. Spices, tarragon, dried — 295.0 kcal, P 22.8g, C 50.2g, F 7.24g, sugar None, fiber 7.4, Na 0.062g (per 100 g) | dist 1.8024 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Spices', 'branded': False} | allergy=not-checked
  2. Bread, naan, whole wheat, commercially prepared, refrigerated — 286.0 kcal, P 10.2g, C 46.2g, F 6.7g, sugar 3.4, fiber 4.8, Na 0.467g (per 100 g) | dist 1.9413 | missing=none | {'class': 'indian_dish', 'matched_term': 'naan', 'branded': False} | allergy=not-checked
  3. Spices, dill weed, dried — 253.0 kcal, P 20.0g, C 55.8g, F 4.36g, sugar None, fiber 13.6, Na 0.208g (per 100 g) | dist 2.0115 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Spices', 'branded': False} | allergy=not-checked
  4. 365 EVERYDAY VALUE, TANDOORI WHOLE WHEAT NAAN — 306.0 kcal, P 8.24g, C 48.2g, F 8.24g, sugar 4.71, fiber 5.9, Na 0.494g (per 100 g) | dist 2.1922 | missing=none | {'class': 'indian_dish', 'matched_term': 'tandoori whole', 'branded': True} | allergy=not-checked
  5. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 2.2728 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  6. Chickpeas, (garbanzo beans, bengal gram), dry — 372.0 kcal, P 21.3g, C 60.4g, F 6.27g, sugar None, fiber None, Na 0.009g (per 100 g) | dist 2.279 | missing=['sugars_100g', 'fiber_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas', 'branded': False} | allergy=not-checked
  7. Lentils, dry — 351.0 kcal, P 23.6g, C 62.2g, F 1.92g, sugar None, fiber None, Na 0.0g (per 100 g) | dist 2.304 | missing=['sugars_100g', 'fiber_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Lentils', 'branded': False} | allergy=not-checked
  8. Bread, chapati or roti, whole wheat, commercially prepared, frozen — 299.0 kcal, P 7.85g, C 46.1g, F 9.2g, sugar 2.93, fiber 9.7, Na 0.298g (per 100 g) | dist 2.3333 | missing=none | {'class': 'indian_dish', 'matched_term': 'chapati', 'branded': False} | allergy=not-checked
  9. Tomatoes, sun-dried, packed in oil, drained — 213.0 kcal, P 5.06g, C 23.3g, F 14.1g, sugar None, fiber 5.8, Na 0.266g (per 100 g) | dist 2.4107 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Tomatoes', 'branded': False} | allergy=not-checked
  10. Chickpea flour (besan) — 387.0 kcal, P 22.4g, C 57.8g, F 6.69g, sugar 10.8, fiber 10.8, Na 0.064g (per 100 g) | dist 2.4346 | missing=none | {'class': 'indian_dish', 'matched_term': 'besan', 'branded': False} | allergy=not-checked

## 3_vegetarian

- RF: **Balanced** {'Balanced': 0.4782, 'Low_Carb': 0.2829, 'Low_Sodium': 0.2389}
- goal profile: balanced | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 100
- enforced: none
- notes: [{'type': 'restriction_unsupported', 'value': 'Vegetarian'}]
- unmet: None

  1. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 0.6857 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  2. Peas and carrots, frozen, cooked, boiled, drained, with salt — 201.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.304g (per 100 g) | dist 0.9702 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked
  3. Tomatoes, sun-dried, packed in oil, drained — 213.0 kcal, P 5.06g, C 23.3g, F 14.1g, sugar None, fiber 5.8, Na 0.266g (per 100 g) | dist 1.0405 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Tomatoes', 'branded': False} | allergy=not-checked
  4. Potatoes, boiled, cooked in skin, skin, with salt — 78.0 kcal, P 2.86g, C 17.2g, F 0.1g, sugar None, fiber 3.3, Na 0.25g (per 100 g) | dist 1.0963 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Potatoes', 'branded': False} | allergy=not-checked
  5. Cauliflower, green, cooked, with salt — 136.0 kcal, P 3.04g, C 6.28g, F 0.31g, sugar None, fiber 3.3, Na 0.259g (per 100 g) | dist 1.1028 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked
  6. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, solids and liquids, low sodium — 88.0 kcal, P 4.92g, C 13.5g, F 1.95g, sugar 2.59, fiber 4.4, Na 0.132g (per 100 g) | dist 1.1563 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  7. Carrots, frozen, cooked, boiled, drained, with salt — 155.0 kcal, P 0.58g, C 7.73g, F 0.68g, sugar 4.08, fiber 3.3, Na 0.295g (per 100 g) | dist 1.2217 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Carrots', 'branded': False} | allergy=not-checked
  8. Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt — 164.0 kcal, P 8.86g, C 27.4g, F 2.59g, sugar 4.8, fiber 7.6, Na 0.007g (per 100 g) | dist 1.3674 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  9. Peas and onions, frozen, unprepared — 70.0 kcal, P 3.98g, C 13.5g, F 0.32g, sugar None, fiber 3.5, Na 0.061g (per 100 g) | dist 1.3942 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Peas and onions', 'branded': False} | allergy=not-checked
  10. Peas and carrots, frozen, cooked, boiled, drained, without salt — 48.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.068g (per 100 g) | dist 1.4254 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked

## 4_low_sugar

- RF: **Low_Carb** {'Balanced': 0.3534, 'Low_Carb': 0.3778, 'Low_Sodium': 0.2688}
- goal profile: weight loss | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 54
- enforced: [{'restriction': 'Low_Sugar', 'rule': 'sugars_100g <= 5.0 g', 'excluded_rows': 46}]
- notes: none
- unmet: None

  1. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, solids and liquids, low sodium — 88.0 kcal, P 4.92g, C 13.5g, F 1.95g, sugar 2.59, fiber 4.4, Na 0.132g (per 100 g) | dist 0.8731 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  2. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 0.8741 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  3. Lentils, mature seeds, cooked, boiled, without salt — 116.0 kcal, P 9.02g, C 20.1g, F 0.38g, sugar 1.8, fiber 7.9, Na 0.002g (per 100 g) | dist 1.0628 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Lentils', 'branded': False} | allergy=not-checked
  4. Spinach, frozen, chopped or leaf, cooked, boiled, drained, without salt — 143.0 kcal, P 4.01g, C 4.8g, F 0.87g, sugar 0.51, fiber 3.7, Na 0.097g (per 100 g) | dist 1.1787 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Spinach', 'branded': False} | allergy=not-checked
  5. Spinach, frozen, chopped or leaf, cooked, boiled, drained, with salt — 34.0 kcal, P 4.01g, C 4.8g, F 0.87g, sugar 0.51, fiber 3.7, Na 0.322g (per 100 g) | dist 1.1847 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Spinach', 'branded': False} | allergy=not-checked
  6. Peas and carrots, frozen, cooked, boiled, drained, without salt — 48.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.068g (per 100 g) | dist 1.2132 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked
  7. Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt — 164.0 kcal, P 8.86g, C 27.4g, F 2.59g, sugar 4.8, fiber 7.6, Na 0.007g (per 100 g) | dist 1.2705 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  8. Cauliflower, green, cooked, no salt added — 134.0 kcal, P 3.04g, C 6.28g, F 0.31g, sugar 3.12, fiber 3.3, Na 0.023g (per 100 g) | dist 1.3095 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked
  9. Cauliflower, green, raw — 31.0 kcal, P 2.95g, C 6.09g, F 0.3g, sugar 3.03, fiber 3.2, Na 0.023g (per 100 g) | dist 1.3148 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked
  10. Peas and carrots, frozen, cooked, boiled, drained, with salt — 201.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.304g (per 100 g) | dist 1.3283 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked

## 5_low_sodium

- RF: **Low_Carb** {'Balanced': 0.3848, 'Low_Carb': 0.4096, 'Low_Sodium': 0.2056}
- goal profile: balanced | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 91
- enforced: [{'restriction': 'Low_Sodium', 'rule': 'sodium_100g <= 0.4 g', 'excluded_rows': 9}]
- notes: none
- unmet: None

  1. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 0.6857 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  2. Peas and carrots, frozen, cooked, boiled, drained, with salt — 201.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.304g (per 100 g) | dist 0.9702 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked
  3. Tomatoes, sun-dried, packed in oil, drained — 213.0 kcal, P 5.06g, C 23.3g, F 14.1g, sugar None, fiber 5.8, Na 0.266g (per 100 g) | dist 1.0405 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Tomatoes', 'branded': False} | allergy=not-checked
  4. Potatoes, boiled, cooked in skin, skin, with salt — 78.0 kcal, P 2.86g, C 17.2g, F 0.1g, sugar None, fiber 3.3, Na 0.25g (per 100 g) | dist 1.0963 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Potatoes', 'branded': False} | allergy=not-checked
  5. Cauliflower, green, cooked, with salt — 136.0 kcal, P 3.04g, C 6.28g, F 0.31g, sugar None, fiber 3.3, Na 0.259g (per 100 g) | dist 1.1028 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked
  6. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, solids and liquids, low sodium — 88.0 kcal, P 4.92g, C 13.5g, F 1.95g, sugar 2.59, fiber 4.4, Na 0.132g (per 100 g) | dist 1.1563 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  7. Carrots, frozen, cooked, boiled, drained, with salt — 155.0 kcal, P 0.58g, C 7.73g, F 0.68g, sugar 4.08, fiber 3.3, Na 0.295g (per 100 g) | dist 1.2217 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Carrots', 'branded': False} | allergy=not-checked
  8. Chickpeas (garbanzo beans, bengal gram), mature seeds, cooked, boiled, without salt — 164.0 kcal, P 8.86g, C 27.4g, F 2.59g, sugar 4.8, fiber 7.6, Na 0.007g (per 100 g) | dist 1.3674 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  9. Peas and onions, frozen, unprepared — 70.0 kcal, P 3.98g, C 13.5g, F 0.32g, sugar None, fiber 3.5, Na 0.061g (per 100 g) | dist 1.3942 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Peas and onions', 'branded': False} | allergy=not-checked
  10. Peas and carrots, frozen, cooked, boiled, drained, without salt — 48.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.068g (per 100 g) | dist 1.4254 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked

## 6_peanut_allergy

- RF: **Balanced** {'Balanced': 0.4198, 'Low_Carb': 0.299, 'Low_Sodium': 0.2811}
- goal profile: weight loss | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 0
- enforced: none
- notes: [{'type': 'allergy_unverifiable', 'value': 'Peanuts', 'reason': 'Catalog contains no allergen information: compatibility cannot be established and is never assumed.'}]
- unmet: No foods satisfy all constraints; relax restrictions. Catalog contains no allergen information: compatibility cannot be established and is never assumed.


## 7_multi_constraint

- RF: **Low_Carb** {'Balanced': 0.3518, 'Low_Carb': 0.401, 'Low_Sodium': 0.2473}
- goal profile: balanced | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 0
- enforced: [{'restriction': 'Low_Sodium', 'rule': 'sodium_100g <= 0.4 g', 'excluded_rows': 0}]
- notes: [{'type': 'allergy_unverifiable', 'value': 'Peanuts', 'reason': 'Catalog contains no allergen information: compatibility cannot be established and is never assumed.'}, {'type': 'allergy_unverifiable', 'value': 'Sesame', 'reason': 'Catalog contains no allergen information: compatibility cannot be established and is never assumed.'}, {'type': 'allergy_unmapped', 'value': 'Sesame', 'reason': 'Label maps to no known catalog flag; compatibility cannot be established.'}]
- unmet: No foods satisfy all constraints; relax restrictions. Catalog contains no allergen information: compatibility cannot be established and is never assumed.


## 8a_minimal

- RF: **Low_Carb** {'Balanced': 0.3308, 'Low_Carb': 0.3876, 'Low_Sodium': 0.2816}
- goal profile: balanced | catalog: indian (indian_catalog.csv (derived from healthy_foods_database.csv))
- candidates: 100 -> 100
- enforced: none
- notes: none
- unmet: None

  1. Chickpeas (garbanzo beans, bengal gram), mature seeds, canned, drained solids — 139.0 kcal, P 7.05g, C 22.5g, F 2.77g, sugar 4.01, fiber 6.4, Na 0.246g (per 100 g) | dist 0.6857 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Chickpeas (garbanzo beans', 'branded': False} | allergy=not-checked
  2. Peas and carrots, frozen, cooked, boiled, drained, with salt — 201.0 kcal, P 3.09g, C 10.1g, F 0.42g, sugar 4.36, fiber 3.1, Na 0.304g (per 100 g) | dist 0.9702 | missing=none | {'class': 'staple_ingredient', 'matched_term': 'Peas and carrots', 'branded': False} | allergy=not-checked
  3. Tomatoes, sun-dried, packed in oil, drained — 213.0 kcal, P 5.06g, C 23.3g, F 14.1g, sugar None, fiber 5.8, Na 0.266g (per 100 g) | dist 1.0405 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Tomatoes', 'branded': False} | allergy=not-checked
  4. Potatoes, boiled, cooked in skin, skin, with salt — 78.0 kcal, P 2.86g, C 17.2g, F 0.1g, sugar None, fiber 3.3, Na 0.25g (per 100 g) | dist 1.0963 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Potatoes', 'branded': False} | allergy=not-checked
  5. Cauliflower, green, cooked, with salt — 136.0 kcal, P 3.04g, C 6.28g, F 0.31g, sugar None, fiber 3.3, Na 0.259g (per 100 g) | dist 1.1028 | missing=['sugars_100g'] | {'class': 'staple_ingredient', 'matched_term': 'Cauliflower', 'branded': False} | allergy=not-checked

## Invalid inputs
- 8b_top_k_999: rejected: top_k must be between 1 and 50
- 8c_top_k_0: rejected: top_k must be between 1 and 50
- 8d_non_dict: rejected: profile must be a dict

## RF sensitivity
- low-risk vitals -> Balanced, high-risk vitals -> Low_Sodium
- Checks the model is not constant; NOT a validity proof.

KNN features: ['energy_kcal', 'fat_100g', 'carbs_100g', 'sugars_100g', 'fiber_100g', 'proteins_100g', 'sodium_100g']

## Audit findings

### Confirmed bugs fixed this round
1. **Stale artifact path**: `ml/data_preparation.py:main()` still wrote the
   superseded `food_catalog.csv`; removed `ml/evaluate_catalog.py` (dual-catalog
   era), stale `food_catalog.csv`/`allergen_catalog.csv`, and stale `__pycache__`.
   Active artifacts are now exactly: `indian_catalog.csv`, `workout_catalog.csv`,
   `diet_model.joblib`, `knn.joblib`, `diet_meta.json`, `meta.json`.
2. **Doc discrepancies**: sugar-missing 32% → 37%, dish count 10 → 9, review date.

### Verified correct (with evidence)
- RF preprocessing parity: inference reuses the fitted training pipeline
  (median/mode imputation + one-hot-ignore); unknown categories and all-missing
  inputs handled (profile 8a returns results; invalid shapes rejected).
- No target leakage in features (`Patient_ID`, `Disease_Type` excluded; verified
  in `diet_features` + tests). Category spelling consistent end to end.
- Class imbalance is moderate (426/316/258); probabilities sum to 1.0.
- KNN uses StandardScaler fitted per catalog; median imputation; filters run
  before ranking (counts 100→54 low-sugar, 100→91 low-sodium, 100→0 allergy).
- Missing values display as `None`/"–" and populate `missing_nutrition`; sugar
  37% missing fails closed under Low_Sugar (46 rows excluded, 0 violations).
- kJ-suspect rows still excluded (energy>950 check: 0 present in artifact).
- Evidence classes/terms preserved into every response item.
- Vegetarian is reported `restriction_unsupported` with unfiltered results; the
  catalog incidentally contains zero animal-flesh records (verified), but this
  is NOT claimed as verification.
- Safety-empty (allergy) vs preference-empty messages differ and both render
  in backend + frontend (backend forwards full payload; UI shows warnings).

### Suspected issues / data limitations (documented, not disguised)
1. **Source-data anomaly (not fixable in code)**: frozen spinach "with salt"
   34 kcal vs "without salt" 143 kcal in the raw file — kept verbatim.
2. **Same-name conflicting rows**: "Nuts, cashew nuts, raw" exists twice with
   different nutrition (533 vs 553 kcal); both kept as separate items.
3. **Muscle top-1 is a spice** (tarragon, 295 kcal/22.8 g protein): numerically
   closest to the muscle reference, nutritionally odd per-100 g. Algorithmically
   correct; reflects a 100-item catalog with no portion logic. No arbitrary
   spice penalty added.
4. **Sugar axis is weak**: 37% missing → median-imputed distances.
5. **ML service alone accepts any numerics** (e.g. negative age); Express
   validates for the app path. Direct ML-service callers must validate.
6. Thin dish coverage (9 dishes; no idli/dosa/biryani records exist locally);
   `health_score` near-constant; RF test accuracy 0.39 ≈ dummy.

### Recommendations (priority order)
1. Acquire a dedicated Indian food/nutrition dataset WITH allergen info —
   unblocks allergy users and dish variety. (Data, not model work.)
2. Confirm source units for the 46 kJ-suspect rows; only then convert.
3. Portion/meal-slot logic only after (1); never on the current catalog.
