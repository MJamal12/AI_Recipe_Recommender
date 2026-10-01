"""
Recipe Core
Pure recommendation logic shared by the CLI and the web app.

Nothing in this module touches the network or the filesystem, so the same
file runs in CPython (main.py) and in the browser via Pyodide (web/).
"""

import re
from typing import Dict, List, Optional

import pandas as pd


# Diets Spoonacular reports as boolean flags on the recipe itself.
# Anything else (paleo, ketogenic, ...) is matched against the `diets` list.
DIET_FLAGS = {
    'vegetarian': 'vegetarian',
    'vegan': 'vegan',
    'gluten-free': 'glutenFree',
    'gluten free': 'glutenFree',
    'dairy-free': 'dairyFree',
    'dairy free': 'dairyFree',
}

# Spoonacular occasionally returns a recipe step as an ingredient "name"
# ("in a soup pot over heat, stir in..."). Real names are short.
_MAX_NAME_WORDS = 4

_SEPARATORS = re.compile(r'\s*(?:,|;|\n|\band\b|&|\+)\s*', re.IGNORECASE)


def parse_ingredients(text: str) -> List[str]:
    """
    Turn loosely typed input into a clean ingredient list.

    Handles "chicken, rice", "chicken and rice; garlic", one per line, and
    repeated entries. Order is preserved so the user sees what they typed.
    """
    seen = set()
    ingredients = []
    for part in _SEPARATORS.split(text or ''):
        name = ' '.join(part.lower().split())
        if name and name not in seen:
            seen.add(name)
            ingredients.append(name)
    return ingredients


def clean_names(ingredients: List[Dict]) -> List[str]:
    """Readable, de-duplicated ingredient names, dropping sentence-like junk."""
    names = []
    for item in ingredients:
        name = ' '.join(str(item.get('name', '')).split())
        if name and len(name.split()) <= _MAX_NAME_WORDS and ',' not in name and name not in names:
            names.append(name)
    return names


def merge_details(found: List[Dict], details: List[Dict]) -> pd.DataFrame:
    """
    Join findByIngredients matches with their full recipe information.

    `found` carries the match data (used / missing ingredients); `details`
    carries time, servings, diets and the source link. Recipes missing from
    `details` are dropped, since they can't be filtered reliably.
    """
    details_by_id = {d['id']: d for d in details if d and 'id' in d}
    rows = []
    for match in found:
        info = details_by_id.get(match['id'])
        if not info:
            continue
        used = match.get('usedIngredients', [])
        missed = match.get('missedIngredients', [])
        rows.append({
            'id': match['id'],
            'title': match['title'],
            'image': match.get('image') or info.get('image', ''),
            'used_count': len(used),
            'missed_count': len(missed),
            'used_names': clean_names(used),
            'missed_names': clean_names(missed),
            'ready_in_minutes': info.get('readyInMinutes'),
            'servings': info.get('servings'),
            'source_url': info.get('sourceUrl') or info.get('spoonacularSourceUrl', ''),
            'diets': info.get('diets', []),
            'cuisines': info.get('cuisines', []),
            'vegetarian': bool(info.get('vegetarian')),
            'vegan': bool(info.get('vegan')),
            'glutenFree': bool(info.get('glutenFree')),
            'dairyFree': bool(info.get('dairyFree')),
        })
    return pd.DataFrame(rows)


def apply_filters(
    df: pd.DataFrame,
    diet: Optional[str] = None,
    max_time: Optional[int] = None,
    cuisine: Optional[str] = None,
) -> pd.DataFrame:
    """Narrow recipes by diet, maximum ready time and cuisine."""
    if df.empty:
        return df

    if diet:
        key = diet.strip().lower()
        if key in DIET_FLAGS:
            df = df[df[DIET_FLAGS[key]]]
        else:
            df = df[df['diets'].map(lambda ds: key in [d.lower() for d in ds])]

    if max_time:
        minutes = pd.to_numeric(df['ready_in_minutes'], errors='coerce')
        df = df[minutes <= max_time]

    if cuisine:
        key = cuisine.strip().lower()
        df = df[df['cuisines'].map(lambda cs: key in [c.lower() for c in cs])]

    return df


def rank(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """
    Order recipes by how cookable they are right now.

    Most of your ingredients used first, then fewest missing, then quickest.
    A recipe that uses 4 of yours and needs 1 more beats a "perfect" match
    on one ingredient that needs 9 more.
    """
    if df.empty:
        return df

    df = df.assign(
        match_ratio=df['used_count'] / (df['used_count'] + df['missed_count']).clip(lower=1),
        _minutes=pd.to_numeric(df['ready_in_minutes'], errors='coerce').fillna(10_000),
    )
    df = df.sort_values(
        by=['used_count', 'missed_count', '_minutes'],
        ascending=[False, True, True],
        kind='stable',
    )
    return df.drop(columns='_minutes').head(limit).reset_index(drop=True)


def recommend(
    found: List[Dict],
    details: List[Dict],
    diet: Optional[str] = None,
    max_time: Optional[int] = None,
    cuisine: Optional[str] = None,
    limit: int = 10,
) -> pd.DataFrame:
    """Full pipeline: merge, filter, rank."""
    df = merge_details(found, details)
    df = apply_filters(df, diet=diet, max_time=max_time, cuisine=cuisine)
    return rank(df, limit=limit)
