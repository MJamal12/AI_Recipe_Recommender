"""
Browser entry point. Runs inside Pyodide in a Web Worker.

Fetches through the site's own /api/recipes proxy (which holds the API key),
then hands the raw JSON to recipe_core: the same engine the CLI uses.
"""

import json
import time

from pyodide.http import pyfetch

import recipe_core


class QuotaExceeded(Exception):
    pass


class ApiError(Exception):
    pass


async def _get(params):
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    response = await pyfetch(f'/api/recipes?{query}')
    cache = (response.headers.get('cache-status') or '').lower()
    if response.status in (402, 429):
        raise QuotaExceeded()
    if not response.ok:
        raise ApiError(f'HTTP {response.status}')
    return await response.json(), 'hit' in cache


def parse(text):
    return json.dumps(recipe_core.parse_ingredients(text))


async def search(ingredients_json, diet='', max_time=0, cuisine='', limit=12):
    """Run one search. Returns a JSON string for the UI thread."""
    from urllib.parse import quote

    ingredients = json.loads(ingredients_json)
    stats = {'api_calls': 0, 'cache_hits': 0}
    try:
        found, hit = await _get({
            'op': 'find',
            'ingredients': quote(','.join(ingredients)),
            'number': limit * 2,
        })
        stats['api_calls'] += 1
        stats['cache_hits'] += hit

        details = []
        if found:
            details, hit = await _get({
                'op': 'bulk',
                'ids': ','.join(str(r['id']) for r in found),
            })
            stats['api_calls'] += 1
            stats['cache_hits'] += hit

        started = time.perf_counter()
        df = recipe_core.recommend(
            found,
            details,
            diet=diet or None,
            max_time=int(max_time) or None,
            cuisine=cuisine or None,
            limit=limit,
        )
        stats['python_ms'] = round((time.perf_counter() - started) * 1000, 1)
        stats['candidates'] = len(found)
    except QuotaExceeded:
        return json.dumps({'error': 'quota'})
    except ApiError as e:
        return json.dumps({'error': 'network', 'detail': str(e)})

    return json.dumps({
        'recipes': json.loads(df.to_json(orient='records')) if not df.empty else [],
        'stats': stats,
    })
