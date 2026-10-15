"""Indian-food derived catalog: documented keyword/head-noun selection.

Rule (reviewed 2026-10-15 against the full 185-row shortlist):
  1. DISH match (explicit Indian dish/ingredient keywords) and not BLOCKed
     -> evidence class "indian_dish".
  2. Else HEAD-NOUN match (generic staple head nouns) and not BLOCKed
     -> evidence class "staple_ingredient" (ordinary Indian-diet staple with an
     exact record; NOT claimed to be a dish).
  3. Else excluded (branded foreign products, other cuisines, snacks, ...).
Branded flag: name starts with 6+ ALL-CAPS/digit characters (e.g. "365 ...",
"AUTHENTIC ..."); recorded, not hidden. Cottage cheese / tofu / cape-gooseberry
"poha" and similar false friends are NOT matched by any pattern.
Names are kept verbatim — never renamed or translated.
"""
import re

import pandas as pd

DISH_PATTERNS = [
    'chapati', '\\broti,', '\\bnaan\\b', 'paratha', 'besan', 'papad',
    'puri\\b', 'bhatura', 'kulcha', 'samosa', 'pakora', 'bhaji',
    'dal bukhara', 'pindi chana', 'palak paneer', 'pav bhaji', 'chana dal',
    'bengal gram split', 'aloo paratha', 'aloo puri', 'tandoori whole',
    'tandoori chicken', '\\bghee\\b', '\\bdosa\\b', '\\bidli\\b', 'upma',
    'dhokla', 'biryani', 'khichdi', 'sambar', 'rasam', 'jalebi', 'laddu',
    'ladoo', 'halwa', 'kheer', 'raita', 'chole', 'saag', 'khandvi',
    'thepla', 'misal', 'kachori', 'uttapam', 'vada pav',
]

HEAD_NOUNS = [
    'Lentils', 'Rice, b', 'Rice, r', 'Chickpeas', 'Wheat flour', 'Wheat flours',
    'Flour, semolina', 'Semolina', 'Spices', 'Spinach', 'Potatoes, baked',
    'Potatoes, boiled', 'Potatoes, microwaved', 'Potatoes, gold', 'Potatoes, red',
    'Potatoes, russet', 'Tomatoes, sun', 'Tomato powder', 'Tomato, paste',
    'Carrots,', 'Cauliflower, green', 'Cabbage, savoy', 'Okra', 'Guavas, common',
    'Guavas, strawberry', 'Nuts, almond', 'Nuts, cashew', 'Peanuts,',
    'Peas and', 'Bread, chapati', 'Bread, naan', 'Papad', 'Chickpea flour',
    'Chickpeas,',
]

BLOCK_PATTERNS = [
    'granola', 'popcorn', 'cheddar', 'dijon', 'chips', 'crisps', 'snack',
    'pasta', 'macaroni', 'spaghetti', 'pork', 'fast food', 'babyfood',
    'fried', 'hash brown', 'mashed', 'cake', 'cracker', 'jerky', 'pickled',
    'japanese', 'honey roasted', 'smoke flavor', 'matzo', 'bagel', 'noodle',
    'pizza', 'sandwich', 'nacho', 'quaker', 'oat', 'cereal', 'stuffing',
    'sponge', 'sardine', 'mackerel', 'tuna', 'candy', 'chocolate', 'ice cream',
    'wild rice', "uncle ben",
]

_DISH_RE = re.compile('(' + '|'.join(DISH_PATTERNS) + ')', re.I)
_HEAD_RE = re.compile('^(' + '|'.join(HEAD_NOUNS) + ')')
_BLOCK_RE = re.compile('(' + '|'.join(BLOCK_PATTERNS) + ')', re.I)
_BRANDED_RE = re.compile(r'^[A-Z0-9 ,&\-]{6,}')


def classify(name: str) -> tuple[str | None, str | None]:
    """Return (evidence_class, matched_term) or (None, None) if excluded."""
    n = str(name)
    if _BLOCK_RE.search(n):
        return None, None
    m = _DISH_RE.search(n)
    if m:
        return "indian_dish", m.group(1).lower()
    if _HEAD_RE.search(n):
        return "staple_ingredient", n.split(',')[0].strip()
    return None, None


def is_branded(name: str) -> bool:
    return bool(_BRANDED_RE.search(str(name)))


def build_indian_catalog(df: pd.DataFrame, name_col: str = "food_name") -> pd.DataFrame:
    """Filter a healthy-schema frame to the Indian-food derived catalog."""
    names = df[name_col].fillna('')
    classes, terms = zip(*[classify(n) for n in names]) if len(names) else ([], [])
    out = df.copy()
    out['cuisine_evidence'] = list(classes)
    out['evidence_term'] = list(terms)
    out['is_branded'] = [is_branded(n) for n in names]
    out = out[out['cuisine_evidence'].notna()].reset_index(drop=True)
    return out
