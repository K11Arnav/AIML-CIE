# Indian Recipe Catalog Audit (`indian_food.csv` → `recipe_catalog.csv`)

Source preserved at `datasets/indian_food.csv` (255 × 9, 0 exact duplicates).
Derived artifact: `artifacts/recipe_catalog.csv` (cleaned copy, names/ingredients verbatim).

## Cleaning decisions (nothing invented)
- `prep_time`/`cook_time` negative (-1 sentinel): 30 / 28 → unknown (null).
  Unknown times never fit a user time limit (excluded when a limit is set).
- `state`/`region`/`flavor_profile` of `-1`/empty → null: 24 / 14 / 29.
- `diet`/`course` lowercased only: `vegetarian` 226 / `non vegetarian` 29;
  courses: main course 129, dessert 85, snack 39, starter 2.
- No rows removed, no values filled, no merges.

## Course distribution note
Desserts (85) are never shown as mains: the default course filter is
`main course`; desserts appear only when the user explicitly selects dessert.

## Data honesty notes
- The recipe file's own "cottage cheese" means paneer (dairy); mapped to dairy,
  name kept verbatim.
- "Drumsticks" in sambar context is ambiguous (moringa vs chicken leg) → left
  `unknown`, forcing ingredient review when allergies matter — never guessed.
- "Meat curry powder" is a spice mix, not meat.
- 2 vegetarian-labeled recipes contain meat/egg tokens (Sambar "drumsticks"
  ambiguous; Bebinca egg yolks): ingredient evidence wins over the label for
  vegetarian-strict filtering, and the conflict is reported.
- Ingredient text cannot establish cross-contamination safety; the UI states
  that allergy safety cannot be certified.
