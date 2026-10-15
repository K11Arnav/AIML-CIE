"""Reviewed ingredient taxonomy for indian_food.csv recipe tokens.

Rules:
- Whole-token match only (after normalization); no substring matching, so
  "peanut" never matches "groundnut" unless an explicit synonym entry exists.
- Normalization: lowercase, trim, collapse whitespace, explicit plural folding
  (SINGULARS) — never stemming.
- Unknown tokens stay "unknown" and force needs-review when allergies matter.
- "drumstick(s)" is deliberately NOT meat (moringa vegetable vs chicken leg is
  ambiguous in sambar context) -> unknown.
- "meat curry powder" is a spice mix, not meat -> spices.
- The recipe file's own "cottage cheese" means paneer (dairy); kept verbatim.
"""
import re

GROUP = {}  # canonical token -> group


def _g(group, *tokens):
    for t in tokens:
        GROUP[t] = group


# -- legumes --
_g("legumes", "urad dal", "chana dal", "chana daal", "moong dal", "toor dal",
   "arhar dal", "masoor dal", "split urad dal", "white urad dal",
   "whole urad dal", "split pigeon peas", "pigeon peas", "green moong beans",
   "moong beans", "mung bean", "kala chana", "chole", "chickpeas",
   "green peas", "fresh green peas", "frozen green peas", "peas", "dal",
   "lentils", "lentil flour", "black lentils", "green beans", "french beans",
   "long beans", "red kidney beans", "whole red beans", "kidney beans",
   "black eyed peas", "valor papdi", "surti papdi", "papdi", "sattu",
   "besan", "besan flour", "bengal gram flour", "gram flour",
   "roasted gram flour", "chickpea flour", "kala masala")
# -- grains --
_g("grains", "rice", "basmati rice", "parboiled rice", "raw rice", "cooked rice",
   "soaked rice", "idli rice", "brown rice", "glutinous rice", "sticky rice",
   "forbidden black rice", "beaten rice flakes", "rice flakes", "thick poha",
   "thin rice flakes", "poha", "bhatura", "naan bread", "pav", "puri",
   "bread crumbs", "loaf bread", "white bread slices", "whole wheat bread",
   "dinner rolls", "atta", "makki atta", "wheat flour", "whole wheat flour",
   "all purpose flour", "maida", "maida flour", "plain flour", "white flour",
   "refined flour", "corn flour", "rice flour", "brown rice flour",
   "jowar flour", "pearl millet flour", "sorghum flour", "rava", "sooji",
   "bombay rava", "semolina", "sevai", "vermicelli", "falooda sev", "sev",
   "boondi", "khaman", "dough", "sorghum")
# -- vegetables --
_g("vegetables", "potato", "potatoes", "baby potatoes", "boiled potatoes",
   "mashed potato", "aloo", "tomato", "tomatoes", "chopped tomatoes",
   "onion", "onions", "red onion", "pearl onions", "spinach", "palak",
   "cauliflower", "gobi", "cabbage", "okra", "ladies finger", "eggplant",
   "brinjal", "baingan", "bottle gourd", "ridge gourd", "bitter gourd",
   "pumpkin", "firm white pumpkin", "pumpkin flowers", "beetroot", "carrot",
   "carrots", "cucumber", "capsicum", "bell pepper", "bell peppers",
   "green bell pepper", "shimla mirch", "tindora", "potol", "drumstick",
   "drumsticks", "banana flower", "raw banana", "raw papaya", "elephant foot yam",
   "sweet potato", "mixed vegetables", "greens", "green", "arbi ke patte",
   "amaranth leaves", "fenugreek leaves", "methi leaves", "kasuri methi",
   "curry leaves", "coriander", "cilantro", "mint", "watercress", "mushroom",
   "wild mushrooms", "baby corn", "peas and carrots",
   "green peas and carrots", "lemon", "kitchen lime", "tamarind", "imli",
   "tamarind paste", "kokum", "amchur powder", "mango powder", "lemon juice",
   "wine vinegar", "ginger", "ginger powder", "ginger and garlic",   "garlic", "garlic powder", "green chili", "green chilies", "green chilli",
   "green chillies", "chilli", "chillies", "dry chilli", "fresh green chilli",
   "red chili", "red chilli", "red chillies", "whole red", "chili powder",
   "green chili paste", "green garlic chutney")
# -- fruits --
_g("fruits", "mango", "dried mango", "banana", "papaya", "guava", "coconut",
   "grated coconut", "desiccated coconut", "dry coconut", "fresh coconut",
   "coconut flakes", "coconut milk", "canned coconut milk", "coconut ice",
   "pomegranate", "apricots", "dried fruits", "dried mango",
   "dry dates", "dates", "dry fruits", "raisins", "cashews and raisins",
   "gooseberry", "orange rind", "musk melon seeds")
# -- dairy --
_g("dairy", "milk", "litre milk", "dharwadi buffalo milk", "reduced milk",
   "sweetened milk", "skimmed milk powder", "milk powder", "condensed milk",
   "yogurt", "yoghurt", "greek yogurt", "curd", "dahi", "butter",
   "clarified butter", "ghee", "cream", "heavy cream", "whipping cream",
   "nestle cream", "malai", "paneer", "cottage cheese", "chenna",
   "chenna cheese", "chhena", "khoa", "mawa", "fried milk power")
# -- nuts_seeds --
_g("nuts_seeds", "peanut", "peanuts", "raw peanuts", "peanut oil", "cashew nuts",
   "cashews", "sliced almonds", "slivered almonds", "almond", "almonds",
   "badam", "pistachio", "mixed nuts", "nuts", "sesame", "sesame seeds",
   "white sesame seeds", "black sesame seeds", "sesame oil", "poppy seeds",
   "khus khus", "khus-khus seeds", "chia seed", "nigella seeds", "flax seeds",
   "melon seeds", "sunflower seeds", "pumpkin seeds")
# -- spices --
_g("spices", "turmeric", "cumin", "coriander seed", "coriander powder",
   "cardamom", "green cardamom", "cardamom pods", "cardamom powder", "elachi",
   "cinnamon", "cinnamon stick", "clove", "cloves", "bay leaf", "fennel",
   "fennel seeds", "fenugreek seeds", "mustard seeds", "mustard seed",
   "nigella", "cumin seeds", "caraway seed", "celery seed", "dill seed",
   "fennel seed", "fenugreek", "mustard", "yellow mustard", "asafoetida",
   "hing", "saffron", "nutmeg", "mace", "star anise", "pepper", "black pepper",
   "white pepper", "red pepper", "paprika", "garam masala",
   "garam masala powder", "biryani masala", "biryani masala powder",
   "sambar powder", "rasam powder", "pav bhaji masala", "tandoori masala",
   "chole masala", "kitchen king", "curry powder", "meat curry powder",
   "malvani masala", "kala jeera", "panch phoran masala", "tea leaves",
   "tea bags", "coffee", "cocoa", "vanilla", "kewra",    "rose water",
   "citric acid", "baking soda", "baking powder", "alum powder",
   "arrowroot powder", "corn starch", "salt", "black salt", "rock salt",
   "sea salt", "pink salt")
# -- oils_fats (dairy fats stay in dairy; sesame oil stays in nuts_seeds) --
_g("oils_fats", "oil", "vegetable oil", "mustard oil", "olive oil",
   "sunflower oil", "rapeseed oil", "avocado oil", "coconut oil", "vanaspati")
# -- sweeteners --
_g("sweeteners", "sugar", "powdered sugar", "sugar syrup", "jaggery",
   "jaggery syrup", "gur", "honey", "rose syrup", "sweetened condensed milk",
   "sweet")
# -- meat_eggs --
_g("meat_eggs", "chicken", "chicken chunks", "chicken thighs",
   "skinless chicken breasts", "mutton", "lamb", "beef", "pork",
   "boiled pork", "fish", "fish fillet", "fish fillets", "fish roe",
   "prawns", "lobster", "crab", "eggs", "egg yolks", "whole egg", "egg")
# -- other (non-food / negligible) --
_g("other", "water", "hot water", "ice", "oil for frying", "fry",
   "marinade", "filling", "gravy", "sauce", "tomato sauce", "tomato paste",
   "soy sauce", "vinegar", "red food coloring", "saffron color", "steamer",
   "banana leaf", "low fat")

# Explicit plural folding (reviewed; never stemming)
SINGULARS = {
    "tomatoes": "tomato", "potatoes": "potato", "chilies": "chili",
    "chillies": "chili", "berries": "berry", "leaves": "leaf",
    "cloves": "clove", "cashews": "cashew", "almonds": "almond",
    "pistachios": "pistachio", "walnuts": "walnut", "dates": "date",
    "figs": "fig", "apricots": "apricot", "raisins": "raisin",
    "peanuts": "peanut", "beans": "bean", "peas": "pea", "eggs": "egg",
    "noodles": "noodle",
}

# Canonical synonyms (reviewed; whole-token only)
SYNONYMS = {
    "dahi": "curd", "yoghurt": "yogurt", "paneer": "cottage cheese",
    "besan": "gram flour", "chickpea flour": "gram flour",
    "bengal gram flour": "gram flour", "atta": "whole wheat flour",
    "maida": "all purpose flour", "rava": "semolina", "sooji": "semolina",
    "gur": "jaggery", "aloo": "potato", "baingan": "eggplant",
    "bhindi": "okra", "gobi": "cauliflower", "palak": "spinach",
    "methi": "fenugreek leaves", "haldi": "turmeric",
    "jeera": "cumin", "dhania": "coriander", "elaichi": "cardamom",
    "dalchini": "cinnamon", "laung": "clove", "adrak": "ginger",
    "lehsun": "garlic", "badam": "almond", "kaju": "cashew",
    "moongphali": "peanut", "til": "sesame", "sarson": "mustard",
    "chawal": "rice", "roti": "whole wheat bread", "elachi": "cardamom",
    "groundnut": "peanut", "groundnuts": "peanut",
}

# Singular canonical forms (SINGULARS folds plurals onto these keys)
_g("fruits", "raisin", "apricot", "date")
_g("nuts_seeds", "cashew", "peanut")
_g("vegetables", "pea", "bean")
_g("grains", "flour", "blend rice", "whole wheat rava", "sabudana",
   "vermicelli pudding")
_g("vegetables", "chili", "chilli")
_g("spices", "spices")
_g("legumes", "bhuna chana", "yellow moong daal", "axone")  # axone = fermented soybean
_g("meat_eggs", "bombay duck")  # bombay duck is a fish
_g("spices", "masala")
_g("other", "edible gum", "dried rose petals", "dry roasted")

# Safety sets (whole canonical tokens)
PEANUT = {"peanut", "peanuts", "raw peanuts", "peanut oil", "groundnut", "groundnut oil"}
MILK = {"milk", "litre milk", "dharwadi buffalo milk", "reduced milk",
        "sweetened milk", "skimmed milk powder", "milk powder",
        "condensed milk", "sweetened condensed milk", "yogurt", "curd",
        "greek yogurt", "butter", "clarified butter", "ghee", "cream",
        "heavy cream", "whipping cream", "nestle cream", "malai", "paneer",
        "cottage cheese", "chenna", "chenna cheese", "chhena", "khoa", "mawa",
        "fried milk power", "buttermilk", "lassi", "kefir"}
EGG = {"egg", "eggs", "egg yolks", "whole egg"}
FISH = {"fish", "fish fillet", "fish fillets", "fish roe", "bombay duck",
        "mackerel", "sardine", "tuna", "salmon"}
SHELLFISH = {"prawns", "lobster", "crab", "shellfish"}
FISH_SEAFOOD = FISH | SHELLFISH
TREENUT = {"almond", "almonds", "sliced almonds", "slivered almonds",
           "cashew", "cashew nuts", "cashews", "pistachio", "walnut", "mixed nuts",
           "nuts", "cashews and raisins"}
GLUTEN = {"wheat flour", "whole wheat flour", "atta", "maida", "maida flour",
          "all purpose flour", "plain flour", "white flour", "refined flour",
          "semolina", "rava", "sooji", "bread crumbs", "loaf bread",
          "white bread slices", "whole wheat bread", "dinner rolls", "pav",
          "naan bread", "bhatura", "sev", "vermicelli", "vermicelli pudding",
          "falooda sev", "soy sauce", "beer"}
SOY = {"soy sauce", "soy", "tofu", "soya", "soya chunks", "axone"}  # axone = fermented soybean
SESAME = {"sesame", "sesame seeds", "white sesame seeds",
          "black sesame seeds", "sesame oil", "til", "gingelly"}
MUSTARD = {"mustard", "mustard oil", "mustard seed", "mustard seeds",
           "yellow mustard", "mustard green", "sarson"}
NONVEG = {"chicken", "chicken chunks", "chicken thighs",
          "skinless chicken breasts", "mutton", "lamb", "beef", "pork",
          "boiled pork", "fish", "fish fillet", "fish fillets", "fish roe",
          "bombay duck", "prawns", "lobster", "crab", "egg", "eggs",
          "egg yolks", "whole egg"}
SWEETENERS = {"sugar", "powdered sugar", "sugar syrup", "jaggery",
              "jaggery syrup", "gur", "honey", "rose syrup",
              "sweetened milk", "condensed milk",
              "sweetened condensed milk"}
SALT_FAMILY = {"salt", "black salt", "rock salt", "sea salt", "pink salt"}

ALLERGY_SETS = {
    "peanut": PEANUT, "nut": PEANUT | TREENUT, "treenut": TREENUT,
    "dairy": MILK, "milk": MILK, "lactose": MILK,
    "egg": EGG,
    "fish": FISH_SEAFOOD, "seafood": FISH_SEAFOOD, "shellfish": SHELLFISH,
    "gluten": GLUTEN, "wheat": GLUTEN,
    "soy": SOY, "sesame": SESAME, "mustard": MUSTARD,
}


def normalize(token: str) -> str:
    t = re.sub(r"\s+", " ", str(token).strip().lower())
    t = SINGULARS.get(t, t)
    return SYNONYMS.get(t, t)


def group_of(token: str) -> str:
    return GROUP.get(normalize(token), "unknown")


def allergen_flags(token: str) -> set:
    """Allergy keys whose explicit sets match this token.

    Whole-token match, plus whole-WORD match inside multi-word tokens
    (e.g. "raw peanuts" contains the word "peanuts"). Single common words are
    never set members, so word-matching cannot misfire on "and"/"raw"/"oil".
    """
    c = normalize(token)
    candidates = {c} | set(c.split())
    return {k for k, s in ALLERGY_SETS.items() if candidates & s}
