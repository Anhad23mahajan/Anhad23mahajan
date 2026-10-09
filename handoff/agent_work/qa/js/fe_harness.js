// Drives the real static/index.html in jsdom against a live server. Plotly is stubbed (records calls).
// usage: node fe_harness.js BASE_URL
const { JSDOM } = require('jsdom'); const fs = require('fs'); const path = require('path');
const BASE = process.argv[2]; const HTML = fs.readFileSync('/home/user/Anhad23mahajan/lumen/static/index.html', 'utf8');
const DATA = '/home/user/work/qa/fixtures/data/';
async function upload(name, buf) { const fd = new FormData(); fd.append('file', new Blob([buf ?? fs.readFileSync(DATA + name)]), name); const r = await fetch(BASE + '/api/upload', { method: 'POST', body: fd }); return { status: r.status, body: await r.json() }; }
function makeWindow() {
  const errors = []; const plot = { calls: [], purged: 0 };
  const dom = new JSDOM(HTML, { runScripts: 'dangerously', pretendToBeVisual: true, url: BASE + '/',
    beforeParse(w) {
      w.Plotly = { newPlot: (el, d, l) => { plot.calls.push({ el: typeof el === 'string' ? el : el.className, traces: d.length }); }, purge: () => plot.purged++ };
      w.fetch = (p, o) => fetch(BASE + p, o);
      w.addEventListener('error', e => errors.push('window.error: ' + e.message));
      w.addEventListener('unhandledrejection', e => errors.push('unhandledrejection: ' + e.reason));
    } });
  return { w: dom.window, errors, plot };
}
const tick = ms => new Promise(r => setTimeout(r, ms));
const text = w => { const b = w.document.body.cloneNode(true); b.querySelectorAll('script,style').forEach(e => e.remove()); return b.textContent.replace(/\s+/g, ' '); };
(async () => {
  if (process.argv[3] !== 'only5') {
  // ---- T1/T2: stale forecast chart + note after switching dataset
  let { w, errors, plot } = makeWindow(); await tick(200);
  const demo = await (await fetch(BASE + '/api/demo', { method: 'POST' })).json();
  w.render(demo); await tick(2500);
  const noteAfterDemo = w.document.querySelector('#fnote').textContent;
  const inv = await upload('inventory.csv');
  w.render(inv.body); await tick(1500);
  console.log('T2 stale forecast: after demo #fnote =', JSON.stringify(noteAfterDemo.slice(0, 60)), '| after loading inventory (no date col) #fnote =', JSON.stringify(w.document.querySelector('#fnote').textContent.slice(0, 60)), '| #ferr =', JSON.stringify(w.document.querySelector('#ferr').textContent), '| Plotly.purge calls =', plot.purged);
  // ---- T3: date but no metric -> forecast auto-called with empty value
  const nm = await upload('edge_date_no_metric.csv'); w.render(nm.body); await tick(1500);
  console.log('T3 date-no-metric: #ferr =', JSON.stringify(w.document.querySelector('#ferr').textContent), '| #fv options =', w.document.querySelector('#fv').options.length);
  // ---- T4: HTML injection via headers and cells
  const evil = 'date,amount,<img src=x onerror=window.__pwn=1>\n' + Array.from({ length: 12 }, (_, i) => `2025-01-${String(i + 1).padStart(2, '0')},${i + 1},"<script>window.__pwn2=1</script>"`).join('\n') + '\n';
  const ev = await upload('evil.csv', Buffer.from(evil)); w.render(ev.body); await tick(800);
  console.log('T4 injection: <img> elements in DOM =', w.document.querySelectorAll('img').length, '| <script> in preview =', w.document.querySelectorAll('#preview-box script').length, '| window.__pwn =', w.__pwn, w.__pwn2);
  console.log('   errors so far:', errors);
  }
  // ---- T5: every fixture through render(): JS exceptions + junk strings in visible text
  const junk = /NaN|undefined|\[object|Infinity|\bnull\b/;
  const files = fs.readdirSync(DATA).filter(f => !f.startsWith('big_')).sort();
  for (const f of files) {
    const m = makeWindow(); await tick(30);
    const r = await upload(f); if (r.status !== 200) continue;
    try { m.w.render(r.body); } catch (e) { m.errors.push('render threw: ' + e.message); }
    await tick(900);
    const t = text(m.w); const hit = t.match(junk);
    if (m.errors.length || hit) console.log(`T5 ${f.padEnd(32)} ${m.errors.length ? 'ERR ' + m.errors.slice(0, 2).join(' | ') : ''} ${hit ? 'JUNK:' + JSON.stringify(t.slice(Math.max(0, hit.index - 50), hit.index + 30)) : ''}`);
    // (windows intentionally left open: closing mid-fetch throws inside the page's async code)
  }
  console.log('T5 done:', files.length, 'fixtures rendered');
  setTimeout(() => process.exit(0), 100);
})();
