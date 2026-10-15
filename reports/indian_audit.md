# Indian-Food Catalog Audit (2026-10-15)

## Per-dataset evidence (keyword screen, then manual review of every hit)

| file | rows | raw keyword hits | defensible Indian records | verdict |
|---|---|---|---|---|
| `healthy_foods_database.csv` | 9,028 | 318 (3.5%), mostly US cottage cheese / buttermilk biscuits / Thai curry / French "poulet rôti" false positives | ~146 pre-cleaning → **100 active** | **SOURCE** of derived catalog |
| `comprehensive_foods_usda.csv` | 40,000 | 683 (1.7%), same false-positive pattern + a few genuine dishes (aloo paratha, samosas, pav bhaji, palak paneer) | redundant (healthy names ⊂ USDA) + 4.4× larger + no allergens | excluded |
| `foods_health_scores_allergens.csv` | 4,997 | 43 (0.9%): German basmati rice, lentil chips, French curries | no usable Indian selection (branded only) | excluded |
| `foods_dietary_restrictions.csv` | 4,997 | same 43 (derived copy) | nothing new | excluded |
| `foods_allergens.csv` | 3,332 | 17 (0.5%): tikka paste, Thai curry paste, French ready meals | condiments only, conflicting flags | excluded |

False friends explicitly NOT counted as Indian: cottage cheese (≠ paneer),
tofu "curd cheese" (≠ dahi), cape-gooseberry "poha" (≠ poha dish), buttermilk
biscuits, Thai/French curries, "roti" = French roast. Cottage cheese is never
presented as paneer.

## Derived catalog: `artifacts/indian_catalog.csv` (100 rows)
Built by `ml/indian_catalog.py` from `healthy_foods_database.csv` (source
untouched): dish-keyword class (10: chapati/roti, naan, besan, papad, chana dal,
dal bukhara, pindi chana, tandoori naan) + generic-staple head-noun class
(90: rice, lentils, chickpeas, wheat flour, semolina/rava, spices incl. turmeric
survivors, spinach, potatoes, tomatoes, carrots, cauliflower, okra, guavas,
almonds, cashews, peanuts). Names verbatim; branded items (5) flagged, not hidden.

## Unit finding (blocker documented, not silently fixed)
46 Indian-candidate rows carry values consistent with kilojoules, not kcal
(÷4.184 reproduces known truths: chapati 1240→296, lentils 1500→359, turmeric
1300→311, peanuts 2460→588, wheat flour 1520→363). They were EXCLUDED, not
converted: magnitude-inferred conversion is unsafe because low-calorie kJ rows
(<950) cannot be distinguished from true-kcal rows. Recovering them needs source
unit confirmation — recommended follow-up. Same risk may lurk in retained rows;
spot-checks pass but systematic verification needs source metadata.

## Coverage verdict
100 items (9 dishes + 91 staples) with complete macros (sugar 37% missing in
spice/flour rows — flagged per item). Sufficient for single-food top-K
suggestions; thin on finished dishes (no idli/dosa/biryani records exist
locally). Allergy + Indian combined requests return empty with a clear message:
the Indian catalog has no allergen data and there is NO fallback to branded
products. A dedicated Indian food/nutrition dataset with allergen info remains
the recommended next data acquisition.
