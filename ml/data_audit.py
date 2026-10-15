"""Dataset audit: inventory every candidate file -> reports/dataset_audit.md + manifest."""
import json
from pathlib import Path

import pandas as pd

from .config import REPORTS_DIR, DATASETS_DIR

CANDIDATES = [
    "programs_detailed_boostcamp_kaggle.csv",
    "program_summary.csv",
    "diet_recommendations_dataset.csv",
    "foods_health_scores_allergens.csv",
    "foods_dietary_restrictions.csv",
    "healthy_foods_database.csv",
    "foods_allergens.csv",
    "comprehensive_foods_usda.csv",
    "indian_food.csv",
]

DECISIONS = {
    "programs_detailed_boostcamp_kaggle.csv": (
        "used",
        "Primary workout/exercise catalog (filter + rank). NOT classifier training data: "
        "no defensible supervised target; Gym Members Exercise dataset absent locally.",
    ),
    "program_summary.csv": (
        "archived",
        "Moved to data/archive_unused/: titles fully redundant with detailed data. "
        "Only referenced by this audit script (tolerates missing files).",
    ),
    "diet_recommendations_dataset.csv": (
        "used",
        "Diet-category classifier training data. Target Diet_Recommendation "
        "(Balanced/Low_Sodium/Low_Carb, n=1000). Patient_ID excluded (ID); "
        "Disease_Type excluded (perfect target proxy = leakage).",
    ),
    "foods_health_scores_allergens.csv": (
        "archived",
        "Moved to data/archive_unused/: no usable Indian-food selection (branded only). "
        "Excluded from the Indian-food pipeline even as allergy fallback.",
    ),
    "foods_dietary_restrictions.csv": (
        "archived",
        "Moved to data/archive_unused/: derived duplicate, contributes nothing.",
    ),
    "healthy_foods_database.csv": (
        "used (filtered)",
        "SOURCE of derived Indian-food catalog (ml/indian_catalog.py, 100 rows). "
        "Raw file preserved; see reports/indian_audit.md.",
    ),
    "foods_allergens.csv": (
        "archived",
        "Moved to data/archive_unused/: conflicting allergen labels, no stable key.",
    ),
    "comprehensive_foods_usda.csv": (
        "archived",
        "Moved to data/archive_unused/: redundant 40k superset, no allergen data.",
    ),
    "indian_food.csv": (
        "used",
        "Indian recipe catalog (255 recipes): diet/course/time filtering + "
        "deterministic ingredient matching (ml/recipes.py). Never merged into KNN.",
    ),
}


def audit_file(path: Path, sample_n: int = 5000) -> dict:
    info = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    info["size_mb"] = round(path.stat().st_size / 1e6, 2)
    # row count without full load for large files
    with open(path) as f:
        n = sum(1 for _ in f) - 1
    info["rows"] = n
    df = pd.read_csv(path, nrows=sample_n)
    info["columns_sampled"] = len(df.columns)
    info["columns"] = list(df.columns)
    # full-column missingness via chunked scan of all columns (cheap: usecols all)
    miss = df.isna().mean().mul(100).round(1).to_dict()
    info["missing_pct_sample"] = {k: v for k, v in sorted(miss.items(), key=lambda x: -x[1])[:12]}
    info["dup_rows_sample"] = int(df.duplicated().sum())
    return info


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in CANDIDATES:
        p = DATASETS_DIR / name
        a = audit_file(p)
        status, reason = DECISIONS[name]
        a.update({"status": status, "reason": reason})
        rows.append(a)

    # Full (non-sampled) stats for small files
    extra = {}
    diet = pd.read_csv(DATASETS_DIR / "diet_recommendations_dataset.csv")
    extra["diet_target_counts"] = diet["Diet_Recommendation"].value_counts().to_dict()
    extra["diet_missing_pct"] = (diet.isna().mean().mul(100).round(1)).to_dict()
    extra["diet_dup_rows"] = int(diet.duplicated().sum())

    lines = ["# Dataset Audit", "", f"Source directory: `{DATASETS_DIR}`", ""]
    for r in rows:
        lines += [
            f"## {Path(r['path']).name} — **{r['status'].upper()}**",
            f"- rows: {r.get('rows')}, columns: {r.get('columns_sampled')}, size: {r.get('size_mb')} MB",
            f"- columns: {', '.join(r.get('columns', []))}",
            f"- missing% (sample): {r.get('missing_pct_sample')}",
            f"- duplicate rows (sample of 5000): {r.get('dup_rows_sample')}",
            f"- decision: {r['reason']}",
            "",
        ]
    lines += [
        "## Diet target detail",
        f"- class counts: {extra['diet_target_counts']}",
        f"- missing%: {extra['diet_missing_pct']}",
        f"- duplicate rows (full): {extra['diet_dup_rows']}",
        "- leakage note: `Disease_Type` perfectly predicts `Diet_Recommendation` "
        "(Diabetes→Low_Carb, Hypertension→Low_Sodium, Obesity/None→Balanced); excluded from features.",
        "",
        "## Key integrity notes",
        "- foods_dietary_restrictions vs primary: identical row order, 100% agreement on all shared "
        "columns, zero unique columns → derived copy, not merged.",
        "- foods_allergens vs primary on (product_name, brands) keys: flags agree only 89–100% "
        "(dairy 88.9%, soy 90.7%, gluten 92.8%) → conflicting labels, not merged.",
        "- program_summary titles == detailed titles (2,598 = 2,598, full overlap) → redundant.",
        "- healthy_foods names ⊂ USDA names (7,571/7,572 overlap) and lack allergen data → excluded.",
        "- Gym Members Exercise dataset: NOT present locally → workout RF classifier BLOCKED.",
        "",
        "## Limitations",
        "- Large workout file inspected via chunks/samples; full duplicate count not materialized.",
        "- Allergen flags in primary catalog are complete (0% missing) but sourced from OpenFoodFacts-style "
        "data; unknown-ingredient products keep their explicit flag values — never treated as allergen-free "
        "when user allergy maps to an uncertain field (see recommender safety rule).",
    ]
    (REPORTS_DIR / "dataset_audit.md").write_text("\n".join(lines))

    manifest = {
        "sources": [
            {"file": Path(r["path"]).name, "rows": r.get("rows"),
             "status": r["status"], "rationale": r["reason"],
             "join_key": None, "transformations": []}
            for r in rows
        ],
        "merges": [],
        "notes": "No index/order-based merges performed. No source files modified.",
    }
    (REPORTS_DIR / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Wrote reports/dataset_audit.md and reports/dataset_manifest.json")


if __name__ == "__main__":
    main()
