"""Verify snippets 04-09 (+02 css, +08 js) by injecting them into the ORIGINAL page in flight (nothing is edited on disk).
Run: pwvenv/bin/python scripts/08_verify_extras.py      (BASE = LUMEN_URL, default original :8112)  -> extras_verify.json, shots/extras/*.png
Set LUMEN_URL=http://localhost:8113 LUMEN_TAG=final to run the same checks on the patched copy (all fixes + all extras).
"""
import sys, subprocess; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
SN = ROOT / 'snippets'
def part(name):
    s = (SN / name).read_text()
    if name.endswith('.css'): return f'<style>{s}</style>'
    if name.endswith('.js'): return f'<script>{s}</script>'
    return s
def inject(page, names):
    parts = ''.join(part(n) for n in names)
    def h(route):
        r = route.fetch(); route.fulfill(response=r, body=r.text().replace('</body>', parts + '</body>'))
    page.route(re.compile(r'^http://localhost:\d+/$'), h)
    # the original server has no static/samples (that is part of the install step) -> serve them from snippets/samples for the test
    page.route(re.compile(r'/assets/samples/(\w+)\.csv$'), lambda r: r.fulfill(status=200, content_type='text/csv', body=(SN / 'samples' / (re.search(r'/(\w+)\.csv$', r.request.url).group(1) + '.csv')).read_bytes()) if BASE.endswith('8112') else r.continue_())
R = {}
def rec(k, v): R[k] = v; print('==', k, json.dumps(v, ensure_ascii=False, default=str)[:600])

# ---------------- 04 sample picker
with env(width=1440, height=900) as e:
    inject(e.page, ['04-sample-picker.html']); p = e.goto()
    rec('04.chips', p.evaluate("[...document.querySelectorAll('#samples .sample-chip')].map(c=>c.innerText.replace(/\\n/g,' '))"))
    shot(p, 'extras/04-hero-sample-picker.png', full=False)
    res = {}
    for sid in ('donations', 'inventory', 'shop'):
        p.click(f'#samples .sample-chip[data-sample={sid}]'); wait_dashboard(p)
        res[sid] = {'meta': p.inner_text('#meta'), 'kpis': p.evaluate("[...document.querySelectorAll('.kpi')].map(k=>k.innerText.replace(/\\n/g,' | '))")[:2], 'first_insight': p.inner_text('.ins b')}
        shot(p, f'extras/04-dashboard-{sid}-fold.png', full=False)
        p.click('#again'); p.wait_for_timeout(200)
    rec('04.results', res); rec('04.log', e.log.summary())

# ---------------- 05 trust panel (original => third parties; patched => 0)
with env(width=1440, height=900) as e:
    inject(e.page, ['05-trust-panel.html']); p = e.goto(); p.wait_for_timeout(600)
    rec('05.receipt', p.inner_text('#receipt')); shot(p, 'extras/05-hero-trust-panel-full.png'); rec('05.log', e.log.summary())
with env(width=390, height=844) as e:
    inject(e.page, ['05-trust-panel.html', '02-layout-fixes.css']); p = e.goto(); p.wait_for_timeout(600); shot(p, 'extras/05-hero-trust-panel-390.png'); rec('05.hscroll_390', p.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"))

# ---------------- 06 loading + reveal
with env(width=1440, height=900) as e:
    inject(e.page, ['06-loading-and-reveal.html']); p = e.goto()
    p.route('**/api/upload', lambda r: (time.sleep(2.2), r.continue_())[-1])
    p.set_input_files('#file', str(DATA / 'donations.csv')); p.wait_for_timeout(1500)
    rec('06.stage_states_at_1.5s', p.evaluate("[...document.querySelectorAll('#stage li')].map(l=>l.className||'-')")); rec('06.stage_visible', p.is_visible('#stage'))
    shot(p, 'extras/06-loading-stages.png', full=False, clip={'x': 700, 'y': 150, 'width': 740, 'height': 520})
    wait_dashboard(p, settle=100); rec('06.reveal_class', p.evaluate("document.querySelector('#app').classList.contains('reveal')"))
    rec('06.kpi_animation', p.evaluate("getComputedStyle(document.querySelector('.kpis')).animationName"))
    shot(p, 'extras/06-reveal-midway.png', full=False)
    rec('06.log', e.log.summary())
with sync_playwright() as pw:
    e = Env(pw, reduced_motion='reduce'); inject(e.page, ['06-loading-and-reveal.html']); p = e.goto(); p.click('#demo'); wait_dashboard(p, settle=50)
    rec('06.reduced_motion_kpi_animation', p.evaluate("getComputedStyle(document.querySelector('.kpis')).animationName")); e.close()

# ---------------- 07 report
with sync_playwright() as pw:
    e = Env(pw, width=1440, height=900); e.ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=BASE)
    p = e.page; inject(p, ['07-report-export.html']); p.goto(BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)')
    rec('07.buttons_visible_on_hero', p.is_visible('#rep-copy'))
    upload(p, DATA / 'donations.csv'); rec('07.buttons_visible_on_dashboard', [p.is_visible('#rep-copy'), p.is_visible('#rep-print')])
    shot(p, 'extras/07-header-buttons.png', full=False, clip={'x': 0, 'y': 0, 'width': 1440, 'height': 90})
    p.click('#rep-copy'); p.wait_for_timeout(300); clip = p.evaluate("navigator.clipboard.readText()")
    rec('07.clipboard_markdown', clip[:900]); rec('07.copy_button_label', p.inner_text('#rep-copy'))
    p.evaluate("window.print = () => { window.__printed = 1 }; 0"); p.click('#rep-print'); p.wait_for_function('window.__printed===1'); rec('07.print_images_created', p.evaluate("document.querySelectorAll('.print-chart').length"))
    pdf = p.pdf(format='A4', print_background=True, prefer_css_page_size=True); pp = ROOT / 'shots/extras/07-report-donations.pdf'; pp.parent.mkdir(parents=True, exist_ok=True); pp.write_bytes(pdf)
    rec('07.pdf_pages', len(re.findall(rb'/Type\s*/Page[^s]', pdf)))
    subprocess.run(['pdftoppm', '-png', '-r', '70', str(pp), str(ROOT / 'shots/extras/07-report-donations')], check=False)
    rec('07.log', e.log.summary()); e.close()

# ---------------- 08 a11y enhancer + 09 ask-disabled (original page, no key)
with env(width=1440, height=900) as e:
    p = e.page; inject(p, ['08-a11y-enhancer.js', '09-ask-disabled-state.html']); p.goto(BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); load_demo(p)
    rec('08.state', p.evaluate("""() => ({tabs:[...document.querySelectorAll('.tab')].map(t=>[t.getAttribute('role'),t.getAttribute('aria-selected'),t.tabIndex]), tablist: !!document.querySelector('[role=tablist]'), panel: document.querySelector('#preview-box').getAttribute('role'),
        ans_live: document.querySelector('#ans').getAttribute('aria-live'), charts: [...document.querySelectorAll('#charts .chart,#fchart')].map(c=>[c.getAttribute('role'),(c.getAttribute('aria-label')||'').slice(0,60)]),
        focus: document.activeElement.tagName+':'+document.activeElement.textContent.slice(0,20)})"""))
    p.focus('#tab-processed'); p.keyboard.press('ArrowLeft'); rec('08.arrow_left', p.evaluate("[document.querySelector('#tab-raw').getAttribute('aria-selected'), document.activeElement.id]"))
    cnt = {'n': 0}; p.route('**/api/forecast', lambda r: (cnt.__setitem__('n', cnt['n'] + 1), time.sleep(0.8), r.continue_())[-1])
    p.focus('#fgo'); [p.keyboard.press('Enter') for _ in range(3)]; p.wait_for_timeout(3500); rec('08.forecast_requests_from_3_enters (was 3)', cnt['n'])
    rec('09.qerr', p.inner_text('#qerr')); rec('09.section_class', p.evaluate("document.querySelector('#q').closest('section').className"))
    shot(p, 'extras/09-ask-disabled-calm.png', el='section:has(#q)'); rec('0809.log', e.log.summary())

# ---------------- all extras together (conflict check) on original, desktop + mobile
ALL = ['02-layout-fixes.css', '04-sample-picker.html', '05-trust-panel.html', '06-loading-and-reveal.html', '07-report-export.html', '08-a11y-enhancer.js', '09-ask-disabled-state.html']
for w, h in ((1440, 900), (390, 844)):
    with env(width=w, height=h) as e:
        inject(e.page, ALL); p = e.goto(); p.wait_for_timeout(500); shot(p, f'extras/all-hero-{w}.png', full=False)
        p.click('#samples .sample-chip[data-sample=donations]'); wait_dashboard(p); p.wait_for_timeout(700)
        shot(p, f'extras/all-dashboard-{w}-full.png'); shot(p, f'extras/all-dashboard-{w}-fold.png', full=False)
        rec(f'all.{w}.log', e.log.summary()); rec(f'all.{w}.hscroll', p.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"))
save_json('extras_verify.json', R); print('DONE')
