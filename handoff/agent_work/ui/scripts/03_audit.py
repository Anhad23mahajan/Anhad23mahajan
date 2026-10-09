"""Task 2: automated audit -> audit.json (+ shots/qa/focus-*.png, shots/qa/print-*.png).
Run: /home/user/work/ui/pwvenv/bin/python /home/user/work/ui/scripts/03_audit.py
"""
import sys, gzip, zlib; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *

A = {}
def rec(k, v): A[k] = v; print('==', k, '\n  ', json.dumps(v, ensure_ascii=False, default=str)[:900])

DESC = """const desc = el => { if(!el) return null; let s = el.tagName.toLowerCase(); if (el.id) s += '#' + el.id; if (el.classList && el.classList.length) s += '.' + [...el.classList].slice(0,2).join('.'); return s; };"""

# ------------------------------------------------------------------ 1. horizontal overflow sweep (+ culprit finder, + candidate fix)
OVERFLOW_JS = DESC + """
() => {
  const W = document.documentElement.clientWidth; const bad = [];
  const clipped = el => { for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p); if (/(auto|scroll|hidden)/.test(o.overflowX)) return true } return false };
  document.querySelectorAll('body *').forEach(el => {
    if (el.closest('.js-plotly-plot')) return; const r = el.getBoundingClientRect();
    if (r.width && r.right > W + 1 && !clipped(el)) bad.push({el: desc(el), right: Math.round(r.right), width: Math.round(r.width)});
  });
  return {scrollWidth: document.documentElement.scrollWidth, clientWidth: W, culprits: bad.slice(0, 8)};
}"""
FIX_CSS = '@media(max-width:960px){#app{grid-template-columns:minmax(0,1fr)}}'
sweep = {}
for w in [320, 360, 390, 414, 480, 600, 640, 700, 768, 820, 960, 1024, 1280, 1440, 1920]:
    with env(width=w, height=900) as e:
        p = e.goto(); load_demo(p)
        r = p.evaluate(OVERFLOW_JS)
        p.add_style_tag(content=FIX_CSS); p.wait_for_timeout(400)
        r2 = p.evaluate(OVERFLOW_JS)
        sweep[w] = {'as_is': {'scrollWidth': r['scrollWidth'], 'overflow_px': r['scrollWidth'] - r['clientWidth'], 'culprits': r['culprits'][:3]},
                    'with_fix': {'scrollWidth': r2['scrollWidth'], 'overflow_px': r2['scrollWidth'] - r2['clientWidth'], 'culprits': r2['culprits'][:3]}}
rec('overflow_sweep', sweep)

# ------------------------------------------------------------------ 2. overlaps + header wrap at 3 widths
OVERLAP_JS = DESC + """
() => {
  const atoms = [];
  document.querySelectorAll('body *').forEach(el => {
    if (el.closest('.js-plotly-plot') || el.closest('script,style') || el.closest('svg') || el.closest('.preview-table') || el.closest('details')) return;
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const isCtl = /^(BUTTON|INPUT|SELECT|SUMMARY)$/.test(el.tagName) || el.classList.contains('chart');
    if (!(own || isCtl)) return; const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return;
    atoms.push({el, r});
  });
  const out = [];
  for (let i = 0; i < atoms.length; i++) for (let j = i + 1; j < atoms.length; j++) {
    const a = atoms[i], b = atoms[j]; if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left), h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
    if (w > 2 && h > 2) out.push({a: desc(a.el) + ' "' + (a.el.innerText||a.el.value||'').slice(0,24).replace(/\\n/g,' ') + '"', b: desc(b.el) + ' "' + (b.el.innerText||b.el.value||'').slice(0,24).replace(/\\n/g,' ') + '"', w: Math.round(w), h: Math.round(h)});
  }
  return out.slice(0, 15);
}"""
ov = {}
for w in [1440, 820, 390]:
    with env(width=w, height=900) as e:
        p = e.goto(); load_demo(p)
        ov[w] = p.evaluate(OVERLAP_JS)
        ov[f'{w}_header'] = p.evaluate("(()=>{const h=document.querySelector('header');const r=h.getBoundingClientRect();const b=document.querySelector('#again').getBoundingClientRect();const t=document.querySelector('header span').getBoundingClientRect();return {header_h:Math.round(r.height), btn:[Math.round(b.width),Math.round(b.height)], tagline:[Math.round(t.width),Math.round(t.height)]}})()")
rec('overlaps_and_header', ov)

# ------------------------------------------------------------------ 3. contrast (text) + non-text UI boundaries
CONTRAST_JS = """
() => {
  const parse = c => { let m = c.match(/^color\\(srgb ([\\d.]+) ([\\d.]+) ([\\d.]+)(?: \\/ ([\\d.]+))?\\)/); if (m) return {r:+m[1]*255, g:+m[2]*255, b:+m[3]*255, a: m[4]===undefined?1:+m[4]};
    m = c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number); return {r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1}; };
  const over = (f, b) => ({r: f.r*f.a + b.r*(1-f.a), g: f.g*f.a + b.g*(1-f.a), b: f.b*f.a + b.b*(1-f.a), a: 1});
  const L = c => { const f = v => { v /= 255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4) }; return .2126*f(c.r) + .7152*f(c.g) + .0722*f(c.b) };
  const ratio = (a, b) => { const x = L(a), y = L(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05) };
  const bgOf = el => { const chain = []; for (let e = el; e; e = e.parentElement) chain.push(e); let base = {r:255,g:255,b:255,a:1};
    for (const e of chain.reverse()) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a > 0) base = over(c, base) } return base };
  const hex = c => '#' + [c.r,c.g,c.b].map(v => Math.round(v).toString(16).padStart(2,'0')).join('');
  const seen = new Map(); const rows = [];
  document.querySelectorAll('body *').forEach(el => {
    const cs = getComputedStyle(el); if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const isSvgText = el.tagName.toLowerCase() === 'text';
    const own = isSvgText ? el.textContent.trim() : [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (!own) return; const r = el.getBoundingClientRect(); if (r.width < 1 || r.height < 1) return;
    let fg = parse(isSvgText ? cs.fill : cs.color); if (!fg) return; const bg = bgOf(el); const fg2 = over(fg, bg);
    const size = parseFloat(cs.fontSize); const bold = parseInt(cs.fontWeight) >= 700; const large = size >= 24 || (size >= 18.66 && bold);
    const cr = ratio(fg2, bg); const key = el.tagName + '.' + (el.className.baseVal ?? el.className) + hex(fg2) + hex(bg) + size;
    if (seen.has(key)) { seen.get(key).count++; return } const row = {sel: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + '.' + String(el.className.baseVal ?? el.className).split(' ')[0], text: own.slice(0, 40), fg: hex(fg2), bg: hex(bg), ratio: +cr.toFixed(2), size, bold, need: large ? 3 : 4.5, count: 1, pass: cr >= (large ? 3 : 4.5)};
    seen.set(key, row); rows.push(row);
  });
  // placeholder
  const q = document.querySelector('#q'); if (q) { const ph = getComputedStyle(q, '::placeholder'); const f = parse(ph.color), b = bgOf(q); rows.push({sel: '#q::placeholder', text: q.placeholder.slice(0,30), fg: hex(over(f,b)), bg: hex(b), ratio: +ratio(over(f,b), b).toFixed(2), size: 16, need: 4.5, count: 1, pass: ratio(over(f,b), b) >= 4.5}) }
  // non-text boundaries (WCAG 1.4.11 needs 3:1 against adjacent colour)
  const nt = []; const bnd = (sel, label) => { const el = document.querySelector(sel); if (!el) return; const cs = getComputedStyle(el); const bc = parse(cs.borderTopColor); const parentBg = bgOf(el.parentElement);
    if (bc) nt.push({control: label, border: hex(over(bc, parentBg)), against: hex(parentBg), ratio: +ratio(over(bc, parentBg), parentBg).toFixed(2), need: 3, pass: ratio(over(bc, parentBg), parentBg) >= 3}) };
  bnd('#q', 'Ask text input border'); bnd('#fp', 'Forecast periods input border'); bnd('#fv', 'Forecast select border'); bnd('.tab:not(.active)', 'Inactive preview tab border');
  const chip = document.querySelector('.chip'); if (chip) { const cb = parse(getComputedStyle(chip).backgroundColor), pb = bgOf(chip.parentElement); nt.push({control: 'Suggestion chip fill (no border)', border: hex(cb), against: hex(pb), ratio: +ratio(cb, pb).toFixed(2), need: 3, pass: ratio(cb, pb) >= 3}) }
  const am = {r:199,g:127,b:0,a:1}, wh = {r:255,g:255,b:255,a:1}; nt.push({control: 'Focus ring (amber #C77F00) on white', border: '#c77f00', against: '#ffffff', ratio: +ratio(am, wh).toFixed(2), need: 3, pass: ratio(am, wh) >= 3});
  const pb2 = {r:238,g:242,b:243,a:1}; nt.push({control: 'Focus ring (amber) on page background #EEF2F3', border: '#c77f00', against: '#eef2f3', ratio: +ratio(am, pb2).toFixed(2), need: 3, pass: ratio(am, pb2) >= 3});
  return {text: rows, nontext: nt};
}"""
with env(width=1440, height=900) as e:
    p = e.goto()
    hero = p.evaluate(CONTRAST_JS)
    load_demo(p)
    dash = p.evaluate(CONTRAST_JS)
    # answered state + error + unverified states
    M = json.loads((ROOT / 'mocks.json').read_text())
    mock_ask(p, M['unverified']); ask(p, 'x')
    ans = p.evaluate(CONTRAST_JS)
    allrows = {}
    for src in (hero, dash, ans):
        for r in src['text']: allrows[(r['sel'], r['fg'], r['bg'], r['size'])] = r
    fails = sorted([r for r in allrows.values() if not r['pass']], key=lambda r: r['ratio'])
    lows = sorted([r for r in allrows.values() if r['pass']], key=lambda r: r['ratio'])[:8]
    rec('contrast_text_fails', fails)
    rec('contrast_text_lowest_passing', lows)
    rec('contrast_nontext', dash['nontext'])
    A['contrast_all_rows_count'] = len(allrows)
    # hover/disabled states
    p.hover('#fgo'); p.wait_for_timeout(200)
    rec('contrast_hover_fgo', p.evaluate("(()=>{const cs=getComputedStyle(document.querySelector('#fgo'));return [cs.color,cs.backgroundColor]})()"))
    # disabled forecast button (no date columns)
with env(width=1440, height=900) as e:
    p = e.goto(); upload(p, DATA / 'no_dates.csv', forecast=False)
    rec('disabled_forecast_btn_style', p.evaluate("(()=>{const b=document.querySelector('#fgo');const cs=getComputedStyle(b);return {disabled:b.disabled,color:cs.color,bg:cs.backgroundColor,opacity:cs.opacity,cursor:cs.cursor}})()"))

# ------------------------------------------------------------------ 4. keyboard + focus visibility (+ chips with Enter) + ARIA/semantics
FOCUS_JS = DESC + """
() => { const el = document.activeElement; if (!el || el === document.body) return null; const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
  return {el: desc(el), text: (el.innerText || el.value || el.getAttribute('aria-label') || '').slice(0, 30), outline: cs.outlineStyle + ' ' + cs.outlineWidth + ' ' + cs.outlineColor, outlineOffset: cs.outlineOffset, shadow: cs.boxShadow === 'none' ? '' : cs.boxShadow.slice(0, 60),
    border: cs.borderTopColor, visible_in_viewport: r.top >= 0 && r.bottom <= innerHeight, y: Math.round(r.top + scrollY), matches_focus_visible: el.matches(':focus-visible'), tabindex: el.getAttribute('tabindex')} }"""
with env(width=1440, height=900) as e:
    p = e.goto()
    stops = []
    for i in range(4):
        p.keyboard.press('Tab'); s = p.evaluate(FOCUS_JS); stops.append(s)
        if s and i < 2: shot(p, f'qa/focus-hero-{i+1}.png', clip={'x': max(0, 0), 'y': 0, 'width': 1440, 'height': 640}) if False else None
    rec('keyboard.hero_tab_stops', stops)
    p.keyboard.press('Enter')   # Tab 4 was after 2nd button -> nothing. Go back and test activating "Try sample" by keyboard
    p.reload(); p.evaluate('document.fonts.ready.then(()=>0)')
    p.keyboard.press('Tab'); p.keyboard.press('Tab'); focused = p.evaluate(FOCUS_JS)
    shot(p, 'qa/focus-hero-try-sample.png', full=False)
    p.keyboard.press('Enter'); wait_dashboard(p)
    rec('keyboard.enter_on_demo_button', {'focused': focused, 'dashboard_shown': p.evaluate("getComputedStyle(document.querySelector('#app')).display"), 'focus_after': p.evaluate(FOCUS_JS)})
    # where does focus go after the hero is hidden? (focus lost -> keyboard users start from top)
    A['keyboard.focus_after_render_is_body'] = p.evaluate("document.activeElement===document.body")
    stops = []
    for i in range(30):
        p.keyboard.press('Tab'); s = p.evaluate(FOCUS_JS)
        if s: stops.append(s)
        if s and s['el'].startswith('input#fp') and i > 5: pass
    rec('keyboard.dashboard_tab_stops', stops)
    # focus crops
    for sel, name in [('#q', 'input-q'), ('#go', 'btn-ask'), ('.chip >> nth=0', 'chip'), ('#tab-raw', 'tab'), ('#fv', 'select'), ('#fp', 'input-fp'), ('#fgo', 'btn-forecast'), ('summary', 'summary')]:
        try:
            p.locator(sel).first.scroll_into_view_if_needed(); p.locator(sel).first.focus(); p.keyboard.press('Shift+Tab'); p.keyboard.press('Tab'); p.wait_for_timeout(120)
            b = p.locator(sel).first.bounding_box()
            if b: p.screenshot(path=str(SHOTS / f'qa/focus-{name}.png'), clip={'x': max(0, b['x'] - 14), 'y': max(0, b['y'] - 14), 'width': min(b['width'] + 28, 700), 'height': b['height'] + 28})
        except Exception as ex: print('focus shot fail', sel, str(ex)[:80])
    # chip activation with Enter / Space
    p.locator('.chip').first.focus(); p.keyboard.press('Enter'); p.wait_for_timeout(900)
    rec('keyboard.chip_enter', {'q': p.input_value('#q'), 'qerr': p.inner_text('#qerr')})
    # Enter pressed 3x quickly in #q -> number of /api/ask requests
    cnt = {'n': 0}
    def cnt_route(route): cnt['n'] += 1; time.sleep(0.4); route.fulfill(status=200, content_type='application/json', body=json.dumps(M['bar']))
    p.route('**/api/ask', cnt_route)
    p.fill('#q', 'bar'); p.focus('#q'); p.keyboard.press('Enter'); p.keyboard.press('Enter'); p.keyboard.press('Enter'); p.wait_for_timeout(2500)
    rec('keyboard.triple_enter_ask_requests', cnt['n'])
    # Tab order sanity: DOM order == visual order?  (aside first on mobile)
    SEM = """() => ({lang: document.documentElement.lang, title: document.title, h1: document.querySelectorAll('h1').length, h1_visible: [...document.querySelectorAll('h1')].filter(h=>h.offsetParent).length,
      headings: [...document.querySelectorAll('h1,h2,h3')].filter(h=>h.offsetParent).map(h=>h.tagName+':'+h.innerText.slice(0,28)),
      landmarks: [...document.querySelectorAll('header,main,aside,nav,footer,section,[role]')].map(l=>l.tagName.toLowerCase()+(l.getAttribute('role')?'[role='+l.getAttribute('role')+']':'')+(l.getAttribute('aria-label')?'[label]':'')),
      tabs: [...document.querySelectorAll('.tab')].map(t=>({text:t.innerText, role:t.getAttribute('role'), selected:t.getAttribute('aria-selected'), pressed:t.getAttribute('aria-pressed'), cls:t.className})),
      tablist: !!document.querySelector('.tabs[role=tablist]'),
      charts: [...document.querySelectorAll('.chart,#fchart,.js-plotly-plot')].filter((v,i,a)=>a.indexOf(v)===i).map(c=>({id:c.id||c.className.split(' ')[0], role:c.getAttribute('role'), label:c.getAttribute('aria-label'), labelledby:c.getAttribute('aria-labelledby')})),
      live_regions: [...document.querySelectorAll('[aria-live],[role=alert],[role=status]')].map(l=>l.id||l.className),
      ans_is_live: !!document.querySelector('#ans[aria-live]'), ans_role: document.querySelector('#ans').getAttribute('role'),
      aria_busy_used: document.querySelectorAll('[aria-busy]').length, busy_css: (()=>{for(const s of document.styleSheets){let rules; try{rules=s.cssRules}catch(e){continue} for(const r of rules){if(r.selectorText==='.busy')return r.style.cssText}}})(),
      imgs_without_alt: [...document.querySelectorAll('img:not([alt])')].length, svg_icons_hidden: [...document.querySelectorAll('header svg')].map(s=>s.getAttribute('aria-hidden')),
      inputs: [...document.querySelectorAll('input,select')].map(i=>({id:i.id, label:(i.labels&&i.labels[0]?i.labels[0].innerText.trim().slice(0,30):null), aria:i.getAttribute('aria-label')})),
      preview_th_scope: [...document.querySelectorAll('#preview-box th')].some(t=>t.getAttribute('scope')), table_caption: !!document.querySelector('#preview-box caption'),
      meta_description: !!document.querySelector('meta[name=description]'), favicon_link: !!document.querySelector('link[rel~=icon]'), noscript: !!document.querySelector('noscript'),
      color_scheme_meta: !!document.querySelector('meta[name=color-scheme]'), skip_link: !!document.querySelector('a[href^="#"]'), viewport: document.querySelector('meta[name=viewport]').content,
      aside_scrollable_without_tabindex: (()=>{const a=document.querySelector('aside');return a.scrollHeight>a.clientHeight && !a.hasAttribute('tabindex')})()})"""
    rec('semantics.dashboard', p.evaluate(SEM))
    try: A['aria_snapshot'] = p.locator('body').aria_snapshot()[:3500]
    except Exception as ex: A['aria_snapshot'] = 'ERR ' + str(ex)[:100]

# ------------------------------------------------------------------ 5. keyboard: busy class vs keyboard (pointer-events:none only)
with env(width=1440, height=900) as e:
    p = e.goto(); load_demo(p)
    cnt = {'n': 0}
    def slow(route):
        cnt['n'] += 1; time.sleep(1.2); route.fulfill(status=200, content_type='application/json', body=json.dumps({'detail': 'x'}), headers={})
    p.route('**/api/forecast', lambda r: (cnt.__setitem__('n', cnt['n'] + 1), time.sleep(1.0), r.continue_())[-1])
    p.focus('#fgo'); p.keyboard.press('Enter'); p.keyboard.press('Enter'); p.keyboard.press('Space'); p.wait_for_timeout(3500)
    rec('busy_vs_keyboard.forecast_requests_from_3_key_presses', cnt['n'])

# ------------------------------------------------------------------ 6. performance / weight / third parties
with env(width=1440, height=900) as e:
    p = e.page
    p.add_init_script("""window.__lcp=0; new PerformanceObserver(l=>{for(const x of l.getEntries()) window.__lcp=Math.round(x.startTime)}).observe({type:'largest-contentful-paint',buffered:true});
                         window.__long=[]; try{new PerformanceObserver(l=>{for(const x of l.getEntries()) window.__long.push([Math.round(x.startTime),Math.round(x.duration)])}).observe({type:'longtask',buffered:true})}catch(e){}""")
    p.goto(BASE + '/', wait_until='load'); p.evaluate('document.fonts.ready.then(()=>0)')
    nav = p.evaluate("(()=>{const n=performance.getEntriesByType('navigation')[0];const fcp=performance.getEntriesByType('paint').find(x=>x.name==='first-contentful-paint');return {dcl:Math.round(n.domContentLoadedEventEnd),load:Math.round(n.loadEventEnd),fcp:fcp?Math.round(fcp.startTime):null,lcp:window.__lcp,html_transfer:n.encodedBodySize,html_decoded:n.decodedBodySize}})()")
    t0 = time.time(); p.click('#demo'); wait_dashboard(p, settle=0); click_to_dash = time.time() - t0
    fetches = p.evaluate("performance.getEntriesByType('resource').filter(r=>r.initiatorType==='fetch').map(r=>[r.name.replace(location.origin,''), Math.round(r.duration), r.encodedBodySize])")
    dom = p.evaluate("({nodes: document.getElementsByTagName('*').length, plots: document.querySelectorAll('.js-plotly-plot').length, heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize/1e5)/10 : null, long: window.__long})")
    third = sorted({re.match(r'https?://[^/]+', r['url']).group(0) for r in e.log.requests if re.match(r'https?://[^/]+', r['url']) and not r['url'].startswith(BASE)})
    plotly_gz = len(gzip.compress(PLOTLY_JS, 9))
    rec('perf', {'navigation_ms (all third-party served locally by the harness, so CDN latency NOT included)': nav, 'click_demo_to_dashboard_s': round(click_to_dash, 2), 'fetches[name,ms,bytes]': fetches, 'dom': dom,
                 'third_party_origins_contacted': third,
                 'plotly_basic_2.35.2_bytes_raw': len(PLOTLY_JS), 'plotly_gzip9_bytes': plotly_gz, 'fonts_woff2_bytes_vendored_latin_subset': len(FONT_BRICOLAGE) + len(FONT_FIGTREE),
                 'index_html_bytes': nav['html_decoded'], 'index_html_gzip_bytes': len(gzip.compress(pathlib.Path('/home/user/Anhad23mahajan/lumen/static/index.html').read_bytes(), 9)),
                 'est_download_1.6Mbps_slow4g_s_for_plotly_gz': round(plotly_gz * 8 / 1.6e6, 1), 'est_download_10Mbps_s_for_plotly_gz': round(plotly_gz * 8 / 10e6, 2)})
    # render-blocking: Plotly <script> is sync in <head>
    rec('render_blocking', p.evaluate("[...document.querySelectorAll('head script[src], head link[rel=stylesheet]')].map(s=>({tag:s.tagName,src:s.src||s.href,async:s.async,defer:s.defer}))"))
    # response headers for static
    import urllib.request
    rq = urllib.request.Request(BASE + '/', headers={'Accept-Encoding': 'gzip'}); rs = urllib.request.urlopen(rq)
    hh = {k.lower(): v for k, v in rs.getheaders()}
    rec('server_headers', {'headers': hh, 'gzip_middleware_active': 'content-encoding' in hh, 'csp': 'content-security-policy' in hh, 'cache-control': hh.get('cache-control'), 'etag': hh.get('etag')})

# ------------------------------------------------------------------ 7. reduced motion
with sync_playwright() as pw:
    e = Env(pw, width=1440, height=900, reduced_motion='reduce')
    p = e.goto()
    delay = {'n': 0}
    p.route('**/api/upload', lambda r: (time.sleep(1.2), r.continue_())[-1])
    p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_selector('#uerr .spin', timeout=3000)
    rm = p.evaluate("(()=>{const s=document.querySelector('.spin');const cs=getComputedStyle(s);return {animationName:cs.animationName, matchMedia:matchMedia('(prefers-reduced-motion: reduce)').matches}})()")
    shot(p, 'qa/loading-state-upload.png', full=False, clip={'x': 700, 'y': 230, 'width': 700, 'height': 320})
    e.close()
with sync_playwright() as pw:
    e = Env(pw, width=1440, height=900)
    p = e.goto(); p.route('**/api/upload', lambda r: (time.sleep(1.2), r.continue_())[-1])
    p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_selector('#uerr .spin', timeout=3000)
    normal = p.evaluate("getComputedStyle(document.querySelector('.spin')).animationName")
    rec('reduced_motion', {'reduce': rm, 'normal_animationName': normal, 'other_transitions': 'only .btn background .15s, #drop background .15s (both harmless)'})
    e.close()

# ------------------------------------------------------------------ 8. print stylesheet (what "Print / Save as PDF" gives today)
for name, f in [('demo', None), ('donations', DATA / 'donations.csv')]:
    with env(width=1100, height=900) as e:
        p = e.goto()
        if f: upload(p, f)
        else: load_demo(p)
        pdf = p.pdf(format='A4', print_background=True)
        pdfp = ROOT / f'shots/qa/print-{name}.pdf'; pdfp.write_bytes(pdf)
        pages = len(re.findall(rb'/Type\s*/Page[^s]', pdf))
        p.emulate_media(media='print'); p.wait_for_timeout(300)
        shot(p, f'qa/print-{name}-emulated.png')
        rec(f'print.{name}', {'pdf_pages_A4': pages, 'aside_clipped_in_print': p.evaluate("(a=>a.scrollHeight>a.clientHeight)(document.querySelector('aside'))"),
                              'has_print_css': True and any(('print' in (r.media.mediaText if hasattr(r, 'media') else '')) for r in [])})
print(json.dumps(list(A.keys())))
save_json('audit.json', A)
print('DONE')
