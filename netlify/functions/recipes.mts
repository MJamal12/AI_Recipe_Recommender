// Thin proxy to Spoonacular. Exists only so the API key never reaches the
// browser; all recipe logic lives in Python (recipe_core.py).

const SEARCH = 'https://api.spoonacular.com/recipes/complexSearch';

const DIETS = new Set(['vegetarian', 'vegan', 'gluten free', 'paleo', 'ketogenic']);
const INTOLERANCES = new Set(['dairy']);

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });

export default async (req: Request) => {
  const key = Netlify.env.get('SPOONACULAR_API_KEY');
  if (!key) return json({ message: 'Server is missing its API key.' }, 500);

  const params = new URL(req.url).searchParams;
  const ingredients = (params.get('ingredients') ?? '').trim().toLowerCase();
  if (!ingredients || ingredients.length > 300) {
    return json({ message: 'Give between 1 and 300 characters of ingredients.' }, 400);
  }

  // One call returns the matches, what each recipe still needs, and its
  // details. Roughly 2 points per search instead of ~13 for a search plus a
  // bulk detail lookup, which matters on a 50 point per day plan.
  const upstream = new URL(SEARCH);
  upstream.searchParams.set('includeIngredients', ingredients);
  upstream.searchParams.set('number', String(Math.min(Math.max(Number(params.get('number')) || 24, 1), 30)));
  upstream.searchParams.set('sort', 'max-used-ingredients');
  upstream.searchParams.set('fillIngredients', 'true');
  upstream.searchParams.set('addRecipeInformation', 'true');
  upstream.searchParams.set('ignorePantry', 'true');

  const diet = params.get('diet');
  if (diet) {
    if (!DIETS.has(diet)) return json({ message: 'Unknown diet.' }, 400);
    upstream.searchParams.set('diet', diet);
  }
  const intolerances = params.get('intolerances');
  if (intolerances) {
    if (!INTOLERANCES.has(intolerances)) return json({ message: 'Unknown intolerance.' }, 400);
    upstream.searchParams.set('intolerances', intolerances);
  }
  const maxReadyTime = params.get('maxReadyTime');
  if (maxReadyTime) {
    if (!/^\d{1,3}$/.test(maxReadyTime)) return json({ message: 'maxReadyTime must be minutes.' }, 400);
    upstream.searchParams.set('maxReadyTime', maxReadyTime);
  }
  const cuisine = params.get('cuisine');
  if (cuisine) {
    if (!/^[a-z ]{1,30}$/.test(cuisine)) return json({ message: 'Unknown cuisine.' }, 400);
    upstream.searchParams.set('cuisine', cuisine);
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
