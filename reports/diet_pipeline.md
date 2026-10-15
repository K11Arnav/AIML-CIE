# Diet Pipeline: Actual Data Flow

## Step-by-step (what runs, in order)

1. **User inputs** → plain dict (age, weight, height, goal, allergies,
   restrictions, cuisine, top_k, ...). Only model/catalog-supported fields are used.
2. **Validation/normalization** (`FitnessRecommender.recommend_diet`,
   Express `validateDiet`): types/ranges checked (`top_k` 1–50); BMI derived
   from weight/height if missing (documented formula); goal lowercased and mapped
   via `GOAL_ALIASES`; unknown goals fall back to `balanced`. Invalid → 400, never defaults.
3. **Random Forest diet-category prediction** (`predict_diet_category`): the 17
   health-profile features above → `RandomForestClassifier` (200 trees) →
   category + class probabilities. The user goal does NOT enter this step, so a
   weight-loss goal can yield `Balanced`. Category is context output, not diagnosis.
4. **Nutritional target calculation**: the goal maps to an explicit per-100g
   reference vector (`GOAL_NUTRITION_TARGETS`, e.g. weight loss =
   80 kcal / 12 g protein / ...). No BMR or daily-calorie formulas are implemented —
   stated here explicitly. This vector is the KNN query, NOT a meal plan.
5. **Dietary/allergy filtering** (BEFORE ranking): catalog routing first —
   allergies requested ⇒ allergen-annotated catalog (verified flags), else general
   catalog. Then hard filters: allergy flags exclude matches; Low_Sodium/Low_Sugar
   thresholds exclude violators (missing values fail closed: treated as violating).
   Unsupported restrictions and unmapped allergies are reported in `filter_notes`;
   unverifiable allergies exclude everything with a warning. No merge, no fuzzy join.
6. **Feature scaling**: the 7 nutrition columns are median-imputed (training medians
   of the SAME catalog) and `StandardScaler`-transformed. Raw values are never used
   for Euclidean distance.
7. **KNN ranking**: `NearestNeighbors(k=min(top_k, eligible))` over eligible items
   only → top-K by scaled Euclidean distance. Distance = closeness, never proof
   of suitability or safety.
8. **Final recommendations**: JSON with category + explanation, goal profile,
   items (nutrition, `missing_nutrition`, `distance`, per-food `explanation`),
   `catalog_used`, `candidate_counts` (before/after), enforced/unsupported
   restrictions, scope (single-food suggestions — no meal slots, portions, or
   daily totals are computed), version.

## Meaning of scores
- `distance`: scaled Euclidean distance to the goal reference profile (smaller =
  nutritionally closer). Not a health or safety score.
- `probabilities`: RF class probabilities for this profile (uncertain: test
  accuracy 0.39). Not confidence in appropriateness.
- `health_score` (0–100, source-provided): displayed only; near-constant, not a ranking claim.
- Removed: the old 0–1 `similarity` score (implied suitability — misleading).

## Limitations preventing fully reliable recommendations
- Small diet training set (n=1000); RF barely beats a dummy baseline.
- General catalog has no allergen data; annotated catalog is packaged products.
- Missing nutrition cells (up to 30% fiber in annotated catalog) reduce ranking fidelity.
- No BMR/daily-needs math, no portions, no meal slots → single foods only.
