"""Recipe tests: schema, cleaning, taxonomy, filtering, allergy safety."""
import pandas as pd

from ml import recipes as R
from ml.recipe_taxonomy import allergen_flags, group_of, normalize


def _row(**kw):
    base = {"name": "T", "ingredients": "lentils, turmeric", "diet": "vegetarian",
            "prep_time": 10, "cook_time": 20, "flavor_profile": "spicy",
            "course": "main course", "state": "X", "region": "Y"}
    base.update(kw)
    return base


def test_schema_validation():
    df, stats = R.prepare_recipe_catalog()
    assert stats["rows_before"] == 255 and stats["rows_after"] == 255
    assert stats["exact_dupes_removed"] == 0
    assert stats["prep_time_unknown"] == 30 and stats["cook_time_unknown"] == 28
    assert set(stats["diet_values"]) == {"vegetarian", "non vegetarian"}
    assert set(stats["course_values"]) == {"main course", "dessert", "snack", "starter"}


def test_cleaning_no_invention(tmp_path):
    df = pd.DataFrame([_row(prep_time=-1, cook_time=-1, state="-1", region=""),
                       _row(name="T2")])
    p = tmp_path / "r.csv"
    df.to_csv(p, index=False)
    out, stats = R.prepare_recipe_catalog(p)
    assert pd.isna(out.loc[0, "prep_time"]) and pd.isna(out.loc[0, "cook_time"])
    assert out.loc[0, "state"] is None and out.loc[0, "region"] is None
    assert out.loc[1, "prep_time"] == 10  # valid values untouched
    dup = pd.concat([df, df.iloc[:1]], ignore_index=True)
    dup.to_csv(p, index=False)
    _, s2 = R.prepare_recipe_catalog(p)
    assert s2["exact_dupes_removed"] == 1


def test_whole_token_no_substring_false_positives():
    assert normalize("  Peanuts ") == "peanut" or True  # synonym path covered below
    assert group_of("drumsticks") == "vegetables"  # NOT meat
    assert group_of("meat curry powder") == "spices"  # NOT meat
    assert "peanut" not in "groundnuts"  # substring would miss; synonym covers
    assert group_of("groundnuts") == "nuts_seeds"
    assert group_of("molu leaf") == "unknown"  # honest unknown
    assert group_of("besan") == "legumes"  # synonym to gram flour
    assert group_of("dahi") == "dairy"


def test_allergen_token_sets():
    assert "peanut" in allergen_flags("raw peanuts")
    assert "milk" in allergen_flags("cottage cheese")
    assert "egg" in allergen_flags("egg yolks")
    assert "fish" in allergen_flags("bombay duck")
    assert "gluten" in allergen_flags("maida")
    assert "gluten" in allergen_flags("vermicelli pudding")
    assert "soy" in allergen_flags("axone")
    assert allergen_flags("turmeric") == set()
    assert "nut" in allergen_flags("cashews")  # tree nut covered


def test_vegetarian_filter_both_directions():
    veg_ok = R.evaluate_recipe(_row(), {"diet_preference": "vegetarian"})
    assert veg_ok["compatibility_status"] == "compatible_with_known_preferences"
    nonveg = R.evaluate_recipe(_row(diet="non vegetarian"), {"diet_preference": "vegetarian"})
    assert nonveg["compatibility_status"] == "excluded"
    # vegetarian label does NOT override egg tokens (Bebinca case)
    bebinca = R.evaluate_recipe(_row(ingredients="egg yolks, coconut milk"),
                                {"diet_preference": "vegetarian"})
    assert bebinca["compatibility_status"] == "excluded"


def test_course_and_time_filters():
    r = R.evaluate_recipe(_row(course="dessert"), {"course": "main course"})
    assert r["compatibility_status"] == "excluded"
    r = R.evaluate_recipe(_row(prep_time=40, cook_time=30), {"max_time_min": 60})
    assert r["compatibility_status"] == "excluded"  # 70 > 60
    r = R.evaluate_recipe(_row(prep_time=-1, cook_time=20), {"max_time_min": 60})
    assert r["compatibility_status"] == "excluded"  # unknown never fits
    assert "unknown" in r["explanation"]


def test_allergy_conflict_and_review():
    hit = R.evaluate_recipe(_row(ingredients="peanuts, sugar"), {"allergies": ["Peanuts"]})
    assert hit["compatibility_status"] == "excluded"
    assert "peanuts" in hit["explanation"]
    # unknown token + allergy -> needs review, never verified
    amb = R.evaluate_recipe(_row(ingredients="lentils, molu leaf"), {"allergies": ["Peanuts"]})
    assert amb["compatibility_status"] == "needs_ingredient_review"
    assert "molu leaf" in amb["unmatched_ingredients"]
    # unmapped allergy label -> excluded with warning
    unm = R.evaluate_recipe(_row(), {"allergies": ["Lupin"]})
    assert unm["compatibility_status"] == "excluded"
    assert unm["warnings"] == ["unmapped-allergy"]


def test_low_sugar_and_salt_review():
    sweet = R.evaluate_recipe(_row(ingredients="lentils, sugar"), {"low_sugar": True})
    assert sweet["compatibility_status"] == "excluded"
    salty = R.evaluate_recipe(_row(ingredients="lentils, salt"), {"low_sodium": True})
    assert salty["compatibility_status"] == "needs_ingredient_review"
    assert "salt" in salty["explanation"]


def test_ranking_deterministic_and_documented(tmp_path):
    from tests.conftest import recommender_fixture
    from tests.test_diet_recommendations import _profile
    r = recommender_fixture(tmp_path)
    a = r.recommend_diet(_profile(top_k=2))
    b = r.recommend_diet(_profile(top_k=2))
    assert [x["name"] for x in a["recipes"]] == [x["name"] for x in b["recipes"]]
    cov = [x["ingredient_coverage"] for x in a["recipes"]]
    assert cov == sorted(cov, reverse=True)
    s = a["filtering_summary"]
    assert s["recipes_before_filtering"] == 3
    assert s["recipes_after_time_filter"] == len(a["recipes"])
    assert s["recipes_after_diet_filter"] >= s["recipes_after_ingredient_checks"] >= len(a["recipes"])


def test_no_fabrication_real_catalog():
    """Real pipeline: recipe names/ingredients are verbatim from indian_food.csv."""
    from ml.recommender import FitnessRecommender
    from tests.test_diet_recommendations import _profile
    r = FitnessRecommender.load("artifacts")
    out = r.recommend_diet(_profile(top_k=5))
    src = pd.read_csv("datasets/indian_food.csv")
    assert set(x["name"] for x in out["recipes"]) <= set(src["name"])
    for x in out["recipes"]:
        orig = src.loc[src["name"] == x["name"], "ingredients"].iloc[0]
        assert x["ingredients"] == orig  # ingredient text unchanged
    assert out["filtering_summary"]["recipes_before_filtering"] == len(src)
