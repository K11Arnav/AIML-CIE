"""Plan layout tests: every model class mapped, deterministic, equipment-aware."""
import pytest

from ml.plan_layout import (DEFAULT_DAYS_PER_WEEK, EXERCISES_PER_DAY,
                            PLAN_LAYOUTS, build_week, compatible_plans,
                            estimate_minutes, plan_layout)
from tests.conftest import library_fixture


def test_all_24_plan_classes_have_layouts():
    assert len(PLAN_LAYOUTS) == 24


def test_layouts_reference_real_catalog_equipment_values():
    from ml.config import WORKOUT_DATA_FILE
    import pandas as pd
    df = pd.read_csv(WORKOUT_DATA_FILE)
    equip_values = set(df["Equipment"].unique())
    for name, cfg in PLAN_LAYOUTS.items():
        assert set(cfg["equipment"]) <= equip_values, (name, cfg["equipment"])


def test_every_equipment_label_has_compatible_plans():
    from ml.plan_layout import EQUIPMENT_TO_GROUPS
    for label in EQUIPMENT_TO_GROUPS:
        assert compatible_plans(label), label


def test_unknown_plan_raises():
    with pytest.raises(ValueError):
        plan_layout("Made-up Plan")


def test_build_week_respects_equipment(tmp_path):
    lib = library_fixture()
    wk = build_week("Push-Pull-Legs Split (Hypertrophy)", lib, "Bodyweight Only", None)
    assert wk["days"], "empty layout"
    for day in wk["days"]:
        for ex in day["exercises"]:
            assert ex["equipment"] in ("body weight",), ex  # barbell/dumbbell excluded


def test_build_week_deterministic(tmp_path):
    lib = library_fixture()
    a = build_week("Full Body Dumbbell Complex", lib, "Home Dumbbells", 3)
    b = build_week("Full Body Dumbbell Complex", lib, "Home Dumbbells", 3)
    assert a == b
    names = [ex["name"] for d in a["days"] for ex in d["exercises"]]
    # dumbbell user must get the dumbbell bench options, not barbell-only ones
    assert "Goblet Squat" in names and "Bench Press" not in names


def test_default_days_and_rotation_wrap():
    lib = library_fixture()
    wk = build_week("5x5 Compound Lifts", lib, "Full Home Gym", None)
    assert len(wk["days"]) == DEFAULT_DAYS_PER_WEEK


def test_exercises_per_day_capped():
    lib = library_fixture()
    wk = build_week("5x5 Compound Lifts", lib, "Full Home Gym", None)
    for day in wk["days"]:
        assert len(day["exercises"]) <= EXERCISES_PER_DAY


def test_timed_reps_plan_and_estimate():
    lib = library_fixture()
    wk = build_week("Long Distance Running Plan", lib, "Bodyweight Only", 2)
    assert wk["reps"] is None
    assert all(ex["reps"] is None for d in wk["days"] for ex in d["exercises"])
    assert estimate_minutes(3, None) == estimate_minutes(3, 10)  # timed=10 for estimate


def test_estimate_minutes_positive_and_reasonable():
    e = estimate_minutes(3, 10, 5)  # 5 exercises x 3 sets x ~1.5 min + warmup
    assert 15 <= e <= 45
    assert estimate_minutes(3, 10) >= 5
