# Personalized Workout & Diet Recommendations (ML + local demo app)

Informational recommendations only — not medical advice.

## Service responsibilities

- **React (`frontend/`, :5173)** — workout/diet forms + results views. Calls Express only, never Python directly.
- **Express (`backend/`, :5000)** — validates inputs, forwards to the Python ML service, maps errors. No ML logic.
- **Python ML service (`ml_service/`, :8000)** — thin FastAPI wrapper over `ml.recommender`; loads artifacts once, never retrains per request, never returns fake results.
- **No MongoDB:** recommendation data and model artifacts are local files; a database adds nothing for this demo.

## Quickstart

No training or datasets needed — the app serves from committed `artifacts/`.
Full step-by-step for teammates (install, three terminals, ports, health checks,
smoke test): see **“Run it locally (teammate workflow)”** below. Then open
http://localhost:5173 and submit the single unified profile form once.

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

## Unified profile (one form, one submit)

`ml/unified.py` is the canonical contract. Required: `age` (5–100 yrs), `height_cm`
(50–250), `weight_kg` (20–300), `gender` (Female/Male), `goal` (weight loss /
muscle gain / general fitness), `equipment` (bodyweight / dumbbells / full gym →
exact catalog values At Home / Dumbbell Only / Full Gym), `workout_duration_minutes`.
Optional: `fitness_level`, `activity_level`, `workout_days_per_week` (1–7),
`injuries_or_limitations` ("none" or free text), `dietary_preference`
(any/vegetarian/non vegetarian), `allergies`. Validated in Express AND Python;
every field has a documented consumer in `ml/unified.py`. Goal maps: diet
weight loss→`weight loss`, muscle gain→`muscle`, general fitness→`balanced`;
workout weight loss→`Bodyweight Fitness`, muscle gain→`Bodybuilding`, general
fitness→no goal filter. Injuries get a conservative warning (catalog has no
injury-safety data — never claimed safe). Legacy per-recommender routes still exist.

## Diet results (food-focused, no legacy output)

The diet section shows only: (A) a **daily calorie target** (`daily_calorie_target`
in the unified response) — a Mifflin-St Jeor maintenance estimate
(`ml/calories.py`: BMR × activity factor 1.2/1.55/1.725; optional activity
defaults to documented moderate; no goal deficit applied; labeled calculation,
never a measured fact; unavailable → explicit fallback message, never invented;
no macro targets shown — none are reliably available); (B) **Foods you can eat**
— food cards (kcal per 100 g dataset basis, protein/carbs/fat/fibre, explicit
“ingredients not listed”, no dietary-category inference, goal-suitability line)
plus compatible recipe cards (real ingredient list, dataset diet label,
“nutrition unavailable”); (C) one exact empty message when nothing is eligible;
(D) at most one allergy warning (fail-closed: unverifiable foods never labeled
safe). Removed from the UI: predicted-category banner, goal-profile line,
nutrient-closeness heading, counters/pipeline text, needs-review/eligible-groups
sections, all prep/cook times (workout duration unchanged). `prep_time`/
`cook_time` remain in the response payload (contract + `max_time_min` filtering;
pinned by `tests/test_recipes.py`) but are never rendered.

## API contract

- `GET /api/health` → `{status, ml_service}` (503 when ML is down)
- `GET /api/options/workout` → `{goals, experience_levels, equipment, available_minutes, top_n_choices, defaults, notes}` — values read from the real catalog, the form's source of truth
- `GET /api/options/diet` → `{goals, cuisines, allergies, dietary_restrictions, ..., defaults, notes}`
- `POST /api/recommendations/workout` → `{success, recommendation_type, method, usage, primary{program, equipment, level, goal, duration_check{requested, estimated, fits, note}, exercises[]}, alternatives[] (each labeled "follow INSTEAD"), n_candidates, top_n, unmet[], version}`. `top_n` (1–4, default 1) = total alternative programs = 1 primary plan to follow + up to 3 alternatives to choose from instead. Equipment is an exact-match hard filter (incompatible programs excluded + reported, never remapped)
- `POST /api/recommendations/unified` → `{success, recommendation_type: "unified", profile{...bmi}, safety_note, diet_goal, workout_goal_filter, daily_calorie_target{kcal_per_day, method, source: "calculation", activity_level_used, activity_assumed, disclaimer}, diet{...}, workout{...}, version}` — one profile in, both recommendations out (same schema as the per-recommender payloads, nested).
- `GET /api/options/unified` → `{goals, equipment[{value,label}], fitness_levels, activity_levels, dietary_preferences, safety_note, workout, diet}` — the unified form's source of truth.
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
python -m pytest tests/ -q        # 86 tests: 80 pass. 6 pre-existing failures
                                  # need legacy training CSVs absent from
                                  # datasets/ — they fail identically
                                  # without these changes (FileNotFoundError).
cd backend && npm test            # 12 tests: validation, forwarding, options, unified, timeout-safe errors
cd frontend && npm run build      # verifies the React app compiles
```

## Run it locally (teammate workflow)

Prereqs: Python 3.10+ with the repo `.venv` (or your own venv), Node 18+.

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt               # Python: ML service + tests

# terminal 1 — ML service (:8000)
.venv/bin/python -m uvicorn ml_service.app:app --port 8000

# terminal 2 — Express API (:5000)
cd backend && npm install && npm start         # or: node src/server.js

# terminal 3 — React app (:5173)
cd frontend && npm install && npm run dev      # dev mode (hot reload)
# ...or serve the production build: npm run build, then
# node node_modules/.bin/vite preview --port 5173
```

Open http://localhost:5173, fill the single unified form once — diet
(daily calorie target + food/recipe cards) and workout plan render together.
No training or datasets needed: the app serves from committed `artifacts/`.

| Service | Port | Health check |
|---|---|---|
| ML (FastAPI) | 8000 | `curl localhost:8000/health` → `{"status":"ok"}` |
| API (Express) | 5000 | `curl localhost:5000/api/health` → `{"status":"ok","ml_service":{...}}` |
| UI (React) | 5173 | open in browser |

Optional overrides: copy `backend/.env.example` → `backend/.env`
(`ML_SERVICE_URL`, `FRONTEND_ORIGIN`, `PORT`), `frontend/.env.example` →
`frontend/.env` (`VITE_API_BASE`). Never commit real `.env` files (gitignored).

Quick unified smoke test (backend + ML running):

```bash
curl -X POST localhost:5000/api/recommendations/unified \
  -H 'Content-Type: application/json' \
  -d '{"age":30,"height_cm":165,"weight_kg":65,"gender":"Female","goal":"weight loss","equipment":"bodyweight","workout_duration_minutes":30,"fitness_level":"beginner","allergies":[]}'
```

Expect `recommendation_type: "unified"` with `daily_calorie_target`,
`diet.items`, and `workout.primary`.

Model experiments (diet Ridge regression, workout RF classifier, plots) live in
the team Colab (notebooks were removed from this repo; `*.ipynb` is gitignored):
**<paste your Colab link here>**.

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
- unified (run 2026-10-15, Express :5001 → ML :8001): one profile
  `{age 30, 165cm, 65kg, Female, weight loss, bodyweight, 30min}` →
  5 diet items + workout `Curvy Body Saves The Day` + BMI 23.9 ✅;
  invalid `age: -1` → clean 400 ✅

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

## Datasets (actually present → role; absent → honest status)

Present in `datasets/` (reference data for experiments; the app itself serves from
committed `artifacts/` and needs none of these at runtime):

- `nutrition_dataset.csv` (500 rows → 498 after dropping 2 header-duplicate junk rows;
  zero missing): profile + macro prescriptions. Role: diet-calorie regression
  (`Daily Calorie Target`) + rule-based meal shortlists (goal + preference filter,
  calorie-gap rank). Has NO ingredient/allergen columns — allergy safety unestablishable.
- `Anuvaad_INDB_2024.11.xlsx` (Sheet1, 1014 Indian foods × 82 cols, no dupes/negatives):
  per-100 g nutrients. Role: Indian-food candidate catalog for content-based ranking.
- `smartfit_workout_dataset.csv` (10,000 rows → 9476 after exact-dupe drop; 42.7%
  missing `Injury` → explicit "None"; 20 missing `Experience`): profile → plan.
  Role: workout classifier demo. **Proven synthetic**: plan is a deterministic function
  of (Goal, Equipment, Experience, Injury); RF accuracy 1.0000 = rule recovery.
- `program_summary.csv` (2598 programs metadata): role: audit equipment/duration/goal
  coverage for the app's hard filters (no outcome label → no classifier).
- `exercises.json` (1324 exercises: equipment/body_part/target/instructions-en):
  role: exercise catalogue reference (no sets/reps schedules).

Absent in this checkout (used by committed `artifacts/` + legacy tests, NOT claimed):
`diet_recommendations_dataset.csv`, `healthy_foods_database.csv`, `indian_food.csv`
(deleted from workdir; in git history), `programs_detailed_boostcamp_kaggle.csv`
(gitignored, large). Consequence: `python -m ml.train` and 6 legacy tests fail here
with clear FileNotFoundError; diet/workout/recipe serving works from `artifacts/`.

## Layout

`ml/` — `config.py`, `data_audit.py`, `data_preparation.py`, `train.py`,
`evaluation.py`, `recommender.py`; `tests/` — 21 fixture-based tests;
`reports/` — audit, manifest, evaluation report, metrics JSON.
