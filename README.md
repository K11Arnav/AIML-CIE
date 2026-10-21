# Personalized Workout & Diet Recommendations (ML + local demo app)

Informational recommendations only — not medical advice.

## Service responsibilities

- **React (`frontend/`, :5173)** — unified profile form + results views. Calls Express only, never Python directly.
- **Express (`backend/`, :5000)** — validates inputs, forwards to the Python ML service, maps errors. No ML logic.
- **Python ML service (`ml_service/`, :8000)** — thin FastAPI wrapper over `ml.recommender`; loads artifacts once, never retrains per request, never returns fake results.
- **No MongoDB:** recommendation data and model artifacts are local files; a database adds nothing for this demo.

## Quickstart

The app serves from committed `artifacts/` — no training needed to run:

```bash
pip install -r requirements.txt       # Python side (see teammate workflow below)
# terminal 1 — ML service (:8000)
.venv/bin/python -m uvicorn ml_service.app:app --port 8000
# terminal 2 — Express API (:5000)
cd backend && npm install && npm start
# terminal 3 — React app (:5173)
cd frontend && npm install && npm run dev
```

Full step-by-step: **“Run it locally (teammate workflow)”** below. Open
http://localhost:5173, submit the single unified profile form once.

To **retrain** (only when ML code or datasets change — reproducible, ~1 min):

```bash
.venv/bin/python -m ml.train          # rebuilds artifacts/ from datasets/ files only
```

## Where do website results come from?

**The `.pkl` question:** `artifacts/workout_model.joblib` / `diet_model.joblib`
ARE the serialized model files (joblib = Python pickle — same thing as a `.pkl`,
just a different extension). They load once per ML-service process; nothing
retrains at request time. Friends working on backend/frontend never touch them:
the website gets results over HTTP.

**It's not database scanning either.** There is no database. Per unified submit:

1. **Workout:** an RF classifier (`smartfit_workout_dataset.csv`, 8 profile
   features: Age, Gender, Weight_kg, Height_cm, Goal, Equipment, Experience,
   Injury) predicts a plan NAME from 24 classes. Probabilities are then
   equipment-constrained (the model can never pick a plan your equipment can't
   do), the primary plan plus up to 3 alternatives are returned, and the plan is
   laid out day-by-day from `datasets/exercises.json` via the documented mapping
   in `ml/plan_layout.py` (`PLAN_LAYOUTS`). Session minutes are a labeled
   heuristic — no per-plan durations exist in any dataset.
2. **Diet:** an RF regressor (`nutrition_dataset.csv`: Age, Gender, Height,
   Weight, Activity Level, Fitness Goal, Dietary Preference) predicts the daily
   calorie target + protein/carbs/fat. Meal suggestions are retrieved rows from
   the same dataset (never generated, not allergy-screened).
3. **Foods:** KNN ranks the `Anuvaad_INDB` per-100 g catalog against a goal
   reference nutrient profile. The Anuvaad catalog has NO allergen flags, so a
   requested allergy fails closed (all foods excluded + warning).

So: two small RF models + one KNN bundle + one deterministic layout table —
every number traceable to a dataset or a documented constant.

## Large files

No large files are needed anymore. All artifacts are compact (12 MB total) and
committed; training reads only the five datasets in `datasets/`. The old
boostcamp program files (282 MB) are retired and unnecessary.

## Unified profile (one form, one submit)

`ml/unified.py` is the canonical contract, validated in Express AND Python —
every field you send is consumed by a model:

| field | required | consumer |
|---|---|---|
| `age`, `height_cm`, `weight_kg`, `gender` | yes | BOTH models' features |
| `goal` | yes | workout RF feature + diet KNN goal profile |
| `equipment` | yes | workout RF feature + layout equipment constraint |
| `workout_duration_minutes` | yes | duration fit check (heuristic estimate) |
| `fitness_level` | optional | workout RF `Experience` feature |
| `activity_level` | optional | diet RF feature (4 levels, nutrition-dataset vocabulary) |
| `workout_days_per_week` | optional | weekly split (default 4, reported) |
| `injuries_or_limitations` | optional | workout RF `Injury` feature + safety warning |
| `dietary_preference` | optional | diet RF feature + meal retrieval |
| `allergies` | optional | food ranking fail-closed exclusion |

Goal values (exact training vocabulary): Weight Loss, Muscle Gain, General
Health, Strength, Endurance, Tone Up, Powerlifting, Flexibility, CrossFit,
Athletic Performance, Marathon Training. Equipment: Bodyweight Only, Yoga Mat,
Home Dumbbells, Full Home Gym, Gym Membership. Injury values: none, knee,
ankle, shoulder, back. Dropdowns are fed live from `GET /api/options/unified`
(values derived from the trained model — never guessed).

## API contract

- `GET /api/health` → `{status, ml_service}` (503 when ML is down)
- `GET /api/options/workout` → `{goals, fitness_levels, injuries, equipment[], available_minutes, days_per_week, top_n_choices, defaults, notes}`
- `GET /api/options/diet` → `{goals, dietary_preferences, activity_levels, allergies, defaults, notes}`
- `GET /api/options/unified` → `{goals, equipment[{value,label}], fitness_levels, activity_levels, injuries, dietary_preferences, genders, defaults, safety_note, ...}` — the form's source of truth
- `POST /api/recommendations/workout` → `{success, method, primary{plan, model_probability, style, sets, reps, workout_days_per_week, duration_check, layout{days[]}}, alternatives[] (each labeled "follow INSTEAD"), raw_probabilities, model_quality, constraints, unmet[], version}`
- `POST /api/recommendations/diet` → `{success, predicted{Daily Calorie Target, Protein, Carbohydrates, Fat}, input_features, model_quality_area, meals{suggestions{Breakfast/Lunch/Dinner/Snack Suggestion}, row_context, selection_basis}, items[] (KNN foods, per-100g), catalog_used, filter_notes, unmet[], version}`
- `POST /api/recommendations/unified` → `{success, profile{...bmi}, safety_note, diet_goal, daily_calorie_target_formula{...}, diet{...}, workout{...}, version}` — one profile in, both recommendations out
- Python service mirrors this at `GET /health`, `GET /options/workout|diet|unified`, `POST /recommendations/workout|diet|unified` (port 8000).
- Errors: `{success: false, error}` with 400 (invalid input), 503 (ML unavailable), 502 (ML error). No stack traces or paths leak to the browser.

## Tests

```bash
.venv/bin/python -m pytest tests/ -q   # 61 tests: model-driven workout/diet, layout, prep, unified, service routes
cd backend && npm test                 # 12 tests: validation, forwarding, options, timeout-safe errors
cd frontend && npm run build           # verifies the React app compiles
```

## Run it locally (teammate workflow)

Prereqs: Python 3.10+ (or 3.14), Node 18+.

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
.venv/bin/pip install -r requirements.txt     # Python: ML service + tests (incl. openpyxl for the xlsx)

# terminal 1 — ML service (:8000)
.venv/bin/python -m uvicorn ml_service.app:app --port 8000

# terminal 2 — Express API (:5000)
cd backend && npm install && npm start        # or: node src/server.js

# terminal 3 — React app (:5173)
cd frontend && npm install && npm run dev     # dev mode (hot reload)
# ...or serve the production build: npm run build, then
# node node_modules/.bin/vite preview --port 5173
```

Open http://localhost:5173, fill the single unified form once — model-predicted
macros, meal suggestions, ranked foods, and the day-by-day workout plan render
together. No training needed; the app serves from committed `artifacts/`. To
retrain anyway: `.venv/bin/python -m ml.train`.

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
  -d '{"age":30,"height_cm":165,"weight_kg":65,"gender":"Female","goal":"Muscle Gain","equipment":"home dumbbells","workout_duration_minutes":45,"activity_level":"moderately active","dietary_preference":"any","allergies":[]}'
```

Expect `recommendation_type: "unified"` with `diet.predicted`,
`diet.meals`, and `workout.primary.layout.days`.
A captured real response lives at `reports/sample_unified_response.json`.

Model experiments/plots live in the team Colab (`*.ipynb` is gitignored):
**<paste your Colab link here>**.

## Troubleshooting

- `Port 5000 is already in use` — a backend instance is already running. Reuse it
  (check `curl localhost:5000/api/health`) or stop it first. Same for 8000/5173.
- `npm start` must run inside `backend/` (own `package.json`); same for `frontend/`.
- `FileNotFoundError: Missing artifacts ... Run python -m ml.train` — artifacts
  folder emptied; retrain (datasets/ must be present).

## ML package (importable, no servers needed)

```python
from ml.recommender import FitnessRecommender

rec = FitnessRecommender.load("artifacts/")  # loads once; no retraining per request

workout = rec.recommend_workout({
    "age": 28, "gender": "Male", "weight_kg": 80, "height_cm": 180,
    "goal": "Muscle Gain",             # exact smartfit goal value
    "equipment": "Full Home Gym",      # exact smartfit equipment value
    "experience_level": "Beginner",
    "injury": "None",                  # None/Knee/Ankle/Shoulder/Back
    "available_minutes": 45,
    "workout_days_per_week": 4,
    "top_n": 3,                        # 1 primary + up to 3 alternatives
})

diet = rec.recommend_diet({
    "age": 25, "gender": "Male", "height_cm": 175, "weight_kg": 70,
    "activity_level": "Moderately Active", # exact nutrition-dataset value
    "fitness_goal": "Weight Loss",
    "dietary_preference": "Omnivore",  # Omnivore/Vegetarian/Vegan
    "goal": "weight loss",             # KNN reference profile key
    "allergies": [],                   # any allergy -> fail-closed empty + warning
    "top_k": 5,
})
```

All outputs are JSON-serializable. Invalid inputs raise `ValueError` with clear
messages; missing artifacts raise `FileNotFoundError` telling you to retrain.

## Model quality (honest numbers)

| Model | Test metric | Baseline | Source |
|---|---|---|---|
| Workout RF (24 plan classes, 9,476 rows) | accuracy **1.0** / f1_macro 1.0 | most-frequent dummy 0.147 | `smartfit_workout_dataset.csv` |
| Diet RF (4 macro targets, 498 rows) | MAE 101 kcal / R² 0.91 | mean baseline 371 kcal | `nutrition_dataset.csv` |
| Diet RF protein/carbs/fat | MAE 12.8 / 22.5 / 6.4 g, R² 0.78/0.73/0.70 | — | same |

The smartfit dataset encodes a deterministic rule (plan = f(features)); the RF
recovers it exactly. This is reported as observed — treat live predictions as an
implementation of the dataset's rule, not a validated coach. All numbers
regenerate with `python -m ml.train` into `reports/metrics/*.json` and
`reports/model_report.md`.

## Datasets (all training comes from these five files — nothing else exists)

- `smartfit_workout_dataset.csv` (10,000 → 9,476 after exact-dupe drop; Injury
  NaN → `None` 42.7%; Experience NaN → `Unspecified` 20 rows): profile → plan.
  Workout classifier training data.
- `nutrition_dataset.csv` (500 → 498 after dropping 2 header-row junk rows; 3
  "Weight Maintenance" folded into "Maintenance"): profile → calorie target +
  macros + meal suggestion strings. Diet regressor training data + meal source.
- `Anuvaad_INDB_2024.11.xlsx` (1,014 Indian foods × 82 columns, per-100 g):
  KNN food-ranking catalog. No allergen flags → allergies fail closed.
- `exercises.json` (1,324 exercises: equipment/body_part/instructions): plan →
  exercise layout library (`ml/plan_layout.py`).
- `program_summary.csv` — **retired**, not part of any pipeline (old boostcamp
  program scrapes kept only as raw data).

Retired references that no longer exist anywhere (code, configs, or reports):
`programs_detailed_boostcamp_kaggle.csv`, `diet_recommendations_dataset.csv`,
`healthy_foods_database.csv`, `indian_food.csv`, `foods_*` catalogs.

## Layout

`ml/` — `config.py`, `data_preparation.py`, `plan_layout.py`, `train.py`,
`evaluation.py`, `recommender.py`, `unified.py`, `options.py`, `calories.py`;
`ml_service/` — FastAPI wrapper; `backend/` — Express proxy + validation;
`frontend/` — React single-form app; `tests/` — 61 fixture-based pytest tests;
`artifacts/` — committed models + catalogs (rebuildable, reproducible);
`reports/` — `model_report.md`, `sample_unified_response.json`, `metrics/`.
