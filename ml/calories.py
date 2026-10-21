"""Daily calorie target: Mifflin-St Jeor estimate. No model artifact exists for this
(nothing trained or saved), so a documented formula is used instead of inventing
a prediction. Labeled as an estimate everywhere; never clinical advice.

Formula (Mifflin-St Jeor, weight kg, height cm, age years):
  male:   10*w + 6.25*h - 5*a + 5
  female: 10*w + 6.25*h - 5*a - 161
Result x activity factor = maintenance-level daily energy need (goal-neutral:
no deficit/surplus applied, so no invented prescription).
"""
ACTIVITY_FACTORS = {
    "sedentary": 1.2,          # little/no exercise
    "lightly active": 1.375,   # light exercise/sports 1-3 days/week
    "moderate": 1.55,          # moderate exercise 3-5 days/week
    "moderately active": 1.55,          # nutrition_dataset alias of moderate
    "active": 1.725,           # hard exercise 6-7 days/week
    "very active": 1.725,               # nutrition_dataset alias of active
}
DEFAULT_ACTIVITY = "moderate"  # defensible middle when the optional field is omitted

DISCLAIMER = ("Estimate only, not clinical advice: actual needs vary with body "
              "composition, health conditions, and real activity.")


def estimate_daily_calories(age, height_cm, weight_kg, gender,
                            activity_level=None) -> dict:
    """Return {kcal_per_day, method, activity_level_used, activity_assumed, disclaimer}.

    Raises ValueError on non-positive inputs or unknown gender/activity.
    """
    try:
        age, height_cm, weight_kg = float(age), float(height_cm), float(weight_kg)
    except (TypeError, ValueError):
        raise ValueError("age, height_cm and weight_kg must be numeric")
    if not (age > 0 and height_cm > 0 and weight_kg > 0):
        raise ValueError("age, height_cm and weight_kg must be positive")
    g = str(gender or "").strip().lower()
    if g not in ("female", "male"):
        raise ValueError("gender must be Female or Male for this formula")
    assumed = False
    if activity_level is None or not str(activity_level).strip():
        activity_level, assumed = DEFAULT_ACTIVITY, True
    key = str(activity_level).strip().lower()
    if key not in ACTIVITY_FACTORS:
        raise ValueError(f"activity_level must be one of: {', '.join(ACTIVITY_FACTORS)}")
    s = 5 if g == "male" else -161
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + s
    kcal = int(round(bmr * ACTIVITY_FACTORS[key]))
    if kcal <= 0:
        raise ValueError("computed calorie target is not positive")
    return {
        "kcal_per_day": kcal,
        "method": ("Mifflin-St Jeor BMR x activity factor "
                   f"({key}={ACTIVITY_FACTORS[key]}); maintenance-level, goal-neutral"),
        "source": "calculation",
        "activity_level_used": key,
        "activity_assumed": assumed,
        "disclaimer": DISCLAIMER,
    }
