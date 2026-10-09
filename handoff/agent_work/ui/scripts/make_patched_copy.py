"""Build /home/user/work/ui/lumen-patched (copy of the repo, NOT the repo) with all proposed fixes applied, and write the
unified diffs to snippets/.  Every replacement asserts it matched exactly once, so if Harsh restyles index.html the script
fails loudly instead of silently producing a different file.

Run: /home/user/work/venv/bin/python -I /home/user/work/ui/scripts/make_patched_copy.py
"""
import shutil, pathlib, subprocess, re, sys

SRC = pathlib.Path('/home/user/Anhad23mahajan/lumen')
DST = pathlib.Path('/home/user/work/ui/lumen-patched')
UI = pathlib.Path('/home/user/work/ui')
if DST.exists(): shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))

orig = (SRC / 'static/index.html').read_text()
h = orig

def sub(old, new, count=1):
    global h
    n = h.count(old)
    assert n == count, f'expected {count} match(es), found {n} for: {old[:90]!r}'
    h = h.replace(old, new)

def sub_re(pattern, new, flags=re.S):
    global h
    m = re.search(pattern, h, flags); assert m, f'no regex match: {pattern[:80]!r}'
    h = h[:m.start()] + new + h[m.end():]

# ======================================================================== HEAD: vendored assets, favicon, fixes.css
sub('''  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link
    href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Figtree:wght@400;500;600&display=swap"
    rel="stylesheet">
  <script src="https://cdn.plot.ly/plotly-basic-2.35.2.min.js"></script>
''', '''  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 26 26'%3E%3Ccircle cx='13' cy='13' r='12' fill='%23083F40'/%3E%3Ccircle cx='13' cy='13' r='10' fill='none' stroke='%239CC7C4' stroke-width='2'/%3E%3Ccircle cx='13' cy='13' r='5' fill='%23E8A33D'/%3E%3C/svg%3E">
  <meta name="description" content="Upload a spreadsheet. Lumen finds the trends and odd spots, answers questions in plain English and suggests next steps. Private by default: your file stays in memory.">
  <link rel="preload" href="/assets/vendor/fonts/figtree-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/vendor/fonts/bricolage-grotesque-latin-opsz-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/assets/vendor/fonts.css">
  <script src="/assets/vendor/plotly-basic-2.35.2.min.js" defer></script>
''')
sub('  </style>\n</head>', '  </style>\n  <link rel="stylesheet" href="/assets/lumen-fixes.css">\n</head>')

# ======================================================================== HTML: aria on tabs / live regions / maxlength / tabpanel
sub('<div class="tabs">\n            <button class="tab" id="tab-raw">Raw Input</button>\n            <button class="tab active" id="tab-processed">Cleaned Output</button>\n          </div>\n          <div class="preview-table" id="preview-box"></div>',
    '<div class="tabs" role="tablist" aria-label="Data preview">\n            <button class="tab" id="tab-raw" role="tab" aria-selected="false" aria-controls="preview-box" tabindex="-1">Raw Input</button>\n            <button class="tab active" id="tab-processed" role="tab" aria-selected="true" aria-controls="preview-box">Cleaned Output</button>\n          </div>\n          <div class="preview-table" id="preview-box" role="tabpanel" aria-labelledby="tab-processed" tabindex="0"></div>')
sub('<div class="answer" id="ans"></div>', '<div class="answer" id="ans" aria-live="polite"></div>')
sub('<input id="q" placeholder="e.g. Which product sold the most last quarter?"\n              aria-label="Question">', '<input id="q" placeholder="e.g. Which product sold the most last quarter?"\n              aria-label="Question" maxlength="500" autocomplete="off">')
sub('<p class="sub" id="fsub">', '<p class="sub" id="fsub">')
sub('<div class="summary">\n          <h3>What matters most</h3>', '<div class="summary">\n          <h3 id="sumh" tabindex="-1">What matters most</h3>')

# ======================================================================== JS: helpers (fmt, esc, api, busy)
sub_re(r"const fmt = n => \{.*?\};\n    const esc", '''const fmt = n => {
      if (n == null || n === '' || !Number.isFinite(+n)) return '–'; n = +n; const a = Math.abs(n), s = n < 0 ? '-' : '';
      if (a >= 999.5e6) { const v = a / 1e9; return s + v.toFixed(v >= 10 ? 0 : 1) + 'B' }
      if (a >= 999.5e3) { const v = a / 1e6; return s + v.toFixed(v >= 10 ? 0 : 1) + 'M' }
      if (a >= 1e4) return s + Math.round(a / 1e3) + 'k';
      if (a >= 1e3) { const v = +(a / 1e3).toFixed(1); return s + (v >= 10 ? Math.round(a / 1e3) : v.toFixed(1)) + 'k' }
      if (Number.isInteger(n)) return String(n);
      if (a < 1) return String(+n.toPrecision(3));            // rates / ratios: 0.0536 stays 0.0536 (was "0.1")
      const r = +a.toFixed(1); return r >= 1000 ? s + '1.0k' : s + r.toFixed(1);
    };
    const full = n => n == null || !Number.isFinite(+n) ? '–' : (+n).toLocaleString(undefined, { maximumFractionDigits: Math.abs(n) < 1 ? 4 : Math.abs(n) < 100 ? 2 : 0 });  // exact value for hovers and big answers
    const day = v => (typeof v === 'string' && /^\\d{4}-\\d{2}-\\d{2}T00:00:00$/.test(v)) ? v.slice(0, 10) : v;
    const cellv = v => v == null ? '' : typeof v === 'number' ? (Number.isInteger(v) ? String(v) : String(+v.toFixed(4))) : day(v);   // faithful: a preview must not round
    const nice = d => /datetime|date/i.test(d) ? 'date' : /bool/i.test(d) ? 'yes / no' : /int|float|decimal/i.test(d) ? 'number' : 'text';
    const hasPlotly = () => typeof Plotly !== 'undefined';
    const NOPLOT = 'Charts need the plotting library, which could not load (offline or blocked). The numbers and findings still work.';
    const esc''')
sub('''const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));''',
    '''const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));''')
sub_re(r"async function api\(p, o\) \{.*?\}\n    const busy = \(el, on\) => el\.classList\.toggle\('busy', on\);", '''async function api(p, o) {
      let r; try { r = await fetch(p, o) } catch (e) { throw new Error('Cannot reach the Lumen server. Check your connection and try again.') }
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        let d = j.detail; if (Array.isArray(d)) d = d.map(x => x.msg || '').filter(Boolean).join('; ');   // FastAPI 422 returns a list: was shown as "[object Object]"
        d = String(d || ''); const expired = /session expired/i.test(d);
        const err = new Error(expired ? 'Your session expired (the server restarted or timed out). Choose your file again to continue.' : (d || (r.status >= 500 ? 'The server had a problem. Please try again.' : 'Something went wrong. Try again.')));
        err.expired = expired; throw err
      }
      return j
    }
    const busy = (el, on) => { el.classList.toggle('busy', on); el.setAttribute('aria-busy', on); if ('disabled' in el) el.disabled = on; if (el.id === 'drop') el.querySelectorAll('button').forEach(b => b.disabled = on) };''')

# ======================================================================== JS: load / upload (sequence guard, drop guard, focus)
sub_re(r"async function load\(p\) \{.*?\n    \}\n    const send =", '''let loadSeq = 0;
    async function load(p) {
      const my = ++loadSeq;
      $('#uerr').textContent = ''; busy($('#drop'), true); $('#uerr').style.color = '#586674'; $('#uerr').innerHTML = '<span class="spin"></span>Reading your data…';
      try { const d = await p; if (my !== loadSeq) return; $('#uerr').textContent = ''; render(d) } catch (e) { if (my !== loadSeq) return; $('#uerr').style.color = ''; $('#uerr').textContent = e.message; $('#file').value = '' } finally { if (my === loadSeq) busy($('#drop'), false) }
    }
    const send =''')
sub("$('#file').onchange = e => send(e.target.files[0]);", "$('#file').onchange = e => { send(e.target.files[0]); };")
sub("drop.addEventListener('drop', e => send(e.dataTransfer.files[0]));",
    "drop.addEventListener('drop', e => send(e.dataTransfer.files[0]));\n    // dropping a file anywhere else would make the browser navigate away to the file and lose the session\n    ['dragover', 'drop'].forEach(t => window.addEventListener(t, e => { if (!e.target.closest || !e.target.closest('#drop')) e.preventDefault() }));")
sub("$('#again').onclick = () => { $('#app').style.display = 'none'; $('#hero').style.display = 'grid'; $('#again').style.display = 'none'; $('#file').value = '' };",
    "$('#again').onclick = () => { $('#app').style.display = 'none'; $('#hero').style.display = 'grid'; $('#again').style.display = 'none'; $('#file').value = ''; $('#q').value = ''; $('#ans').innerHTML = ''; $('#uerr').textContent = ''; askSeq++; asking = false; busy($('#go'), false); window.scrollTo(0, 0); $('#demo').focus() };")

# ======================================================================== JS: charts
sub('''const ht = c.freq === 'D' ? '%{x|%d %b %Y}: %{y:,.0f}<extra></extra>' : '%{x|%b %Y}: %{y:,.0f}<extra></extra>';''',
    '''const ht = c.freq === 'D' ? '%{x|%d %b %Y}: %{text}<extra></extra>' : '%{x|%b %Y}: %{text}<extra></extra>';''')
sub("mode: 'lines', line: { color: C.teal, width: 2.5, shape: 'spline', smoothing: .4 }, fill: 'tozeroy', fillcolor: 'rgba(14,107,107,.09)', hovertemplate: ht },",
    "mode: 'lines', text: y.map(full), line: { color: C.teal, width: 2.5, shape: 'spline', smoothing: .4 }, fill: 'tozeroy', fillcolor: 'rgba(14,107,107,.09)', hovertemplate: ht },")
sub_re(r"function barH\(el, x, y\) \{.*?\n    \}\n\n    function render", '''function barH(el, x, y) {
      // handles: negatives (axis now spans below zero), long labels (truncated, full label on hover; ticks are index-based so
      // truncated duplicates cannot merge), nulls, empty input
      if (!x.length) { el.innerHTML = '<p class="note">No rows to chart.</p>'; return }
      const vals = y.map(v => v == null || !Number.isFinite(+v) ? null : +v), nums = vals.filter(v => v != null);
      const mx = Math.max(0, ...nums), mn = Math.min(0, ...nums), pad = (mx - mn) * .18 || 1;
      const lim = (el.clientWidth || 600) < 520 ? 18 : 30, lab = x.map(s => String(s ?? '(blank)')), short = lab.map(s => s.length > lim ? s.slice(0, lim - 1) + '…' : s);
      Plotly.newPlot(el, [{ type: 'bar', orientation: 'h', y: lab.map((_, i) => i), x: vals, marker: { color: vals.map((v, i) => v != null && v < 0 ? C.amber : i === 0 ? C.teal : C.light) },
        text: vals.map(fmt), textposition: 'outside', cliponaxis: false, hovertext: lab.map((l, i) => l + ': ' + full(vals[i])), hoverinfo: 'text' }],
        lay({ xaxis: { showgrid: false, showticklabels: false, zeroline: true, zerolinecolor: C.rule, range: [mn < 0 ? mn - pad : 0, mx > 0 ? mx + pad : pad] },
          yaxis: { autorange: 'reversed', tickmode: 'array', tickvals: lab.map((_, i) => i), ticktext: short, gridcolor: 'rgba(0,0,0,0)', linecolor: C.rule }, rest: { showlegend: false, margin: { l: 90, r: 30, t: 6, b: 10 } } }), cfg)
    }

    function render''')

# ======================================================================== JS: render()
sub("sid = d.session_id; $('#hero').style.display = 'none';", "sid = d.session_id; askSeq++; asking = false; busy($('#go'), false); $('#q').value = ''; document.querySelectorAll('#charts .js-plotly-plot, #fchart.js-plotly-plot, #rc').forEach(g => { try { hasPlotly() && Plotly.purge(g) } catch (e) { } }); $('#hero').style.display = 'none';")
sub("$('#recs').innerHTML = d.narrative.recommendations.map(r => `<li>${esc(r)}</li>`).join('');", "$('#recs').innerHTML = [...new Set(d.narrative.recommendations)].map(r => `<li>${esc(r)}</li>`).join('');")
sub("""${k.kind === 'int' ? k.value.toLocaleString() : fmt(k.value)}</strong>${k.delta != null ? `<em class="${k.delta >= 0 ? 'up' : 'down'}">${k.delta >= 0 ? '+' : ''}${k.delta.toFixed(0)}% <span""",
    """${k.kind === 'int' ? k.value.toLocaleString() : fmt(k.value)}</strong>${k.delta != null ? `<em class="${Math.round(k.delta) > 0 ? 'up' : Math.round(k.delta) < 0 ? 'down' : ''}">${Math.round(k.delta) > 0 ? '+' : ''}${Math.round(k.delta)}% <span""")
sub('''<div class="kpi"><small>${esc(k.label)}</small><strong>''', '''<div class="kpi"><small>${esc(k.label)}</small><strong title="${esc(k.kind === 'int' ? k.value.toLocaleString() : full(k.value))}">''')
sub("""$('#qerr').textContent = d.ai ? '' : 'Questions are switched off: add a GEMINI_API_KEY on the server. Everything else works without it.'; $('#ans').innerHTML = '';""",
    """$('#qerr').classList.toggle('info', !d.ai); $('#qerr').textContent = d.ai ? '' : 'Questions are switched off on this server (no Gemini API key). Everything else works without it.'; $('#ans').innerHTML = '';""")
sub("""$('#fgo').disabled = !p.date_cols.length; $('#ferr').textContent = p.date_cols.length ? '' : 'Forecasting needs a date column, and none was found.';""",
    """const canFc = p.date_cols.length && p.metric_cols.length; $('#fgo').disabled = !canFc; $('#ferr').textContent = canFc ? '' : (p.date_cols.length ? 'Forecasting needs a numeric measure, and none was found.' : 'Forecasting needs a date column, and none was found.');""")
# preview: friendly dtypes + dates/bools + tab aria + arrow keys
sub("""<br><small style="color:var(--muted);font-weight:normal">${esc(pv.dtypes[i])}</small></th>`).join('')""", """<br><small style="color:var(--muted);font-weight:normal" title="${esc(pv.dtypes[i])}">${esc(nice(pv.dtypes[i]))}</small></th>`).join('')""")
sub("""h += pv.rows.map(r => `<tr>` + r.map(v => `<td title="${esc(v)}">${esc(v)}</td>`).join('') + `</tr>`).join('');""",
    """h += pv.rows.map(r => `<tr>` + r.map((v, ci) => { const t = /bool/i.test(pv.dtypes[ci]) && (v === 0 || v === 1) ? (v ? 'Yes' : 'No') : cellv(v); return `<td title="${esc(t)}">${esc(t)}</td>` }).join('') + `</tr>`).join('');""")
sub("""$('#tab-raw').className = isRaw ? 'tab active' : 'tab';
        $('#tab-processed').className = !isRaw ? 'tab active' : 'tab';""",
    """$('#tab-raw').className = isRaw ? 'tab active' : 'tab'; $('#tab-raw').setAttribute('aria-selected', isRaw); $('#tab-raw').tabIndex = isRaw ? 0 : -1;
        $('#tab-processed').className = !isRaw ? 'tab active' : 'tab'; $('#tab-processed').setAttribute('aria-selected', !isRaw); $('#tab-processed').tabIndex = !isRaw ? 0 : -1;
        $('#preview-box').setAttribute('aria-labelledby', isRaw ? 'tab-raw' : 'tab-processed');""")
sub("""        $('#tab-raw').onclick = () => showPreview('raw');
        $('#tab-processed').onclick = () => showPreview('processed');""",
    """        $('#tab-raw').onclick = () => showPreview('raw');
        $('#tab-processed').onclick = () => showPreview('processed');
        document.querySelector('.tabs').onkeydown = e => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { const raw = e.key === 'ArrowLeft'; showPreview(raw ? 'raw' : 'processed'); $(raw ? '#tab-raw' : '#tab-processed').focus() } };""")
# charts: figure/figcaption wrapper, a11y labels, plotly-missing guard
sub_re(r"requestAnimationFrame\(\(\) => requestAnimationFrame\(\(\) => \{\n        d\.charts\.forEach\(c => \{.*?\n        if \(p\.date_cols\.length\) runForecast\(\)\n      \}\)\)",
'''requestAnimationFrame(() => requestAnimationFrame(() => {
        if (!hasPlotly()) { $('#charts').innerHTML = `<p class="note" style="grid-column:1/-1">${NOPLOT}</p>`; $('#ferr').textContent = NOPLOT; return }
        d.charts.forEach(c => {
          const cell = document.createElement('figure'); cell.className = 'cell' + (c.type === 'line' ? ' wide' : '');
          const t = document.createElement('figcaption'); t.className = 'note'; t.textContent = c.title; cell.appendChild(t);
          const el = document.createElement('div'); el.className = 'chart'; el.setAttribute('role', 'img');
          const lo = Math.min(...c.y), hi = Math.max(...c.y);
          el.setAttribute('aria-label', `${c.title}. ${c.type === 'line' ? `${c.y.length} points from ${fmt(c.y[0])} to ${fmt(c.y[c.y.length - 1])}, peak ${fmt(hi)}, low ${fmt(lo)}.` : `Top: ${c.x[0]} (${fmt(c.y[0])}); ${c.x.length} categories.`}`);
          cell.appendChild(el); $('#charts').appendChild(cell); c.type === 'line' ? lineChart(el, c) : barH(el, c.x, c.y);
        });
        if (p.date_cols.length && p.metric_cols.length) runForecast();
        const h3 = $('#sumh'); if (h3) h3.focus({ preventScroll: true });
      }))''')

# ======================================================================== JS: ask()
sub_re(r"async function ask\(\) \{.*?\n    \$\('#go'\)\.onclick = ask; \$\('#q'\)\.onkeydown = e => \{ if \(e\.key === 'Enter'\) ask\(\) \};",
r'''let askSeq = 0, asking = false, askingQ = '';
    async function ask() {
      const q = $('#q').value.trim(); if (!q || (asking && q === askingQ)) return;   // ignore key-repeat / double submit of the SAME question; a different question supersedes the one in flight
      const my = ++askSeq; asking = true; askingQ = q;
      $('#qerr').textContent = ''; busy($('#go'), true); $('#ans').innerHTML = '<p class="note"><span class="spin"></span>Working it out…</p>';
      try {
        const r = await api('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sid, question: q }) });
        if (my !== askSeq) return;                                   // a newer question / dataset replaced this one: drop the stale answer
        const cols = r.columns || [], rows = r.rows || [], ch = r.chart || {}, first = rows[0] || [];
        const single = rows.length === 1 && (ch.type === 'number' || cols.length === 1);
        let html = `<span class="badge ${r.verified ? 'ok' : 'chk'}">${r.verified ? 'Answer checked against the data' : 'Please double-check this one'}</span>`;
        if (single) {
          let bi = cols.indexOf(ch.y); if (bi < 0 || typeof first[bi] !== 'number') bi = first.findIndex(v => typeof v === 'number');
          const li = first.findIndex((v, i) => i !== bi && typeof v === 'string');
          const v = bi >= 0 ? first[bi] : first[0];
          html += `<div class="big">${bi >= 0 ? (v == null ? '–' : Math.abs(v) >= 1e9 ? fmt(v) : full(v)) : (esc(day(v)) || '–')}</div>`;   // exact value; was fmt() => "9.0k" for 9,046
          if (li >= 0) html += `<div class="biglabel">${esc(cols[li])}: ${esc(day(first[li]))}</div>`;
        }
        html += `<p class="a">${esc(r.answer)}</p>`; if (r.caveats) html += `<p class="note">${esc(r.caveats)}</p>`;
        const plottable = ['bar', 'line', 'pie'].includes(ch.type) && cols.indexOf(ch.x) >= 0 && cols.indexOf(ch.y) >= 0 && rows.length > 0;
        if (!single && plottable) html += '<div id="rc" class="chart" role="img" style="height:300px"></div>';
        const showAll = ch.type === 'table' || (!single && !plottable);                       // table answers: show the table, do not hide it in a collapsed <details>
        html += `<details${showAll ? ' open' : ''}><summary>${showAll ? 'Result table and how this was worked out' : 'How this was worked out'}</summary><pre>${esc(r.sql)}</pre><div style="overflow:auto"><table><tr>${cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr>${rows.slice(0, 50).map(x => `<tr>${x.map(v => `<td>${esc(cellv(v))}</td>`).join('')}</tr>`).join('')}</table></div>${rows.length > 50 ? `<p class="note">Showing the first 50 of ${rows.length.toLocaleString()} rows.</p>` : ''}</details>`;
        $('#ans').innerHTML = html; if (single || !plottable) return;
        const xi = cols.indexOf(ch.x), yi = cols.indexOf(ch.y);
        const x = rows.map(r => r[xi]), y = rows.map(r => r[yi]); const isDate = /^\d{4}-\d{2}-\d{2}/.test(String(x[0]));
        const rc = $('#rc'); rc.setAttribute('aria-label', `${ch.type} chart: ${cols[yi]} by ${cols[xi]}, ${rows.length} rows. ${r.answer}`.slice(0, 300));
        requestAnimationFrame(() => {
          if (!hasPlotly()) { rc.outerHTML = `<p class="note">${NOPLOT}</p>`; return }
          let pairs = ch.type === 'pie' ? x.map((l, i) => [String(l ?? '(blank)'), +y[i]]).filter(p => p[1] > 0) : [];
          if (ch.type === 'pie' && !y.some(v => v < 0) && pairs.length > 1) {                    // positives only; top 7 + "Other" (28 slices were unreadable; negatives made % add up to >100)
            pairs.sort((a, b) => b[1] - a[1]); if (pairs.length > 8) { const rest = pairs.slice(7).reduce((s, p) => s + p[1], 0); pairs = pairs.slice(0, 7).concat([[`Other (${pairs.length - 7})`, rest]]) }
            Plotly.newPlot(rc, [{ type: 'pie', labels: pairs.map(p => p[0]), values: pairs.map(p => p[1]), hole: .45, sort: false, marker: { colors: [C.teal, C.light, C.amber, '#5F9EA0', '#D9B26A', '#7A8B99', '#2B8A8A', '#B8C4CC'] } }], lay({ rest: { margin: { l: 10, r: 10, t: 10, b: 10 } } }), cfg)
          }
          else if (ch.type === 'line' || (isDate && ch.type !== 'pie')) Plotly.newPlot(rc, [{ x: x.map(day), y, text: y.map(full), mode: 'lines+markers', line: { color: C.teal, width: 2.5 }, marker: { size: 6 }, hovertemplate: '%{text}<extra></extra>' }], lay({ rest: { showlegend: false } }), cfg)
          else barH(rc, x.map(v => String(day(v))), y)
        })
      } catch (e) { if (my !== askSeq) return; $('#ans').innerHTML = ''; $('#qerr').classList.remove('info'); $('#qerr').textContent = e.message }
      finally { if (my === askSeq) { asking = false; busy($('#go'), false) } }
    }
    $('#go').onclick = ask; $('#q').onkeydown = e => { if (e.key === 'Enter' && !e.isComposing) ask() };''')

# ======================================================================== JS: forecast
sub_re(r"async function runForecast\(\) \{.*?\n    \$\('#fgo'\)\.onclick = runForecast;", r'''let fcSeq = 0;
    async function runForecast() {
      if (!hasPlotly()) { $('#ferr').textContent = NOPLOT; return }
      const my = ++fcSeq; const per = Math.min(24, Math.max(1, Math.round(+$('#fp').value) || 6)); $('#fp').value = per;     // clamp client-side: '' / 0 / -3 / 2.5 / 100 were silently coerced or caused a 422
      $('#ferr').textContent = ''; busy($('#fgo'), true);
      try {
        const r = await api('/api/forecast', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sid, date_col: $('#fd').value, value_col: $('#fv').value, periods: per }) });
        if (my !== fcSeq) return;
        const f = r.forecast, h = r.history, last = h.x.length - 1;
        const tf = r.freq === 'D' ? '%d %b %Y' : (r.freq === 'W' ? '%d %b' : '%b %Y');
        const ht = r.freq === 'D' ? '%{x|%d %b %Y}: %{text}' : '%{x|%b %Y}: %{text}';
        Plotly.newPlot('fchart', [
          { x: h.x, y: h.y, text: h.y.map(full), mode: 'lines', name: 'Actual', line: { color: C.teal, width: 2.5 }, hovertemplate: ht + '<extra>Actual</extra>' },
          { x: [...f.x, ...f.x.slice().reverse()], y: [...f.upper, ...f.lower.slice().reverse()], mode: 'lines', fill: 'toself', fillcolor: 'rgba(199,127,0,.16)', line: { width: 0 }, name: 'Likely range', hoverinfo: 'skip' },
          { x: [h.x[last], ...f.x], y: [h.y[last], ...f.y], text: [h.y[last], ...f.y].map(full), mode: 'lines', name: 'Forecast', line: { color: C.amber, width: 2.5, dash: 'dot' }, hovertemplate: ht + '<extra>Forecast</extra>' }],
          lay({
            xaxis: { tickformat: tf }, rest: {
              legend: { orientation: 'h', y: 1.12, x: 0 }, margin: { l: 56, r: 16, t: 30, b: 36 },
              shapes: [{ type: 'line', x0: h.x[last], x1: h.x[last], yref: 'paper', y0: 0, y1: 1, line: { color: '#9AA7B1', width: 1, dash: 'dash' } }]
            }
          }), cfg);
        $('#fchart').setAttribute('role', 'img'); $('#fchart').setAttribute('aria-label', `Forecast of ${$('#fv').value}: ${r.note}`);
        $('#fnote').textContent = r.note.replace(/\b1 (month|week|day)s\b/g, '1 $1')
      } catch (e) { if (my !== fcSeq) return; $('#ferr').textContent = e.message } finally { if (my === fcSeq) busy($('#fgo'), false) }
    }
    $('#fgo').onclick = runForecast;''')

(DST / 'static/index.html').write_text(h)

# ======================================================================== assets: css, vendor, samples
(DST / 'static/lumen-fixes.css').write_text((UI / 'snippets/02-layout-fixes.css').read_text())
v = DST / 'static/vendor'; (v / 'fonts').mkdir(parents=True)
shutil.copy(UI / 'vendor/plotly-basic-2.35.2.min.js', v / 'plotly-basic-2.35.2.min.js')
for f in (UI / 'vendor/fonts').glob('*.woff2'): shutil.copy(f, v / 'fonts' / f.name)
fonts_css = (UI / 'snippets/01-vendor-assets/fonts.css').read_text()
(v / 'fonts.css').write_text(fonts_css)
(DST / 'static/samples').mkdir()
for f in (UI / 'snippets/samples').glob('*.csv'): shutil.copy(f, DST / 'static/samples' / f.name)

# main.py: gzip + cache + CSP (snippet 01)
main_py = (DST / 'app/main.py').read_text()
extra = (UI / 'snippets/01-vendor-assets/main_py_additions.py').read_text()
marker = 'app = FastAPI(title="Lumen")\n'
assert main_py.count(marker) == 1
main_py = main_py.replace(marker, marker + extra.split('# ---8<---\n', 1)[1])
(DST / 'app/main.py').write_text(main_py)

# ======================================================================== diffs
def udiff(a, b, out, la, lb):
    r = subprocess.run(['diff', '-u', '--label', la, '--label', lb, str(a), str(b)], capture_output=True, text=True)
    pathlib.Path(out).write_text(r.stdout); return len(r.stdout.splitlines())
n1 = udiff(SRC / 'static/index.html', DST / 'static/index.html', UI / 'snippets/03-bugfixes.diff', 'a/static/index.html', 'b/static/index.html')
n2 = udiff(SRC / 'app/main.py', DST / 'app/main.py', UI / 'snippets/01-vendor-assets/main.py.diff', 'a/app/main.py', 'b/app/main.py')
print('patched copy at', DST, '| index.html diff lines:', n1, '| main.py diff lines:', n2)
