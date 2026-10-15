"""Workout tests: primary/alternatives, hard equipment filter, duration check, no fabrication."""
import json

import pytest

from tests.conftest import recommender_fixture


def test_default_returns_exactly_one_primary_plan(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({})
    json.dumps(out)
    assert out["primary"] is not None
    assert out["alternatives"] == []
    assert out["top_n"] == 1
    assert "ONE plan" in out["usage"]


def test_alternative_mode_returns_at_most_requested(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"top_n": 3})
    assert out["primary"] is not None
    assert len(out["alternatives"]) <= 2
    assert 1 + len(out["alternatives"]) <= 3
    labels = [a["choice_label"] for a in out["alternatives"]]
    assert all("INSTEAD" in lb for lb in labels)
    assert "follow this one" in out["primary"]["choice_label"]


def test_top_n_range_validated(tmp_path):
    r = recommender_fixture(tmp_path)
    with pytest.raises(ValueError):
        r.recommend_workout({"top_n": 0})
    with pytest.raises(ValueError):
        r.recommend_workout({"top_n": 5})
    with pytest.raises(ValueError):
        r.recommend_workout("not-a-dict")
    with pytest.raises(ValueError):
        r.recommend_workout({"available_minutes": "a lot"})


def test_exact_equipment_filter_excludes_incompatible(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"equipment": ["At Home"], "top_n": 4})
    assert out["primary"]["equipment"] == "At Home"
    assert all(a["equipment"] == "At Home" for a in out["alternatives"])
    assert out["unmet"] == []  # exact value: no warning needed


def test_unsupported_equipment_warns_and_excludes(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"equipment": ["Barbell"], "top_n": 1})
    assert out["primary"] is None
    assert out["alternatives"] == []
    assert any("Barbell" in u or "barbell" in u for u in out["unmet"])


def test_mixed_equipment_keeps_only_compatible(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"equipment": ["Full Gym", "Barbell"], "top_n": 4})
    plans = [out["primary"]] + out["alternatives"]
    assert all(p["equipment"] == "Full Gym" for p in plans)
    assert any("barbell" in u for u in out["unmet"])


def test_duration_check_on_primary(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"available_minutes": 20, "top_n": 1})
    dc = out["primary"]["duration_check"]
    assert dc["requested"] == 20
    assert dc["estimated"] is not None  # catalog always has durations
    assert isinstance(dc["fits"], bool)
    assert dc["note"]


def test_no_duration_requested_states_limitation(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"top_n": 1})
    assert out["primary"]["duration_check"]["fits"] is None
    assert "no fit check" in out["primary"]["duration_check"]["note"].lower()


def test_no_fabrication_all_titles_from_catalog(tmp_path):
    r = recommender_fixture(tmp_path)
    out = r.recommend_workout({"top_n": 4})
    catalog_titles = set(r._workout["title"].unique().tolist())
    plans = [out["primary"]] + out["alternatives"]
    assert len(plans) >= 1
    for p in plans:
        assert p["program"] in catalog_titles
        # exercise rows come from the same catalog slice
        assert len(p["exercises"]) >= 1
        assert {"exercise", "sets", "reps"} <= set(p["exercises"][0])
        assert "score_basis" in p


def test_empty_when_nothing_matches(tmp_path):
    r = recommender_fixture(tmp_path)
    r._workout = r._workout.iloc[0:0].copy()
    out = r.recommend_workout({"goal": "Bodybuilding"})
    assert out["primary"] is None and out["alternatives"] == []
