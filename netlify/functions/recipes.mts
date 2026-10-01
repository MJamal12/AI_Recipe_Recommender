// Thin proxy to Spoonacular. Exists only so the API key never reaches the
// browser; all recipe logic lives in Python (recipe_core.py).

const BASE = 'https://api.spoonacular.com/recipes';

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', ...headers },
  });

export default async (req: Request) => {
  const key = Netlify.env.get('SPOONACULAR_API_KEY');
  if (!key) return json({ message: 'Server is missing its API key.' }, 500);

  const params = new URL(req.url).searchParams;
  const op = params.get('op');
  let upstream: URL;

  if (op === 'find') {
    const ingredients = (params.get('ingredients') ?? '').trim();
    const number = Math.min(Math.max(Number(params.get('number')) || 24, 1), 30);
    if (!ingredients || ingredients.length > 300) {
      return json({ message: 'Give between 1 and 300 characters of ingredients.' }, 400);
    }
    upstream = new URL(`${BASE}/findByIngredients`);
    upstream.searchParams.set('ingredients', ingredients.toLowerCase());
    upstream.searchParams.set('number', String(number));
    upstream.searchParams.set('ranking', '1');
    upstream.searchParams.set('ignorePantry', 'true');
  } else if (op === 'bulk') {
    const ids = params.get('ids') ?? '';
    if (!/^\d+(,\d+){0,29}$/.test(ids)) {
      return json({ message: 'ids must be up to 30 comma separated numbers.' }, 400);
    }
    upstream = new URL(`${BASE}/informationBulk`);
    upstream.searchParams.set('ids', ids);
    upstream.searchParams.set('includeNutrition', 'false');
  } else {
    return json({ message: 'Unknown op.' }, 400);
  }

  upstream.searchParams.set('apiKey', key);
  const res = await fetch(upstream, { signal: AbortSignal.timeout(15_000) });
  const body = await res.text();

  // Identical searches are served from Netlify's CDN for a day, so a
  // popular pantry costs the Spoonacular quota once, not every time.
  const cache: Record<string, string> = res.ok
    ? { 'netlify-cdn-cache-control': 'public, s-maxage=86400, stale-while-revalidate=3600, durable' }
    : { 'cache-control': 'no-store' };

  return new Response(body, {
    status: res.status,
    headers: { 'content-type': 'application/json', ...cache },
  });
};

export const config = {
  path: '/api/recipes',
};
