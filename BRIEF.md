# Brief: AI Recipe Recommender revamp

Source: conversation with Malik, 2026-10-01 (own build, no client).

**Who it's for.** Recruiters and engineers clicking through from Malik's portfolio. Real cooks are a welcome secondary audience, so the tool has to actually work, but the primary reader is someone judging whether Malik can build and ship.

**The one action.** Type what's in your fridge, get recipes ranked by how much of them you can already make.

**Why they'd trust it.** It loads instantly (no Render cold start), the ranking is visibly explained ("uses 4 of 6, missing: garlic, lemon"), and the page shows how it works: the same Python engine from the CLI running in the browser via Pyodide, with a tiny serverless proxy keeping the API key secret.

## Constraints

- Must stay Python. Netlify Functions only run Node/Go, so Python runs client side in Pyodide (WebAssembly CPython). The only non-Python code is a small proxy function that holds the Spoonacular key.
- Host on Netlify, retire Render.
- Spoonacular free tier: 150 points/day. The current Streamlit version spends ~21 calls per search (1 search + 20 detail lookups).
- Design direction: warm editorial food magazine.
- Portfolio (`clients/About_Me`) must be updated to point at the new app, and must contain no em dashes.
