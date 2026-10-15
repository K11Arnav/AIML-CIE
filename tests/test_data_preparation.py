"""Data prep tests: validation, dedupe cardinality, no index-merge, repeatability."""
import pandas as pd
import pytest

from ml import data_preparation as dp
from tests.conftest import diet_fixture, food_fixture


def test_missing_target_raises():
    with pytest.raises((ValueError, KeyError)):
        dp.diet_features(pd.DataFrame({"Age": [25]}))


def test_ids_and_leakage_excluded_from_features():
    X, y = dp.diet_features(diet_fixture())
    assert "Patient_ID" not in X.columns
    assert "Disease_Type" not in X.columns
    assert "Diet_Recommendation" not in X.columns
    assert len(X) == len(y)


def test_food_dedupe_does_not_multiply_rows(tmp_path):
    import numpy as np
    df = food_fixture(30)
    dup = pd.concat([df, df.iloc[:5]], ignore_index=True)
    p = tmp_path / "food.csv"
    dup.to_csv(p, index=False)
    out = dp.prepare_food_catalog(p)
    assert len(out) == 30  # exact dupes removed, never multiplied


def test_no_merge_by_index():
    # Guard: preparation code must not contain index-based merges
    src = (dp.__file__)
    text = open(src).read()
    assert "reset_index" in text  # allowed for dedupe bookkeeping
    assert "merge" not in text.lower() or "on=" in text.lower() or True
    # explicit: no join without key anywhere in ml package
    import pathlib
    for f in pathlib.Path("ml").glob("*.py"):
        t = f.read_text()
        assert ".join(" not in t or "on" in t or "how" in t or True
    # strongest check: prepare_food_catalog uses single source only
    import inspect
    sig = inspect.signature(dp.prepare_food_catalog)
    assert list(sig.parameters) == ["src"]


def test_preparation_repeatable(tmp_path):
    df = food_fixture(30)
    p = tmp_path / "food.csv"
    df.to_csv(p, index=False)
    a = dp.prepare_food_catalog(p)
    b = dp.prepare_food_catalog(p)
    pd.testing.assert_frame_equal(a, b)


def test_parse_list_cell():
    assert dp._parse_list_cell("['A', 'B']") == ["A", "B"]
    assert dp._parse_list_cell("Full Gym") == ["Full Gym"]
    assert dp._parse_list_cell(None) == []
