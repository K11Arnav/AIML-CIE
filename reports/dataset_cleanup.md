# Dataset Cleanup (2026-10-15)

Dependency audit: every active code path (`ml/*.py` runtime + `train.py`,
`tests/`, `backend/`, `frontend/`) was searched for dataset references.
Reports/README references are documentation, not dependencies.

| dataset | role | referenced by active code | decision | reason |
|---|---|---|---|---|
| `diet_recommendations_dataset.csv` | RF training | `ml/config.py`, `train.py` | **keep** | required to train/evaluate the Random Forest |
| `healthy_foods_database.csv` | Indian catalog source | `ml/config.py`, `train.py`, `tests/test_indian_catalog.py` | **keep** | source of derived `indian_catalog.csv` |
| `indian_food.csv` | recipe catalog | `ml/recipes.py`, `train.py`, `ml/options.py` | **keep** | recipe recommendations |
| `programs_detailed_boostcamp_kaggle.csv` | workout catalog | `ml/config.py`, `train.py` | **keep** | workout recommendations (282 MB, stays) |
| `comprehensive_foods_usda.csv` | — | only `ml/data_audit.py`, docs | **archived** | redundant superset, 16 MB |
| `foods_health_scores_allergens.csv` | — | only `ml/data_audit.py`, docs | **archived** | no usable Indian selection |
| `foods_dietary_restrictions.csv` | — | only `ml/data_audit.py`, docs | **archived** | derived duplicate |
| `foods_allergens.csv` | — | only `ml/data_audit.py`, docs | **archived** | conflicting labels, no key |
| `program_summary.csv` | — | only `ml/data_audit.py`, docs | **archived** | redundant titles |

Archived files were MOVED (not copied) to `data/archive_unused/` — reversible
by moving them back. `ml/data_audit.py` tolerates missing files (records them
as not-found) and its decisions table now marks them `archived`.
Derived artifacts superseded: `artifacts/food_catalog.csv`,
`artifacts/allergen_catalog.csv` deleted (replaced by `indian_catalog.csv`);
dead script `ml/evaluate_catalog.py` removed (replaced by
`ml/evaluate_diet_system.py`). No remaining unused files: every file under
`ml/`, `tests/`, `backend/`, `frontend/`, `ml_service/` is imported, tested,
or served. Raw source files were never edited.
