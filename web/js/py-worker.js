// Loads CPython (Pyodide) + pandas off the main thread so the page stays
// responsive while ~10 MB of WebAssembly downloads.
// Module worker: the ESM build is what Pyodide recommends for workers.
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';

// Imported inside the IIFE (not top-level await) so onmessage below is
// registered immediately and early searches queue on `ready` instead of
// being dropped.
const ready = (async () => {
  const started = performance.now();
  const { loadPyodide } = await import(PYODIDE + 'pyodide.mjs');
  // pandas downloads alongside the interpreter, and our two .py files
  // alongside both, instead of one after another.
  const sources = Promise.all(['recipe_core.py', 'pantry_web.py'].map(async (name) => {
    const res = await fetch('/py/' + name);
    if (!res.ok) throw new Error('Could not load ' + name);
    return [name, await res.text()];
  }));
  const py = await loadPyodide({ indexURL: PYODIDE, packages: ['pandas'] });
  for (const [name, text] of await sources) py.FS.writeFile(name, text);
  py.runPython('import pantry_web, sys, pandas');
  const version = py.runPython('sys.version.split()[0]');
  const pandas = py.runPython('pandas.__version__');

  postMessage({
    type: 'ready',
    python: version,
    pandas,
    ms: Math.round(performance.now() - started),
  });
  return py;
})().catch((err) => {
  postMessage({ type: 'boot-error', detail: String(err) });
  throw err;
});

onmessage = async ({ data }) => {
  const py = await ready;
  const web = py.pyimport('pantry_web');
  try {
    if (data.type === 'parse') {
      postMessage({ id: data.id, result: JSON.parse(web.parse(data.text)) });
    } else if (data.type === 'search') {
      const { ingredients, diet, maxTime, cuisine } = data;
      const json = await web.search(JSON.stringify(ingredients), diet, maxTime, cuisine);
      postMessage({ id: data.id, result: JSON.parse(json) });
    }
  } catch (err) {
    postMessage({ id: data.id, result: { error: 'python', detail: String(err) } });
  } finally {
    web.destroy();
  }
};
