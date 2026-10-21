"""Keyword-derived allergen flags for the Anuvaad food catalog.

The Anuvaad INDB ships nutrient composition only — no allergen columns. The
retired OpenFoodFacts archives in data/archive_unused/ carry allergen flags but
match only ~7 of 1014 Anuvaad names exactly, so they cannot tag this catalog.

This module derives allergen flags from the food NAME with explicit,
reviewable keyword rules (Indian, English and French ingredient vocabulary).
Design rules:
- A flag is set ONLY on a positive keyword match. A food with no match is
  reported as "not flagged", never as "certified allergen-free"; the
  recommender surfaces this caveat with every allergy-filtered response.
- Exceptions are applied BEFORE the generic rules (e.g. coconut/soy/oat milk
  must not raise the dairy flag; 'eggless' must not raise the eggs flag).
- Every keyword and exception is unit-tested in tests/test_allergens.py.
"""
import re

ALLERGEN_FLAGS = [
    "contains_gluten", "contains_dairy", "contains_nuts", "contains_peanuts",
    "contains_soy", "contains_eggs", "contains_fish",
]

# Applied first: phrases that must NOT trigger the generic keyword of the
# same family. (pattern, flags_to_cancel)
_EXCEPTIONS = [
    (r"coconut (milk|cream|water)|cr[eè]me de coco|lait de coco",
     ["contains_dairy"]),
    (r"(soy|soya|soja|almond|oat|rice|cashew|hazelnut|pistachio) milk",
     ["contains_dairy"]),
    (r"eggless|sans oeuf|sans œuf|without egg", ["contains_eggs"]),
]

# Generic keyword rules: flag -> word-boundary alternatives.
_KEYWORDS: dict[str, list[str]] = {
    "contains_gluten": [
        "wheat", "atta", "maida", "sooji", "rava", "semolina", "couscous",
        "semoule", "barley", "orge", "rye", "seigle", "spelt", "epeautre",
        "bulgur", "boulgour", "bread", "pain", "roti", "chapati",
        "paratha", "naan", "puri", "toast", "bun", "baguette", "croissant",
        "brioche", "biscuit", "cookie", "cake", "gateau", "gâteau", "pastry",
        "patisserie", "pâtisserie", "pasta", "spaghetti", "macaroni",
        "noodles", "nouilles", "vermicelli", "seviyan", "oat", "oatmeal",
        "avoine", "muesli", "granola", "cracker", "tortilla", "pizza",
        "sandwich", "burger bun", "wrap", "crepe", "crêpe", "pancake",
        "waffle", "gaufre", "sevai", "idiyappam", "appam",
    ],
    "contains_dairy": [
        "milk", "lait", "dairy", "laitier", "paneer", "cheese", "fromage",
        "curd", "yogurt", "yoghurt", "yaourt", "dahi", "lassi", "chaas",
        "ghee", "butter", "beurre", "cream", "creme", "crème", "khoya",
        "mawa", "khoa", "khoya", "whey", "casein", "caseine", "caséine", "ricotta",
        "mascarpone", "mozzarella", "cheddar", "feta", "haloumi", "kulfi",
        "ice cream", "glace", "malai", "rabri", "shrikhand",
        "mishti doi", "payasam", "kheer", "burfi", "barfi", "peda",
        "rasgulla", "rasmalai", "sandesh",
    ],
    "contains_nuts": [
        "almond", "badam", "cashew", "kaju", "pistachio", "pista", "walnut",
        "akhrot", "hazelnut", "noisette", "pecan", "macadamia",
        "brazil nut", "pine nut", "pignons", "nut", "noix",
        "praline", "pralin", "marzipan", "nougat",
    ],
    "contains_peanuts": [
        "peanut", "groundnut", "arachide", "moongphali",
        "moongfali", "mungfali", "satay",
    ],
    "contains_soy": [
        "soy", "soya", "soyabean", "soya bean", "soja", "tofu",
        "edamame", "miso", "tempeh", "natto",
        "textured vegetable protein", "tvp",
    ],
    "contains_eggs": [
        "egg", "oeuf", "œuf", "omelette", "omelet", "mayonnaise", "mayo",
        "meringue", "quiche", "frittata", "hollandaise", "egg wash",
    ],
    "contains_fish": [
        "fish", "poisson", "machli", "tuna", "thon", "salmon", "saumon",
        "sardine", "mackerel", "maquereau", "anchovy", "anchois", "cod",
        "cabillaud", "herring", "trout", "tilapia", "basa", "hilsa",
        "pomfret", "rohu", "katla", "prawn", "shrimp", "crevette", "crab",
        "crabe", "lobster", "homard", "crayfish", "langoustine", "mussel",
        "moule", "clam", "oyster", "huitre", "huître", "scallop",
        "saint-jacques", "squid", "calamari", "encornet", "octopus",
        "poulpe", "surimi", "seafood", "fruits de mer", "caviar", "roe",
    ],
}

# Optional plural suffix per keyword so "sardine" also matches "sardines",
# "egg" -> "eggs", "gateau" -> "gateaux", etc.
def _pattern(alternatives: list[str]) -> str:
    return r"(?<![a-z])(" + "|".join(
        re.escape(k) + r"(?:s|es|x)?" for k in alternatives) + r")(?![a-z])"


_COMPILED = {flag: re.compile(_pattern(kws), re.IGNORECASE)
             for flag, kws in _KEYWORDS.items()}
# 'nut(s)' must not match inside 'nutmeg'; 'noix' must not match in
# 'noix de coco' (coconut) — hand-written override with plurals.
_COMPILED["contains_nuts"] = re.compile(
    r"(?<![a-z])(almonds?|badams?|cashews?|kajus?|pistachios?|pistas?|"
    r"walnuts?|akhrots?|hazelnuts?|noisettes?|pecans?|macadamias?|"
    r"brazil nuts?|pine nuts?|pignons?|nuts?|noix(?! de coco)|"
    r"pralines?|pralins?|marzipans?|nougats?)(?![a-z])", re.IGNORECASE)


def screen_text(text: str) -> dict[str, bool]:
    """Allergen flags for a free-text food/meal name. Pure function."""
    s = str(text or "").lower()
    flags = {f: False for f in ALLERGEN_FLAGS}
    # exceptions cancel generic false positives
    cancelled: set[str] = set()
    for pattern, cancel in _EXCEPTIONS:
        if re.search(pattern, s):
            cancelled.update(cancel)
    for flag in ALLERGEN_FLAGS:
        if flag in cancelled:
            continue
        if _COMPILED[flag].search(s):
            flags[flag] = True
    return flags


def derive_allergens(name: str) -> dict[str, bool]:
    """Alias kept for catalog preparation readability."""
    return screen_text(name)


def flagged(flags: dict[str, bool]) -> list[str]:
    """Compact list of the flags that are True."""
    return [f for f in ALLERGEN_FLAGS if flags.get(f)]


# ---- diet-preference compatibility (vegetarian/vegan screening) ----
# Not allergens: meat vocabulary is screened separately for diet preference.
_MEAT_KEYWORDS = [
    "chicken", "poulet", "beef", "boeuf", "bœuf", "mutton", "lamb", "agneau",
    "pork", "porc", "bacon", "lardon", "ham", "jambon", "sausage",
    "saucisse", "kebab", "brochette", "veal", "veau", "turkey", "dinde",
    "duck", "canard", "meat", "viande", "keema", "qeema", "meatball",
    "mortadella", "salami", "pepperoni", "chorizo", "prosciutto", "jerky",
    "macher", "machher", "jhomka",
    # unambiguous meat dishes: 'kofta'/'korma' stay ambiguous (many
    # vegetarian variants exist in the catalog) but these are not
    "roghan josh", "rogan josh", "gosht", "nihari", "haleem", "paye",
    "nargisi kofta", "gushtaba",
]
MEAT_PATTERN = re.compile(
    r"(?<![a-z])(" + "|".join(
        re.escape(k) + r"(?:s|es|x)?" for k in _MEAT_KEYWORDS) + r")(?![a-z])",
    re.IGNORECASE)
HONEY_PATTERN = re.compile(r"(?<![a-z])honey|miel", re.IGNORECASE)

_PATTERN_LABELS = ((MEAT_PATTERN, "meat keywords in name (not an allergen "
                                  "flag — fish allergen flag covers fish)"),
                   (HONEY_PATTERN, "honey"))

# preference(casefold) -> (allergen flags to exclude, extra patterns to screen)
DIET_EXCLUSIONS = {
    "vegetarian": ({"contains_fish", "contains_eggs"}, (MEAT_PATTERN,)),
    "vegan": ({"contains_fish", "contains_eggs", "contains_dairy"},
              (MEAT_PATTERN, HONEY_PATTERN)),
    "omnivore": (set(), ()),
    "any": (set(), ()),
}


def text_conflicts_with_diet(text: str, preference: str) -> list[str]:
    """Flags that exclude `text` for the given dietary preference.

    Returns a list of reason strings (empty = compatible). Keyword-based:
    'not excluded' is not a certified guarantee — verify recipes.
    """
    key = str(preference or "").strip().casefold()
    a_flags, extra = DIET_EXCLUSIONS.get(key, (set(), ()))
    if not a_flags and not extra:
        return []
    s = str(text or "")
    reasons = [f for f, v in screen_text(s).items() if v and f in a_flags]
    for pattern, label in _PATTERN_LABELS:
        if pattern in extra and pattern.search(s):
            reasons.append(label)
    return reasons


def row_conflicts_with_diet(texts, preference: str) -> dict[str, list[str]]:
    """{text_string: [reasons]} for every conflicting text in an iterable."""
    out = {}
    for t in texts:
        if t is None:
            continue
        reasons = text_conflicts_with_diet(t, preference)
        if reasons:
            out[str(t)] = reasons
    return out
