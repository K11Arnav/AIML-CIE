# Personalized Workout & Diet Recommendations (ML + local demo app)

Informational recommendations only — not medical advice.

## Service responsibilities

- **React (`frontend/`, :5173)** — workout/diet forms + results views. Calls Express only, never Python directly.
- **Express (`backend/`, :5000)** — validates inputs, forwards to the Python ML service, maps errors. No ML logic.
- **Python ML service (`ml_service/`, :8000)** — thin FastAPI wrapper over `ml.recommender`; loads artifacts once, never retrains per request, never returns fake results.
- **No MongoDB:** recommendation data and model artifacts are local files; a database adds nothing for this demo.

## Quickstart for collaborators (no training needed)

Small artifacts + small datasets are committed, so a fresh clone runs immediately:

```bash
git clone <repo-url> && cd <repo>
pip install -r requirements.txt               # Python: model training + ML service

uvicorn ml_service.app:app --port 8000        # terminal 1: ML service (:8000)

cd backend && npm install && npm start         # terminal 2: Express (:5000)

cd frontend && npm install && npm run dev      # terminal 3: React (:5173)
```

Then open http://localhost:5173, submit one workout and one diet form.
Copy `.env.example` to `.env` in `backend/`/`frontend/` to change ports/URLs
(`ML_SERVICE_URL`, `FRONTEND_ORIGIN`, `VITE_API_BASE`).

Only re-run training when ML code/datasets change:

```bash
python -m ml.train          # rebuilds artifacts/ (needs datasets/ files)
python -m ml.data_audit     # regenerates the dataset inventory report
```

## Where do website results come from?

**The `.pkl` question:** `artifacts/diet_model.joblib` IS the serialized model
file (joblib uses Python pickle under the hood — same thing as a `.pkl`, just a
different extension). It loads once per ML-service process; nothing retrains at
request time. Friends working on backend/frontend never touch it: the website
gets results over HTTP (`React → Express :5000 → FastAPI :8000 → Python`).

**It's not database scanning either.** There is no database. Per diet request:
1. Random Forest (from the `.joblib`) predicts a diet *category* from the health
   profile — that model never sees or scores individual foods.
2. Foods come from `artifacts/indian_catalog.csv` (100 Indian foods): hard
   restriction/allergy filters first, then KNN ranks the survivors by nutrient
   closeness to the goal profile.
3. Recipes come from `artifacts/recipe_catalog.csv` (255 Indian recipes) via
   deterministic rule filtering + coverage ranking — no ML involved.
So: one small model file + two small CSVs + explicit rules. Retrain only to
change the model or catalogs.

## Large files (not in git)

GitHub caps files at 100 MB. Excluded via `.gitignore`, clone stays light:
- `artifacts/workout_catalog.csv` (120 MB) + `datasets/programs_detailed_boostcamp_kaggle.csv`
  (282 MB): workout recommendations need these locally. Diet/food/recipe
  endpoints work without them (workout calls return a clear 503 instead).
  To enable workouts, drop the programs CSV into `datasets/` and run
  `python -m ml.train`.
- `data/archive_unused/` (19 MB): removed-from-pipeline datasets, kept locally only.

## API contract

- `GET /api/health` → `{status, ml_service}` (503 when ML is down)
- `GET /api/options/workout` → `{goals, experience_levels, equipment, available_minutes, top_n_choices, defaults, notes}` — values read from the real catalog, the form's source of truth
- `GET /api/options/diet` → `{goals, cuisines, allergies, dietary_restrictions, ..., defaults, notes}`
- `POST /api/recommendations/workout` → `{success, recommendation_type, method, usage, primary{program, equipment, level, goal, duration_check{requested, estimated, fits, note}, exercises[]}, alternatives[] (each labeled "follow INSTEAD"), n_candidates, top_n, unmet[], version}`. `top_n` (1–4, default 1) = total alternative programs = 1 primary plan to follow + up to 3 alternatives to choose from instead. Equipment is an exact-match hard filter (incompatible programs excluded + reported, never remapped)
- `POST /api/recommendations/diet` → `{success, recommendation_type, diet_category{...}, goal_profile, items[] (KNN foods), eligible_foods{group[]}, excluded_foods[], recipes[] (compatible, ranked), recipes_needs_review[], filtering_summary{recipes_before_filtering, recipes_after_diet_filter, recipes_after_ingredient_checks, recipes_needs_review, recipes_excluded_by_time, recipes_after_time_filter}, warnings[], ...}`
- Diet inputs add: `course` (any/main course/dessert/snack/starter; default main course), `diet_preference` (any/vegetarian/non vegetarian), `max_time_min` (positive number; unknown times never fit).
- Python service mirrors this at `GET /health`, `GET /options/workout|diet`, `POST /recommendations/workout|diet` (port 8000).
- Errors: `{success: false, error}` with 400 (invalid input), 503 (ML unavailable), 502 (ML error). No stack traces or paths leak to the browser.

## Flow
Profile → RF category (informational) → eligible Indian foods (rules + KNN rank) → recipes (diet/course → ingredient checks → time → deterministic rank by coverage/time/name). Recipe matches use a reviewed whole-token taxonomy (`ml/recipe_taxonomy.py`, 99.7% occurrence coverage); allergy conflicts excluded on positive evidence, unknown tokens force review, safety never certified. RF and KNN architecture unchanged; no ML on recipes.

Dropdown defaults: Goal `Bodybuilding`, level `Beginner`, 60 min, `top_n` 3.
Equipment note: `Dumbbells`/`Barbell` do not exist in the workout catalog (only
`Full Gym / Garage Gym / At Home / Dumbbell Only`), so the valid default is
`Dumbbell Only`; unsupported values are reported in `unmet`, never remapped.

## Tests

```bash
python -m pytest tests/ -q        # 63 tests: ML package + ML service + options + Indian catalog + recipes
cd backend && npm test            # 9 tests: validation, forwarding, options, timeout-safe errors
cd frontend && npm run build      # verifies the React app compiles
```

## Troubleshooting

- `Port 5000 is already in use` — a backend instance is already running. Reuse it
  (check `curl localhost:5000/api/health`) or stop it before `npm start`. Same for
  port 8000 (ML service) and 5173 (frontend).
- `npm start` must run inside `backend/` (it has its own `package.json`); same for
  `frontend/` commands.

End-to-end smoke tests (run 2026-10-14, all via Express → real artifacts):
- workout `Bodybuilding/Beginner/Full Gym/60min` → `Upper Body Builder with Leg Boost` + exercises ✅
- diet `Weight Loss + Peanuts allergy` → `Balanced` + 3 peanut-free foods with similarities ✅
- invalid `top_k: 999` → clean 400, no leak ✅

## ML package (importable, no servers needed)

```python
from ml.recommender import FitnessRecommender

rec = FitnessRecommender.load("artifacts/")  # loads once; no retraining per request

workout = rec.recommend_workout({
    "goal": "Bodybuilding",            # substring-matched against program goals
    "experience_level": "Beginner",    # substring-matched against levels
    "equipment": ["Full Gym"],         # hard constraint (gracefully ignored if unmatched)
    "available_minutes": 60,           # keeps programs with time <= avail + 15
    "top_n": 5,
})

diet = rec.recommend_diet({
    "Age": 25, "Gender": "Male", "Weight_kg": 70, "Height_cm": 175,
    "Severity": "Moderate", "Physical_Activity_Level": "Moderate",
    "Daily_Caloric_Intake": 2500, "Cholesterol_mg/dL": 190,
    "Blood_Pressure_mmHg": 120, "Glucose_mg/dL": 100,
    "Weekly_Exercise_Hours": 4, "Adherence_to_Diet_Plan": 80,
    "Dietary_Nutrient_Imbalance_Score": 2.0,
    "Dietary_Restrictions": "None", "Allergies": "None",
    "Preferred_Cuisine": "Indian",
    "goal": "Weight Loss",             # maps to an explicit per-100g KNN target vector
    "allergies": ["Peanuts"],          # hard filter BEFORE ranking
    "dietary_restrictions": ["Low_Sodium"],
    "top_k": 10,
})
```

All outputs are JSON-serializable. `rec.predict_diet_category(profile)` returns just the
classifier output. Invalid inputs raise `ValueError`/`FileNotFoundError` with clear messages.

## What was built (and blocked)

| Component | Status |
|---|---|
| Diet RandomForest (`Diet_Recommendation`, n=1000) | Trained. Excludes `Patient_ID` (ID) and `Disease_Type` (perfect target proxy). Test acc **0.39** vs dummy **0.38** — weak signal, reported honestly. Predicts the *category only*, from the health profile (goal is not a feature); runtime explanation includes probabilities, feature importance, target distribution |
| KNN food ranking (scaled per-100g nutrition, restriction filters first) | Dual catalogs: general foods default (8,178 rows); allergen-annotated fallback (4,959 validated flags) when allergies requested. Roles separated: RF predicts category, KNN ranks foods. Output is single-food suggestions, not meal plans; per-food explanations cite source, allergy status, missing fields |
| Allergy safety | Verified flags exclude matches when available; unmapped/unverifiable allergies return empty + explicit warning. Safety is never assumed |

Developer docs: `reports/dataset_transparency.md` (exact datasets/columns/rows),
`reports/diet_pipeline.md` (step-by-step data flow, score meanings, limits).
The diet results page has a "How these recommendations were generated" panel
driven entirely by runtime response metadata.
| Workout catalog filter + rank (2,598 programs / 604k exercise rows) | Implemented |
| Workout RandomForest classifier | **BLOCKED** — Gym Members dataset absent; program titles are catalog entries, not outcome labels. No labels fabricated |

## Datasets

- **Used:** `diet_recommendations_dataset.csv`, `healthy_foods_database.csv`
  (filtered to a 100-row Indian-food catalog; sodium mg→g),
  `programs_detailed_boostcamp_kaggle.csv`
- **Excluded with reasons:** `foods_health_scores_allergens.csv` (no usable
  Indian selection — branded only), `comprehensive_foods_usda.csv` (redundant
  superset), `foods_dietary_restrictions.csv` (derived copy, 0 new columns),
  `foods_allergens.csv` (conflicting flags, no stable key),
  `program_summary.csv` (titles fully redundant)
- See `reports/dataset_audit.md` and `reports/dataset_manifest.json`. Raw files untouched.

## Layout

`ml/` — `config.py`, `data_audit.py`, `data_preparation.py`, `train.py`,
`evaluation.py`, `recommender.py`; `tests/` — 21 fixture-based tests;
`reports/` — audit, manifest, evaluation report, metrics JSON.
