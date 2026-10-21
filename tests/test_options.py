"""Options tests: dropdown values derived from the trained model metadata."""
from ml.options import diet_options, workout_options


def test_workout_options_from_meta(recommender):
    o = workout_options(recommender._meta, recommender._workout_model)
    assert set(o["goals"]) == set(recommender._meta["values"]["workout"]["goals"])
    assert o["defaults"]["goal"] in o["goals"]
    assert {e["value"] for e in o["equipment"]} == \
        {"bodyweight only", "yoga mat", "home dumbbells", "full home gym", "gym membership"}
    assert o["top_n_meaning"].startswith("Total plans returned")


def test_diet_options_from_nutrition_frame(recommender):
    o = diet_options(recommender._nutrition, recommender._meta)
    assert set(o["dietary_preferences"]) >= {"Omnivore", "Vegetarian", "Vegan"}
    assert o["defaults"]["goal"] == "balanced"
    assert "fail-closed" in o["notes"][0]
