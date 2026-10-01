"""
Browser entry point. Runs inside Pyodide in a Web Worker.

Fetches through the site's own /api/recipes proxy (which holds the API key),
then hands the raw JSON to recipe_core: the same engine the CLI uses.
"""

import json
from urllib.parse import urlencode

from pyodide.http import pyfetch

import recipe_core


class QuotaExceeded(Exception):
    pass


class ApiError(Exception):
    pass


async def _get(params):
    response = await pyfetch(f'/api/recipes?{urlencode(params)}')
    if response.status in (402, 429):
        raise QuotaExceeded()
    if not response.ok:
        raise ApiError(f'HTTP {response.status}')
    return await response.json()


def parse(text):
    return json.dumps(recipe_core.parse_ingredients(text))


async def search(ingredients_json, diet='', max_time=0, cuisine='', limit=12):
    """Run one search. Returns a JSON string for the UI thread."""
    ingredients = json.loads(ingredients_json)
    filters = recipe_core.search_filters(diet or None, int(max_time) or None, cuisine or None)
    try:
        data = await _get({
            'ingredients': ','.join(ingredients),
            'number': limit * 2,
            **filters,
        })
    except QuotaExceeded:
        return json.dumps({'error': 'quota'})
    except ApiError as e:
        return json.dumps({'error': 'network', 'detail': str(e)})

    df = recipe_core.recommend(
        data.get('results', []),
        diet=diet or None,
        max_time=int(max_time) or None,
        cuisine=cuisine or None,
        limit=limit,
    )
    return json.dumps({
        'recipes': json.loads(df.to_json(orient='records')) if not df.empty else [],
    })
