# Plan: AI Recipe Recommender on Netlify

## Positioning

"Tell it what's in your fridge. It tells you what you can cook tonight, ranked by what you're missing." Built in Python, running entirely in your browser.

## Architecture (the key change)

```
Browser
  index.html + css + js (UI)
  Web Worker -> Pyodide (CPython 3.12 in WASM) + pandas
      recipe_core.py   parse_ingredients, rank, filter   (shared with CLI)
      web_client.py    pyfetch -> /api/recipes
        |
Netlify Function  /api/recipes  (TypeScript, ~40 lines)
  - whitelists 3 Spoonacular endpoints
  - injects SPOONACULAR_API_KEY from Netlify env (never reaches the browser)
  - CDN-caches identical queries for 24h (saves quota)
```

- **Refactor Python** into `recipe_core.py` (pure logic, no I/O), used by both the CLI (`main.py`, via `requests`) and the web app (via `pyfetch`). One engine, two front ends.
- **Quota fix:** replace the 20 per-recipe detail calls with one `recipes/informationBulk?ids=...` call. A search drops from ~21 API calls to 2.
- **Load time:** Pyodide + pandas start downloading in a Web Worker the moment the page opens, while the visitor types. A small status line shows "Python 3.12 + pandas ready in 2.8s" (real measured value). This turns the cost into a talking point, not a hidden wait.
- **Retire:** `render.yaml`, `gui.py`, `run_gui.py`, Streamlit and Pillow from requirements. The CLI stays.

## Design direction

Warm editorial food magazine: reads like a cookbook page, not a SaaS dashboard.

- **Type** (ui-ux-pro-max "Magazine Style" pairing): Libre Bodoni (headlines, 500/700) + Public Sans (UI/body, 400/600).
- **Palette** (ui-ux-pro-max "Restaurant/Food Service", background warmed to paper):
  - Ink `#450A0A` (text), Tomato `#DC2626` (primary/CTA), Mustard `#A16207` (accent, match meter), Paper `#FBF6EC` (background, replaces the dataset's pinkish `#FEF2F2`), Card `#FFFFFF`, Border `#ECDCCB`, Muted text `#6B4A3A`.
  - Dark mode: espresso `#1C1210` paper, cream text, tomato lightened for contrast. All pairs checked at 4.5:1.
- **Why it fits:** recruiters see a dozen indigo-gradient demo apps. An app that looks like a food magazine reads as deliberate design judgment, and recipe photos from Spoonacular carry the visuals.
- No emoji icons (current app uses them everywhere); inline SVG icons, one stroke weight.

## Sitemap

Single page (`index.html`) plus `404.html`.

1. **Masthead.** Wordmark "Pantry" with the subtitle "AI Recipe Recommender", a link to the portfolio and to GitHub.
2. **Hero / search (the action).** Serif headline "What's in your fridge?". Ingredient chip input: Enter/comma adds a chip, Backspace removes, paste "chicken and rice; garlic" gets parsed by the Python parser. Three sample pantries as one-tap starters. Filters (diet, max time, cuisine) behind a "Refine" disclosure. One primary button: "Find recipes".
3. **Results.** Ranked cards: photo, title, a match meter ("Uses 4 of 6"), the missing ingredients listed by name, time, servings, diet tags, and a link to the full recipe. Skeleton while loading. Empty state that suggests removing a filter. A quota error that is honest ("Daily recipe quota used up, resets at midnight UTC").
4. **How it works** (for engineers). A three-step diagram (browser → Pyodide → proxy), the actual ranking function shown as code (loaded from the same `.py` file the worker runs, so it can't drift), and live stats from the last search: API calls made, time in Python, cache hit or miss.
5. **Footer.** Built by Malik Jamal, links to source and portfolio.

## Tech stack

Static HTML/CSS/vanilla JS (per build standards), Pyodide from the jsDelivr CDN, one Netlify Function in TypeScript. No build step. `netlify.toml` written BOM-free.

## Skills to be used

- `ui-ux-pro-max`: palette and type (done)
- `anthropic-skills:high-end-visual-design`: editorial polish
- `design:ux-copy`: headline, empty, loading and error states
- `anthropic-skills:animate`: chip add/remove and staggered result reveal only
- QA: `design:accessibility-review`, `anthropic-skills:impeccable-frontend-craft`, `anthropic-skills:mobile-native`

## Deploy

- **Repo:** keep `MJamal12/AI_Recipe_Recommender` (history and the portfolio's Source link stay valid). `ship.ps1` is skipped because the repo already exists.
- **Netlify site:** `ai-recipe-recommender-mj` (or the next free name), created by Claude via CLI, badge off.
- **Malik does, one time:** set the API key in Netlify (Claude won't handle the key):
  `netlify env:set SPOONACULAR_API_KEY <key>`, and optionally `netlify init` for push-to-deploy.
- **Shut down the Render service** afterwards (Malik, in the Render dashboard).

## Portfolio changes (`clients/About_Me`)

- Live demo link → the new Netlify URL; delete the "free tier cold start" note.
- Tags: `Python · Pyodide · pandas · Netlify Functions · Spoonacular API` (drop Streamlit, Render).
- Rewrite the card description and the "Read the case" write-up in `js/projects.js` to cover the Render → Pyodide move and the 21 → 2 API call cut.
- New screenshot (`img/recipe-app.webp/.jpg`, same 1440×838) taken from the live site.
- **Em dashes:** remove all 90 across `index.html`, `styles.css`, `js/*.js` and `README.md`. Each one is rewritten to fit its sentence (comma, colon, period, parentheses, or "to" for ranges), not blindly swapped. Verified with a final grep for `—`, `&mdash;` and `&#8212;` showing zero.
- Deploy the portfolio and confirm `state=ready`.

## Assets

- Recipe photos come from Spoonacular at runtime. No stock photography.
- OG image and favicon: generated (a typographic card in the palette).
- Copy: written by Claude, flagged for Malik's review.

## Open questions

- Is "Pantry" OK as the app's display name, or keep "AI Recipe Recommender" as the headline?
- Is your Spoonacular key still valid and under quota? I'll need you to set it in Netlify before the live test.
