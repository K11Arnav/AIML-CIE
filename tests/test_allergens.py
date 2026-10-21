"""Keyword allergen rules (ml/allergens.py): exact, reviewable behavior.

Every positive/negative expectation here documents a real keyword decision —
including exceptions (coconut milk is NOT dairy, 'eggless' is NOT eggs).
"""
import pytest

from ml.allergens import ALLERGEN_FLAGS, derive_allergens, flagged, screen_text


@pytest.mark.parametrize("name,flag", [
    ("Paneer stuffed cheela", "contains_dairy"),
    ("Ghee roast dosa", "contains_dairy"),
    ("Cream of tomato soup", "contains_dairy"),
    ("Lassi sweet", "contains_dairy"),
    ("Khoa and coconut pancake", "contains_dairy"),
    ("Wheat bread slice", "contains_gluten"),
    ("Atta roti", "contains_gluten"),
    ("Sooji halwa", "contains_gluten"),
    ("Sandwich au fromage", "contains_gluten"),
    ("Almond badam milk", "contains_nuts"),
    ("Kaju katli", "contains_nuts"),
    ("Peanut chikki", "contains_peanuts"),
    ("Groundnut oil", "contains_peanuts"),
    ("Soyabean curry", "contains_soy"),
    ("Tofu stir-fry", "contains_soy"),
    ("Egg bhurji", "contains_eggs"),
    ("Mayonnaise dip", "contains_eggs"),
    ("Fish curry", "contains_fish"),
    ("Prawn masala", "contains_fish"),
    ("Sardines in oil", "contains_fish"),
])
def test_positive_flags(name, flag):
    assert derive_allergens(name)[flag] is True


@pytest.mark.parametrize("name,flag,why", [
    ("Coconut milk curry", "contains_dairy", "coconut milk is not dairy"),
    ("Coconut cream pie", "contains_dairy", "coconut cream exception"),
    ("Soy milk latte", "contains_dairy", "plant milk exception"),
    ("Almond milk smoothie", "contains_dairy", "plant milk exception"),
    ("Eggless chocolate cake", "contains_eggs", "eggless exception"),
    ("Rice flour dosa", "contains_gluten", "rice flour has no gluten keyword"),
    ("Besan chilla", "contains_gluten", "chickpea flour is gluten-free"),
    ("Lentil soup", "contains_dairy", "no dairy keyword"),
    ("Basil pesto", "contains_dairy", "name alone carries no dairy keyword"),
    ("Hot tea (Garam Chai)", None, "plain tea carries no allergen"),
    ("Fruit chaat", None, "no flags at all"),
])
def test_negative_and_exceptions(name, flag, why):
    flags = derive_allergens(name)
    if flag:
        assert flags[flag] is False, why
    else:
        assert not flagged(flags), why


def test_nutmeg_is_not_a_nut_and_coconut_is_not_flagged():
    f = screen_text("nutmeg rice pudding")
    assert f["contains_nuts"] is False
    f2 = screen_text("noix de coco dessert")
    assert f2["contains_nuts"] is False and f2["contains_dairy"] is False


def test_flag_keys_stable():
    assert list(screen_text("x").keys()) == ALLERGEN_FLAGS


def test_flagged_helper():
    assert flagged(screen_text("paneer tikka")) == ["contains_dairy"]
    assert flagged(screen_text("peanut paneer eggs sandwich")) == [
        "contains_gluten", "contains_dairy", "contains_peanuts", "contains_eggs"]
