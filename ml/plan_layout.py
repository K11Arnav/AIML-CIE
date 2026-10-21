"""Deterministic plan layout: model-predicted plan name -> day-by-day exercises.

The workout RF model predicts a plan NAME (24 classes from
smartfit_workout_dataset.csv); it cannot predict exercises. This module holds
the single, documented mapping that lays each plan out using only
datasets/exercises.json — no other dataset, nothing invented per-request.

Design rules (all fixed, testable):
- PLAN_LAYOUTS: class -> ordered body-part rotation, supported equipment
  (values from the smartfit dataset itself), and fixed (sets, reps) scheme.
- Equipment groups map exercises.json `equipment` values to the equipment the
  user selected. The user can only receive exercises their selected equipment
  supports.
- Exercise selection is deterministic: stable library order (id order), first
  N per day's body part. No shuffling, no randomness.
- Duration is a transparent heuristic (warmup + sets x (reps x 3s + 60s rest)),
  labeled as an estimate — the training data has NO per-plan durations.
"""
import math

# ---- equipment groups over exercises.json `equipment` values ----
GROUP_VALUES = {
    "barbell": {"barbell", "ez barbell", "olympic barbell", "trap bar"},
    "dumbbell": {"dumbbell", "kettlebell"},
    "machine": {"cable", "leverage machine", "sled machine", "stepmill machine",
                "stationary bike", "elliptical machine", "skierg machine",
                "upper body ergometer", "smith machine", "assisted"},
    "bodyweight": {"body weight", "bosu ball", "stability ball", "roller",
                   "wheel roller", "weighted", "hammer", "tire", "rope",
                   "medicine ball"},
    "band": {"band", "resistance band"},
}
EQUIPMENT_TO_GROUPS = {  # smartfit equipment label -> exercise groups the user can do
    "Bodyweight Only": {"bodyweight"},
    "Yoga Mat": {"bodyweight"},
    "Home Dumbbells": {"dumbbell", "bodyweight"},
    "Full Home Gym": {"dumbbell", "barbell", "machine", "bodyweight", "band"},
    "Gym Membership": {"dumbbell", "barbell", "machine", "bodyweight", "band"},
}
EXERCISE_GROUP = {e: g for g, vals in GROUP_VALUES.items() for e in vals}

# ---- the 24 model classes: name -> (body_parts rotation, supported equipment
# labels, sets, reps (None = timed), style) ----
PLAN_LAYOUTS: dict[str, dict] = {
    "3-Day Full Body Mix": dict(body_parts=["chest", "back", "upper legs", "shoulders", "waist"],
                                equipment=["Home Dumbbells", "Gym Membership", "Full Home Gym"],
                                sets=3, reps=10, style="full-body mix"),
    "5x3x1 Strength Program": dict(body_parts=["upper legs", "back", "chest"],
                                   equipment=["Full Home Gym", "Gym Membership"],
                                   sets=3, reps=3, style="heavy strength blocks"),
    "5x5 Compound Lifts": dict(body_parts=["upper legs", "back", "chest"],
                               equipment=["Full Home Gym", "Gym Membership"],
                               sets=5, reps=5, style="compound strength"),
    "Advanced Calisthenics": dict(body_parts=["chest", "upper arms", "waist", "back"],
                                  equipment=["Bodyweight Only"],
                                  sets=4, reps=8, style="advanced bodyweight"),
    "Bodyweight Circuit": dict(body_parts=["chest", "waist", "upper legs"],
                               equipment=["Bodyweight Only"],
                               sets=3, reps=12, style="bodyweight circuit"),
    "Core Stability, Yoga & Walking": dict(body_parts=["waist", "cardio", "upper legs"],
                                           equipment=["Yoga Mat", "Bodyweight Only"],
                                           sets=3, reps=10, style="mobility + walking"),
    "Daily 30-min Bodyweight Flow": dict(body_parts=["waist", "chest", "upper legs"],
                                         equipment=["Bodyweight Only"],
                                         sets=3, reps=10, style="short flow"),
    "Dumbbell Upper/Lower Split": dict(body_parts=["upper legs", "chest", "back", "shoulders"],
                                       equipment=["Home Dumbbells", "Full Home Gym"],
                                       sets=4, reps=8, style="upper/lower split"),
    "Full Body Dumbbell Complex": dict(body_parts=["upper legs", "chest", "back", "shoulders", "upper arms"],
                                       equipment=["Home Dumbbells", "Full Home Gym"],
                                       sets=3, reps=10, style="dumbbell complex"),
    "HIIT with Dumbbells": dict(body_parts=["shoulders", "upper arms", "upper legs", "waist"],
                                equipment=["Home Dumbbells", "Full Home Gym"],
                                sets=4, reps=12, style="HIIT"),
    "High Reps Low Weight Sculpting": dict(body_parts=["shoulders", "upper arms", "chest", "waist", "upper legs"],
                                           equipment=["Home Dumbbells", "Gym Membership", "Full Home Gym"],
                                           sets=3, reps=15, style="high-rep sculpting"),
    "Jump Rope & Burpee Intervals": dict(body_parts=["cardio", "waist", "lower legs"],
                                         equipment=["Bodyweight Only"],
                                         sets=4, reps=12, style="cardio intervals"),
    "Long Distance Running Plan": dict(body_parts=["cardio", "lower legs", "upper legs"],
                                       equipment=["Bodyweight Only"],
                                       sets=1, reps=None, style="endurance (timed runs)"),
    "Lower Body Bodyweight & Hiking": dict(body_parts=["upper legs", "lower legs", "waist"],
                                           equipment=["Bodyweight Only"],
                                           sets=3, reps=12, style="endurance bodyweight"),
    "Lower Body Power & Stationary Bike": dict(body_parts=["upper legs", "lower legs", "cardio"],
                                               equipment=["Full Home Gym", "Gym Membership"],
                                               sets=4, reps=6, style="power + bike"),
    "Metabolic Resistance Training": dict(body_parts=["chest", "back", "upper legs", "shoulders", "waist"],
                                          equipment=["Home Dumbbells", "Gym Membership", "Full Home Gym"],
                                          sets=3, reps=12, style="metabolic resistance"),
    "Olympic Lifting & Plyometrics": dict(body_parts=["upper legs", "back", "chest", "lower legs"],
                                          equipment=["Gym Membership", "Full Home Gym"],
                                          sets=5, reps=3, style="olympic + plyo"),
    "Push-Pull-Legs Split (Hypertrophy)": dict(body_parts=["chest", "back", "upper legs", "shoulders", "upper arms"],
                                               equipment=["Gym Membership", "Full Home Gym", "Home Dumbbells"],
                                               sets=4, reps=8, style="PPL hypertrophy"),
    "Seated Upper Body Strength & Rowing": dict(body_parts=["back", "shoulders", "upper arms", "chest"],
                                                equipment=["Gym Membership", "Full Home Gym"],
                                                sets=4, reps=5, style="upper-body strength"),
    "Swimming & Upper Body Machines": dict(body_parts=["back", "chest", "upper arms", "shoulders"],
                                           equipment=["Gym Membership", "Full Home Gym"],
                                           sets=3, reps=10, style="machines + swim"),
    "Treadmill Intervals & Circuit Training": dict(body_parts=["cardio", "upper legs", "waist"],
                                                   equipment=["Gym Membership", "Full Home Gym"],
                                                   sets=3, reps=10, style="treadmill circuit"),
    "Upper Body Calisthenics & Core": dict(body_parts=["chest", "upper arms", "shoulders", "waist"],
                                           equipment=["Bodyweight Only"],
                                           sets=3, reps=10, style="calisthenics + core"),
    "WOD & High Intensity Functional Training": dict(body_parts=["chest", "upper legs", "waist", "back"],
                                                     equipment=["Gym Membership", "Full Home Gym", "Home Dumbbells", "Bodyweight Only"],
                                                     sets=4, reps=10, style="WOD"),
    "Yoga & Mobility Flow": dict(body_parts=["waist", "shoulders", "upper legs", "lower legs"],
                                 equipment=["Yoga Mat", "Bodyweight Only"],
                                 sets=2, reps=10, style="mobility"),
}
TIMED_REPS_FOR_ESTIMATE = 10
WARMUP_MIN = 5.0
ACTION_SECONDS_PER_REP = 3.0
REST_SECONDS = 60.0
EXERCISES_PER_DAY = 5
DEFAULT_DAYS_PER_WEEK = 4


def compatible_plans(equipment_label: str) -> set:
    """Plan classes whose layout supports the user's selected equipment."""
    return {name for name, cfg in PLAN_LAYOUTS.items()
            if equipment_label in cfg["equipment"]}


def plan_layout(plan: str) -> dict:
    if plan not in PLAN_LAYOUTS:
        raise ValueError(f"unknown plan class: {plan!r}")
    return PLAN_LAYOUTS[plan]


def estimate_minutes(sets: int, reps: int | None, n_exercises: int = 1) -> float:
    """Transparent estimate (NOT from training data — none exists).

    warmup + per-day: exercises x sets x (moved seconds + rest seconds),
    rounded to 0.1 min. Heuristic only, labeled everywhere.
    """
    reps_eff = TIMED_REPS_FOR_ESTIMATE if reps is None else reps
    per_set = (reps_eff * ACTION_SECONDS_PER_REP + REST_SECONDS) / 60.0
    return round(WARMUP_MIN + n_exercises * sets * per_set, 1)


def _pool_for_day(library, body_part: str, groups: set) -> list:
    """Deterministic exercise pool: stable library order, first N kept."""
    out = []
    for _, r in library.iterrows():  # library preserves source/json id order
        if r["body_part"] != body_part:
            continue
        if EXERCISE_GROUP.get(r["equipment"]) not in groups:
            continue
        out.append(r)
    return out


def build_week(plan: str, library, equipment_label: str,
               days_per_week: int | None) -> dict:
    """Lay the plan out day by day using the user's equipment only.

    Body parts rotate over the plan's rotation; if days > rotation length the
    split repeats (reported, not hidden). Exercises are picked deterministically.
    """
    cfg = plan_layout(plan)
    days_per_week = int(days_per_week or DEFAULT_DAYS_PER_WEEK)
    n = max(1, min(days_per_week, 7))
    groups = EQUIPMENT_TO_GROUPS.get(equipment_label,
                                     EQUIPMENT_TO_GROUPS["Bodyweight Only"])
    days = []
    for d in range(1, n + 1):
        bp = cfg["body_parts"][(d - 1) % len(cfg["body_parts"])]
        pool = _pool_for_day(library, bp, groups)[:EXERCISES_PER_DAY]
        ex = [{"name": str(r["name"]), "equipment": str(r["equipment"]),
               "sets": cfg["sets"], "reps": cfg["reps"],
               "instruction_steps": str(r["instruction_steps"])}
              for r in pool]
        days.append({"day": d, "body_part": bp,
                     "pool_size": len(pool), "exercises": ex})
    repeats = n > len(cfg["body_parts"])
    n_ex_first = len(days[0]["exercises"]) or 1
    est = estimate_minutes(cfg["sets"], cfg["reps"], n_ex_first)
    return {"days": days, "sets": cfg["sets"], "reps": cfg["reps"],
            "style": cfg["style"],
            "split_repeats": bool(repeats),
            "estimated_minutes_per_day": est,
            "estimate_basis": (f"warmup {WARMUP_MIN:g} min + sets x "
                               f"(reps x {ACTION_SECONDS_PER_REP:g}s + {REST_SECONDS:g}s rest) "
                               "— heuristic, no per-plan durations in the training data")}
