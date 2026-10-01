// UI thread. All recipe logic runs in Python inside js/py-worker.js.
(() => {
  const $ = (sel) => document.querySelector(sel);
  const form = $('#search');
  const box = $('#chips-box');
  const list = $('#chips');
  const input = $('#ingredient-input');
  const error = $('#ingredient-error');
  const submit = $('#submit');
  const submitLabel = submit.querySelector('.cta__label');
  const runtime = $('#runtime');
  const runtimeText = $('#runtime-text');
  const results = $('#results');
  const cards = $('#cards');
  const summary = $('#results-summary');
  const status = $('#results-status');
  const filters = { diet: $('#diet'), time: $('#time'), cuisine: $('#cuisine') };
  const tpl = $('#card-tpl');
  const chipStatus = $('#chip-status');

  let ingredients = [];
  let pyReady = false;
  let busy = false;

  // Python worker
  const worker = new Worker('/js/py-worker.js', { type: 'module' });
  const pending = new Map();
  let nextId = 0;

  const ask = (msg) => new Promise((resolve) => {
    const id = ++nextId;
    pending.set(id, resolve);
    worker.postMessage({ ...msg, id });
  });

  worker.onmessage = ({ data }) => {
    if (data.type === 'ready') {
      pyReady = true;
      runtime.hidden = true;
      if (busy) {
        submitLabel.textContent = 'Finding recipes...';
        summary.textContent = `Matching ${list2(ingredients)}`;
      }
      return;
    }
    if (data.type === 'boot-error') {
      runtime.classList.add('is-error');
      runtimeText.textContent = "Pantry couldn't start in this browser. Try reloading the page.";
      return;
    }
    const resolve = pending.get(data.id);
    if (resolve) { pending.delete(data.id); resolve(data.result); }
  };

  // Mirrors recipe_core.parse_ingredients so chips appear instantly,
  // even before Python has finished loading.
  const quickParse = (text) => {
    const out = [];
    for (const part of text.split(/\s*(?:,|;|\n|\band\b|&|\+)\s*/i)) {
      const name = part.toLowerCase().split(/\s+/).filter(Boolean).join(' ');
      if (name && !out.includes(name)) out.push(name);
    }
    return out;
  };

  // Chips
  const setError = (msg) => {
    error.textContent = msg;
    error.hidden = !msg;
    box.setAttribute('aria-invalid', msg ? 'true' : 'false');
  };

  const renderChip = (name) => {
    const li = document.createElement('li');
    li.className = 'chip';
    li.dataset.name = name;
    li.append(name);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip__remove';
    btn.setAttribute('aria-label', `Remove ${name}`);
    btn.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-x"/></svg>';
    btn.addEventListener('click', () => removeChip(name, true));
    li.append(btn);
    list.append(li);
  };

  const syncPlaceholder = () => {
    input.placeholder = ingredients.length ? 'Add another' : 'chicken, rice, garlic';
  };

  const addFrom = (text) => {
    const added = quickParse(text).filter((n) => !ingredients.includes(n));
    for (const name of added) { ingredients.push(name); renderChip(name); }
    if (added.length) {
      setError('');
      chipStatus.textContent = `Added ${list2(added)}. ${ingredients.length} ingredient${ingredients.length === 1 ? '' : 's'} in your list.`;
    }
    syncPlaceholder();
    return added.length;
  };

  const removeChip = (name, refocus) => {
    ingredients = ingredients.filter((n) => n !== name);
    chipStatus.textContent = `Removed ${name}.`;
    syncPlaceholder();
    const li = list.querySelector(`[data-name="${CSS.escape(name)}"]`);
    if (!li) return;
    li.classList.add('is-leaving');
    const done = () => li.remove();
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) done();
    else li.addEventListener('transitionend', done, { once: true });
    setTimeout(done, 250);
    if (refocus) input.focus();
  };

  const clearChips = () => { ingredients = []; list.replaceChildren(); syncPlaceholder(); };

  box.addEventListener('click', (e) => { if (e.target === box) input.focus(); });

  input.addEventListener('keydown', (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.value.trim()) {
      e.preventDefault();
      addFrom(input.value);
      input.value = '';
    } else if (e.key === 'Enter' && !input.value.trim()) {
      // Empty input + Enter submits the search.
    } else if (e.key === 'Backspace' && !input.value && ingredients.length) {
      removeChip(ingredients[ingredients.length - 1], false);
    }
  });
  input.addEventListener('input', () => {
    if (/[,;\n]/.test(input.value)) {
      const parts = input.value.split(/[,;\n]/);
      const rest = parts.pop();
      addFrom(parts.join(','));
      input.value = rest.trimStart();
    }
  });
  input.addEventListener('blur', () => {
    if (input.value.trim()) { addFrom(input.value); input.value = ''; }
  });

  document.querySelectorAll('.starter').forEach((btn) => {
    btn.addEventListener('click', () => {
      clearChips();
      addFrom(btn.dataset.fill);
      form.requestSubmit();
    });
  });

  // Filters
  const refineCount = $('#refine-count');
  const updateRefineCount = () => {
    const n = Object.values(filters).filter((f) => f.value && f.value !== '0').length;
    refineCount.textContent = n ? String(n) : '';
  };
  Object.values(filters).forEach((f) => f.addEventListener('change', updateRefineCount));

  // Results
  const IMG_SIZE = /-\d+x\d+\.(jpe?g|png)$/i;
  const sized = (url, size) => (url && IMG_SIZE.test(url) ? url.replace(IMG_SIZE, `-${size}.$1`) : url);
  const list2 = (arr) => arr.length < 2 ? arr.join('') :
    `${arr.slice(0, -1).join(', ')} and ${arr[arr.length - 1]}`;

  const renderSkeleton = () => {
    cards.replaceChildren();
    for (let i = 0; i < 3; i++) {
      const li = document.createElement('li');
      li.className = 'card skeleton';
      li.style.setProperty('--i', i);
      li.setAttribute('aria-hidden', 'true');
      li.innerHTML = '<div class="card__media"><img alt="" width="556" height="370"></div>' +
        '<div class="card__body"><span class="sk-line is-short"></span><span class="sk-line is-title"></span>' +
        '<span class="sk-line"></span><span class="sk-line is-short"></span></div>';
      cards.append(li);
    }
  };

  const renderNotice = (title, body, action) => {
    const li = document.createElement('li');
    li.className = 'notice';
    li.innerHTML = '<h3></h3><p></p>';
    li.querySelector('h3').textContent = title;
    li.querySelector('p').textContent = body;
    if (action) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'text-btn';
      btn.textContent = action.label;
      btn.addEventListener('click', action.run);
      li.append(btn);
    }
    cards.replaceChildren(li);
  };

  const renderCard = (r, i) => {
    const node = tpl.content.firstElementChild.cloneNode(true);
    node.style.setProperty('--i', i);
    const total = r.used_count + r.missed_count;

    const media = node.querySelector('.card__media');
    const img = media.querySelector('img');
    media.href = r.source_url;
    if (r.image) {
      img.src = sized(r.image, i === 0 ? '636x393' : '556x370');
      img.srcset = `${sized(r.image, '312x231')} 312w, ${sized(r.image, '556x370')} 556w, ${sized(r.image, '636x393')} 636w`;
      img.sizes = i === 0 ? '(max-width: 640px) 100vw, 640px' : '(max-width: 640px) 100vw, 400px';
      if (i === 0) { img.loading = 'eager'; img.fetchPriority = 'high'; }
      // Not every size exists for every recipe: retry the original, then give up gracefully.
      img.addEventListener('error', () => {
        if (img.src !== r.image) { img.srcset = ''; img.src = r.image; }
        else media.classList.add('is-missing');
      });
    } else {
      media.classList.add('is-missing');
    }

    node.querySelector('.card__rank').textContent = `No. ${String(i + 1).padStart(2, '0')}`;
    const link = node.querySelector('.card__link');
    link.href = r.source_url;
    link.textContent = r.title;

    const meter = node.querySelector('.meter');
    meter.setAttribute('aria-label', `Uses ${r.used_count} of ${total} ingredients from your list`);
    for (let k = 0; k < Math.min(total, 12); k++) {
      const seg = document.createElement('span');
      if (k < Math.round((r.used_count / total) * Math.min(total, 12))) seg.className = 'is-have';
      meter.append(seg);
    }

    node.querySelector('.card__match').textContent =
      r.missed_count === 0 ? `You have all ${total} ingredients`
        : `You have ${r.used_count} of ${total} ingredients`;

    const need = node.querySelector('.card__need');
    if (r.missed_count) {
      // Long lists get trimmed; the count above still reflects all of them.
      const shown = r.missed_names.slice(0, 5);
      const more = r.missed_count - shown.length;
      need.append('Still need: ');
      const strong = document.createElement('strong');
      strong.textContent = !shown.length ? `${more} ingredient${more === 1 ? '' : 's'}`
        : more > 0 ? `${shown.join(', ')} and ${more} more` : list2(shown);
      need.append(strong);
    } else {
      need.textContent = 'Nothing to buy.';
    }

    const time = node.querySelector('.card__time');
    if (r.ready_in_minutes) time.querySelector('span').textContent = `${r.ready_in_minutes} min`;
    else time.hidden = true;
    const serves = node.querySelector('.card__serves');
    if (r.servings) serves.querySelector('span').textContent = `Serves ${r.servings}`;
    else serves.hidden = true;

    const tags = node.querySelector('.card__tags');
    for (const tag of [...(r.diets || []).slice(0, 3), ...(r.cuisines || []).slice(0, 1)]) {
      const li = document.createElement('li');
      li.textContent = tag;
      tags.append(li);
    }
    return node;
  };

  // Deep links: ?i=chicken,rice&diet=vegan&time=30&cuisine=Italian
  const syncUrl = () => {
    const p = new URLSearchParams();
    if (ingredients.length) p.set('i', ingredients.join(','));
    if (filters.diet.value) p.set('diet', filters.diet.value);
    if (filters.time.value !== '0') p.set('time', filters.time.value);
    if (filters.cuisine.value) p.set('cuisine', filters.cuisine.value);
    history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
  };

  const setBusy = (on) => {
    busy = on;
    submit.setAttribute('aria-busy', String(on));
    submit.disabled = on;
    submitLabel.textContent = on ? (pyReady ? 'Finding recipes...' : 'Getting ready...') : 'Find recipes';
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (busy) return;
    if (input.value.trim()) { addFrom(input.value); input.value = ''; }
    if (!ingredients.length) {
      setError('Add at least one ingredient to search. Try "eggs" or one of the sample fridges.');
      input.focus();
      return;
    }

    syncUrl();
    setBusy(true);
    results.hidden = false;
    summary.textContent = pyReady ? `Matching ${list2(ingredients)}`
      : `Matching ${list2(ingredients)}. Getting ready, this only takes a moment on your first visit.`;
    renderSkeleton();
    results.scrollIntoView({ block: 'start' });

    const res = await ask({
      type: 'search',
      ingredients: await ask({ type: 'parse', text: ingredients.join(',') }),
      diet: filters.diet.value,
      maxTime: Number(filters.time.value),
      cuisine: filters.cuisine.value,
    });
    setBusy(false);

    if (res.error === 'quota') {
      renderNotice('The kitchen is closed for today',
        "Pantry has used up its free daily recipe quota from Spoonacular. It resets at midnight UTC. Searches people have already made still work, so the sample fridges may load.");
      status.textContent = 'Daily recipe quota used up.';
    } else if (res.error) {
      renderNotice("Couldn't reach the recipe service",
        'Check your connection and try again. If it keeps happening, the recipe service may be down for a moment.',
        { label: 'Try again', run: () => form.requestSubmit() });
      status.textContent = 'Search failed.';
    } else if (!res.recipes.length) {
      const filtered = Object.values(filters).some((f) => f.value && f.value !== '0');
      renderNotice('No recipes match yet',
        filtered ? 'Your filters ruled out every match. Loosen one and search again.'
          : 'Try adding a staple like onion, eggs or rice. More ingredients give the ranking more to work with.',
        filtered ? { label: 'Clear filters and search', run: () => {
          Object.values(filters).forEach((f) => { f.selectedIndex = 0; });
          updateRefineCount();
          form.requestSubmit();
        } } : null);
      status.textContent = 'No recipes found.';
    } else {
      cards.replaceChildren(...res.recipes.map(renderCard));
      const n = res.recipes.length;
      summary.textContent = `${n} recipe${n === 1 ? '' : 's'}, best match first`;
      status.textContent = `Found ${n} recipes.`;
    }
    $('#results-title').focus({ preventScroll: true });
  });

  // Restore a shared search.
  const params = new URLSearchParams(location.search);
  if (params.get('i')) {
    addFrom(params.get('i'));
    for (const key of ['diet', 'time', 'cuisine']) {
      const v = params.get(key);
      if (v && [...filters[key].options].some((o) => o.value === v)) filters[key].value = v;
    }
    updateRefineCount();
    form.requestSubmit();
  }
})();
