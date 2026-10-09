"""Task 5: Devpost / README screenshots.
  python 09_gallery.py asis     -> shots/gallery/          against the CURRENT repo UI   (:8112)
  python 09_gallery.py patched  -> shots/gallery-patched/  against the patched copy + extras 04,05,07 (:8113)
Honesty notes (also in REPORT.md):
  * 'Ask' is enabled in the UI by patching `ai:true` into the /api/demo and /api/upload JSON (what the page looks like with a Gemini key).
  * Answers shown are MOCKED /api/ask responses: SQL + rows are REAL (run through the repo's guard + DuckDB on the real demo data),
    only the one-sentence prose is hand-written from those numbers.  The 'What matters most' text is the app's no-key template fallback.
"""
import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
import common as C
from common import *
from PIL import Image, ImageDraw, ImageFont

mode = sys.argv[1] if len(sys.argv) > 1 else 'asis'
C.BASE = 'http://localhost:8112' if mode == 'asis' else 'http://localhost:8113'
SUB = 'gallery' if mode == 'asis' else 'gallery-patched'
C.SHOTS = ROOT / 'shots'
M = json.loads((ROOT / 'mocks.json').read_text())
EXTRAS = ['04-sample-picker.html', '05-trust-panel.html', '07-report-export.html'] if mode == 'patched' else []
out = {}

QA = {  # question text -> mock payload
    'Which product brings in the most amount?': M['bar'],
    'How did amount change month over month?': M['line'],
    'How is amount split across regions?': M['pie'],
    'Show me the 10 biggest orders': M['table'],
}

def setup(page):
    # in-page wrapper (route.fetch cannot replay multipart uploads): show the UI as it looks WITH a Gemini key
    page.add_init_script("""(() => { const of = window.fetch; window.fetch = async (u, o) => { const r = await of(u, o);
      if (/\\/api\\/(demo|upload)/.test(String(u))) { const j = await r.clone().json().catch(() => null); if (j && j.session_id) { j.ai = 1; return new Response(JSON.stringify(j), { status: r.status, headers: r.headers }) } } return r } })()""")
    page.route('**/api/ask', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(QA[json.loads(r.request.post_data)['question']])))
    if EXTRAS:
        parts = ''.join((ROOT / 'snippets' / n).read_text() for n in EXTRAS)
        page.route(re.compile(r'^http://localhost:\d+/$'), lambda route: (lambda r: route.fulfill(response=r, body=r.text().replace('</body>', parts + '</body>')))(route.fetch()))
        page.route(re.compile(r'/assets/samples/'), lambda route: route.continue_())

def S(page, name, **kw):
    page.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()"); page.mouse.move(2, 2); page.wait_for_timeout(120)
    return shot(page, f'{SUB}/{name}', **kw)

def pad_clip(page, sel, pad=14):
    page.locator(sel).first.scroll_into_view_if_needed(); page.wait_for_timeout(150)
    b = page.evaluate("s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height}}", sel)
    return {'x': max(0, b['x'] - pad), 'y': max(0, b['y'] - pad), 'width': b['width'] + 2 * pad, 'height': b['height'] + 2 * pad}

def label(img_path, text):
    im = Image.open(img_path).convert('RGB'); w, h = im.size; bar = 54
    canvas = Image.new('RGB', (w, h + bar), '#EEF2F3'); canvas.paste(im, (0, bar)); d = ImageDraw.Draw(canvas)
    try: f = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 28)
    except Exception: f = ImageFont.load_default()
    d.text((16, 12), text, fill='#14202B', font=f); canvas.save(img_path)

with env(width=1440, height=960, scale=2) as e:
    p = e.page; setup(p); p.goto(C.BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); p.wait_for_timeout(700)
    out['hero'] = S(p, '01-hero-1440x960.png', full=False)
    if mode == 'patched':
        out['hero_full'] = S(p, '01b-hero-sample-picker-and-trust-panel.png', full=True)
    p.click('#demo'); wait_dashboard(p, settle=1500)
    out['top_fold'] = S(p, '02-dashboard-top-fold-1440x960.png', full=False)
    if mode == 'asis': hide_scroll_clip(p)   # only so the cropped sidebar shows all of its (otherwise nested-scroll clipped) content
    out['insights'] = S(p, '03-insights-panel.png', clip=pad_clip(p, 'aside', 18))
    out['kpis'] = S(p, '03b-kpi-row.png', clip=pad_clip(p, '#kpis', 10))
    out['charts'] = S(p, '04-at-a-glance-charts.png', clip=pad_clip(p, 'section:has(#charts)', 12))
    # forecast with changed controls: 9 periods
    p.fill('#fp', '9')
    with p.expect_response('**/api/forecast'): p.click('#fgo')
    p.wait_for_timeout(900)
    out['forecast'] = S(p, '05-forecast-9-periods.png', clip=pad_clip(p, 'section:has(#fchart)', 12))
    # answered questions (chips -> authentic flow)
    p.locator('section:has(#q)').scroll_into_view_if_needed()
    p.click('.chip >> nth=0'); p.wait_for_selector('#ans .a'); p.wait_for_timeout(1200)
    p.evaluate("document.querySelector('#ans details').open = true"); p.wait_for_timeout(300)
    out['answer_bar_sql'] = S(p, '06-answered-question-bar-with-sql.png', clip=pad_clip(p, 'section:has(#q)', 12))
    p.evaluate("document.querySelector('#ans details').open = false")
    out['answer_bar'] = S(p, '06b-answered-question-bar.png', clip=pad_clip(p, 'section:has(#q)', 12))
    p.click('.chip >> nth=1'); p.wait_for_function("(document.querySelector('#ans .a')||{innerText:''}).innerText.includes('lowest')"); p.wait_for_timeout(1200)
    out['answer_line'] = S(p, '06c-answered-question-line.png', clip=pad_clip(p, 'section:has(#q)', 12))
    p.fill('#q', 'How is amount split across regions?'); p.press('#q', 'Enter'); p.wait_for_function("(document.querySelector('#ans .a')||{innerText:''}).innerText.includes('Campus')"); p.wait_for_timeout(1200)
    out['answer_pie'] = S(p, '06d-answered-question-pie.png', clip=pad_clip(p, 'section:has(#q)', 12))
    p.fill('#q', 'Show me the 10 biggest orders'); p.press('#q', 'Enter'); p.wait_for_function("(document.querySelector('#ans .a')||{innerText:''}).innerText.includes('10 largest')"); p.wait_for_timeout(900)
    p.evaluate("document.querySelector('#ans details').open = true"); p.wait_for_timeout(300)
    out['answer_table'] = S(p, '06e-answered-question-table-open.png', clip=pad_clip(p, 'section:has(#q)', 12))
    out['log'] = e.log.summary()

with env(width=1440, height=960, scale=2) as e:
    p = e.page; setup(p); p.goto(C.BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)')
    upload(p, DATA / 'donations.csv'); p.wait_for_timeout(1200)
    out['donations_fold'] = S(p, '07-donations-dashboard-top-fold-1440x960.png', full=False)
    if mode == 'asis': hide_scroll_clip(p)
    out['donations_insights'] = S(p, '07b-donations-insights-panel.png', clip=pad_clip(p, 'aside', 18))
    out['donations_charts'] = S(p, '07c-donations-charts.png', clip=pad_clip(p, 'section:has(#charts)', 12))
    out['log_donations'] = e.log.summary()

with env(width=1440, height=960, scale=2) as e:
    p = e.page; setup(p); p.goto(C.BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)')
    upload(p, DATA / 'messy_us_shop.csv'); p.wait_for_timeout(800)
    sec = 'section:has(#preview-box)'
    p.locator(sec).scroll_into_view_if_needed()
    p.click('#tab-raw'); p.wait_for_timeout(250); a = S(p, '_raw.png', clip=pad_clip(p, sec, 12))
    p.click('#tab-processed'); p.wait_for_timeout(250); b = S(p, '_clean.png', clip=pad_clip(p, sec, 12))
    label(a, 'Raw input: mixed date formats, $ strings, stray spaces, N/A, yes/no'); label(b, 'Cleaned output: real dates, numbers, trimmed text, true/false')
    ia, ib = Image.open(a), Image.open(b); sheet = Image.new('RGB', (ia.width, ia.height + ib.height + 12), '#EEF2F3'); sheet.paste(ia, (0, 0)); sheet.paste(ib, (0, ia.height + 12))
    dst = ROOT / 'shots' / SUB / '08-data-preview-raw-vs-cleaned.png'; sheet.save(dst, optimize=True)
    pathlib.Path(a).unlink(); pathlib.Path(b).unlink(); out['preview_compare'] = str(dst)

with env(width=390, height=844, scale=2) as e:
    p = e.page; setup(p); p.goto(C.BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); p.wait_for_timeout(500)
    out['mobile_hero'] = S(p, '09-mobile-hero-390x844.png', full=False)
    p.click('#demo'); wait_dashboard(p, settle=1200)
    out['mobile_fold'] = S(p, '09b-mobile-dashboard-top-fold-390x844.png', full=False)
    out['mobile_full'] = S(p, '09c-mobile-dashboard-full.png', full=True)
    out['mobile_hscroll_px'] = p.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")

# verify: not blank / not broken, sizes
rows = []
for f in sorted((ROOT / 'shots' / SUB).glob('*.png')):
    im = Image.open(f).convert('L'); st = im.resize((200, max(1, int(200 * im.height / im.width)))).getextrema(); import statistics
    px = list(im.resize((100, 100)).getdata()); sd = statistics.pstdev(px)
    rows.append({'file': f.name, 'px': f'{Image.open(f).width}x{Image.open(f).height}', 'KB': round(f.stat().st_size / 1024), 'stddev': round(sd, 1), 'ok': sd > 8})
out['verify'] = rows
save_json(f'gallery_{mode}.json', out)
for r in rows: print(r)
print(json.dumps({k: v for k, v in out.items() if k.startswith('log') or 'hscroll' in k}, default=str)[:600])
