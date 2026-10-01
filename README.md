# Pantry: AI Recipe Recommender

Tell it what's in your fridge. It ranks recipes by how much of them you can already make, and tells you exactly what you'd still need to buy.

**Live:** https://ai-recipe-recommender-mj.netlify.app

The recommender is Python and pandas, and it runs entirely in your browser. There is no Python server.

## How it works

```
Browser
  web/ (HTML, CSS, JS)
  Web Worker -> Pyodide (CPython 3.14 compiled to WebAssembly) + pandas
      recipe_core.py   parse, merge, filter, rank        (shared with the CLI)
      pantry_web.py    fetches through /api/recipes
        |
Netlify Function  /api/recipes  (netlify/functions/recipes.mts)
  - allows two Spoonacular endpoints and nothing else
  - adds SPOONACULAR_API_KEY server side, so the key never reaches the browser
  - caches identical searches at Netlify's CDN for 24 hours
```

- **One engine, two front ends.** `recipe_core.py` has no network or file I/O. The command line app (`main.py`) and the web app both import it.
- **2 API calls per search.** The first version made one detail request per recipe, about 21 calls per search against a 150 per day free quota. Details are now fetched with a single `informationBulk` call.
- **Ranking.** Most of your ingredients used first, then fewest missing, then quickest. Having 4 of 6 ingredients beats a "perfect" match on one ingredient that needs 9 more.

## Project layout

```
recipe_core.py          Shared recommendation logic (pure functions, pandas)
api_client.py           Spoonacular client for the CLI (requests)
recipe_recommender.py   CLI orchestration
main.py                 CLI entry point
web/                    The site Netlify publishes
  index.html, 404.html
  css/main.css
  js/app.js             UI thread
  js/py-worker.js       Loads Pyodide + pandas in a Web Worker
  py/pantry_web.py      Browser glue (recipe_core.py is copied in at build time)
netlify/functions/recipes.mts   API key proxy
netlify.toml
```

## Run the web app locally

You need the [Netlify CLI](https://docs.netlify.com/cli/get-started/) and a free [Spoonacular API key](https://spoonacular.com/food-api) in `.env`:

```
SPOONACULAR_API_KEY=your_key_here
```

Then:

```bash
cp recipe_core.py web/py/recipe_core.py
netlify dev
```

`netlify dev` reads `.env` and runs the function locally.

## Run the CLI

```bash
pip install -r requirements.txt
python main.py -i "chicken, rice, tomatoes"
python main.py -i "pasta, cheese, spinach" -d vegetarian -t 30
python main.py -q "chocolate cake" -d gluten-free
```

| Argument | Short | Description |
|----------|-------|-------------|
| `--ingredients` | `-i` | Comma separated list of ingredients |
| `--query` | `-q` | Search by recipe name or type |
| `--number` | `-n` | Number of recipes to return (default 10) |
| `--diet` | `-d` | vegetarian, vegan, paleo, ketogenic, gluten-free, dairy-free |
| `--time` | `-t` | Maximum ready time in minutes |
| `--cuisine` | `-c` | italian, mexican, indian, and so on |
| `--intolerances` | | gluten, dairy, egg, peanut, and so on (name search only) |
| `--no-banner` | | Hide the banner |

## Deploy

The site is on Netlify (it was on Render before). The API key lives in Netlify's environment variables, never in the repo:

```bash
netlify env:set SPOONACULAR_API_KEY your_key_here
netlify deploy --build --prod
```

Once the site is linked to this GitHub repo, `git push` to `main` deploys.

## API limits

The Spoonacular free tier allows 150 points per day. When it runs out, the site says so and explains that it resets at midnight UTC. Searches people have already made keep working from the CDN cache.

## License

MIT. Recipe data from [Spoonacular](https://spoonacular.com/food-api).
