"""Task 1: drive the full flow and take QA screenshots (shots/qa/*).
Run: /home/user/work/ui/pwvenv/bin/python /home/user/work/ui/scripts/01_flow.py
"""
import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *

results = {}
def note(k, v): results[k] = v; print(k, '->', str(v)[:200])

VIEWPORTS = [('desktop-1440x900', 1440, 900), ('desktop-1920x1080', 1920, 1080), ('tablet-820x1180', 820, 1180), ('mobile-390x844', 390, 844)]

# ------------------------------------------------------------------ A/B: hero + demo flow at 4 viewports
for name, w, h in VIEWPORTS:
    with env(width=w, height=h, mobile=(w < 500)) as e:
        p = e.goto()
        note(f'hero.{name}.shot', shot(p, f'qa/hero-{name}.png', full=False))
        t0 = time.time(); p.click('#demo'); wait_dashboard(p, settle=0); dt = time.time() - t0
        p.wait_for_timeout(600)
        note(f'demo.{name}.click_to_dashboard_s', round(dt, 2))
        note(f'demo.{name}.shot_full', shot(p, f'qa/dashboard-demo-{name}-full.png', full=True))
        note(f'demo.{name}.shot_fold', shot(p, f'qa/dashboard-demo-{name}-fold.png', full=False))
        note(f'demo.{name}.scrollWidth', p.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]'))
        note(f'demo.{name}.log', e.log.summary())

# ------------------------------------------------------------------ C: uploads (donations, messy European)
for fname, tag in [('donations.csv', 'donations'), ('messy_european.csv', 'messy-european')]:
    with env(width=1440, height=900) as e:
        p = e.goto(); upload(p, DATA / fname)
        note(f'upload.{tag}.shot_full', shot(p, f'qa/dashboard-{tag}-1440-full.png'))
        note(f'upload.{tag}.sidebar_overflow', p.evaluate("(a=>[a.scrollHeight,a.clientHeight])(document.querySelector('aside'))"))
        # preview tabs
        sec = "section:has(#preview-box)"
        p.locator(sec).scroll_into_view_if_needed()
        note(f'upload.{tag}.preview_cleaned', shot(p, f'qa/preview-{tag}-cleaned.png', el=sec))
        p.click('#tab-raw'); p.wait_for_timeout(200)
        note(f'upload.{tag}.preview_raw', shot(p, f'qa/preview-{tag}-raw.png', el=sec))
        note(f'upload.{tag}.preview_header_raw', p.evaluate("[...document.querySelectorAll('#preview-box th')].map(t=>t.innerText.replace(/\\n/g,' | '))"))
        p.click('#tab-processed')
        note(f'upload.{tag}.preview_header_clean', p.evaluate("[...document.querySelectorAll('#preview-box th')].map(t=>t.innerText.replace(/\\n/g,' | '))"))
        note(f'upload.{tag}.kpis', p.evaluate("[...document.querySelectorAll('.kpi')].map(k=>k.innerText.replace(/\\n/g,' | '))"))
        note(f'upload.{tag}.insights', p.evaluate("[...document.querySelectorAll('.ins')].map(k=>k.innerText.replace(/\\n/g,' | '))"))
        note(f'upload.{tag}.recs', p.evaluate("[...document.querySelectorAll('#recs li')].map(k=>k.innerText)"))
        note(f'upload.{tag}.log', e.log.summary())

# demo preview tabs (raw == cleaned for the demo; tabs look identical)
with env(width=1440, height=900) as e:
    p = e.goto(); load_demo(p)
    sec = "section:has(#preview-box)"
    p.locator(sec).scroll_into_view_if_needed()
    note('preview.demo.cleaned', shot(p, 'qa/preview-demo-cleaned.png', el=sec))
    p.click('#tab-raw'); p.wait_for_timeout(200)
    note('preview.demo.raw', shot(p, 'qa/preview-demo-raw.png', el=sec))
    note('preview.demo.raw_equals_cleaned', p.evaluate("document.querySelector('#preview-box').innerText") == (p.click('#tab-processed') or p.evaluate("document.querySelector('#preview-box').innerText")))

# ------------------------------------------------------------------ D: forecast with changed controls
with env(width=1440, height=900) as e:
    p = e.goto(); load_demo(p)
    fsec = "section:has(#fchart)"
    p.locator(fsec).scroll_into_view_if_needed()
    note('forecast.default', shot(p, 'qa/forecast-default.png', el=fsec))
    p.select_option('#fv', 'quantity'); p.fill('#fp', '12'); p.click('#fgo'); p.wait_for_timeout(1200)
    note('forecast.quantity12.shot', shot(p, 'qa/forecast-quantity-12periods.png', el=fsec))
    note('forecast.quantity12.note', p.inner_text('#fnote'))
    for label, val in [('float-2.5', '2.5'), ('zero', '0'), ('empty', ''), ('negative', '-3'), ('huge-100', '100'), ('sci-1e3', '1e3')]:
        p.fill('#fp', val)
        with p.expect_response('**/api/forecast') as ri: p.click('#fgo')
        p.wait_for_timeout(500)
        note(f'forecast.periods[{label}]', {'sent': val, 'http': ri.value.status, 'err': p.inner_text('#ferr'), 'note': p.inner_text('#fnote')[:90]})
        if label in ('float-2.5', 'zero'): shot(p, f'qa/forecast-periods-{label}.png', el=fsec)
    note('forecast.log', e.log.summary())

for fname, tag in [('short_history.csv', 'short-history'), ('no_dates.csv', 'no-dates'), ('dates_no_metric.csv', 'dates-no-metric')]:
    with env(width=1440, height=900) as e:
        p = e.goto(); upload(p, DATA / fname, charts=(fname != 'dates_no_metric.csv'), forecast=False)
        fsec = "section:has(#fchart)"; p.locator(fsec).scroll_into_view_if_needed(); p.wait_for_timeout(2200)
        note(f'forecast.{tag}', {'err': p.inner_text('#ferr'), 'btn_disabled': p.is_disabled('#fgo'), 'note': p.inner_text('#fnote')})
        shot(p, f'qa/forecast-{tag}.png', el=fsec)
        shot(p, f'qa/dashboard-{tag}-1440-full.png')

# ------------------------------------------------------------------ E: error states
with env(width=1440, height=900) as e:
    p = e.goto()
    def try_file(path, tag, **kw):
        p.set_input_files('#file', str(path)); p.wait_for_function("document.querySelector('#uerr').textContent.length>0 && !document.querySelector('#uerr .spin') || document.querySelector('#app').style.display==='grid'")
        p.wait_for_timeout(500)
        txt = p.inner_text('#uerr'); shot(p, f'qa/err-upload-{tag}.png', full=False)
        note(f'err.upload.{tag}', {'message': txt, 'dashboard_shown': p.evaluate("getComputedStyle(document.querySelector('#app')).display")})
        if p.evaluate("getComputedStyle(document.querySelector('#app')).display") != 'none':
            p.click('#again'); p.wait_for_timeout(200)
    try_file(DATA / 'not_data.txt', 'text-file')
    try_file(DATA / 'empty.csv', 'empty-csv')
    try_file(DATA / 'header_only.csv', 'header-only')
    # corrupt excel
    (ROOT / 'data' / 'fake.xlsx').write_bytes(b'PK\x03\x04' + b'garbage' * 50)
    try_file(DATA / 'fake.xlsx', 'corrupt-xlsx')
    # binary junk .csv is accepted as a 40-row dataset (!)
    try_file(DATA / 'bad_file.csv', 'binary-junk-accepted')
    # 26 MB file -> 413
    big = pathlib.Path('/home/user/work/ui/data/_big26mb.csv'); big.write_bytes(b'a,b\n' + b'1,2\n' * (26 * 1024 * 1024 // 4 + 10))
    t0 = time.time(); try_file(big, '26mb-too-large'); note('err.upload.26mb.seconds', round(time.time() - t0, 1)); big.unlink()
    # network failure
    p.route('**/api/upload', lambda r: r.abort('connectionrefused'))
    p.reload(); p.evaluate('document.fonts.ready.then(()=>0)')
    p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_timeout(1200)
    note('err.upload.network-down', p.inner_text('#uerr')); shot(p, 'qa/err-upload-network-down.png', full=False)
    # HTTP 500 with HTML body
    p.unroute('**/api/upload'); p.route('**/api/upload', lambda r: r.fulfill(status=500, body='<html>Internal Server Error</html>', content_type='text/html'))
    p.set_input_files('#file', str(DATA / 'donations.csv')); p.wait_for_timeout(1200)
    note('err.upload.http500-html', p.inner_text('#uerr')); shot(p, 'qa/err-upload-http500.png', full=False)
    note('err.log', e.log.summary())

with env(width=1440, height=900) as e:
    p = e.goto(); load_demo(p)
    ask_sec = "section:has(#q)"
    note('err.ask-disabled.hint', p.inner_text('#qerr'))
    note('err.ask-disabled.shot_before_click', shot(p, 'qa/err-ask-disabled-hint.png', el=ask_sec))
    p.fill('#q', 'Which product sold the most?'); p.click('#go'); p.wait_for_timeout(900)
    note('err.ask-disabled.after_ask', p.inner_text('#qerr'))
    note('err.ask-disabled.shot_after_ask', shot(p, 'qa/err-ask-disabled-after-ask.png', el=ask_sec))
    p.click('.chip >> nth=0'); p.wait_for_timeout(900)
    note('err.ask-disabled.after_chip', {'q': p.input_value('#q'), 'err': p.inner_text('#qerr')})
    # expired session
    p.evaluate("sid='deadbeefdeadbeef'")
    p.fill('#q', 'x'); p.click('#go'); p.wait_for_timeout(700)
    note('err.expired.ask', p.inner_text('#qerr')); shot(p, 'qa/err-expired-session-ask.png', el=ask_sec)
    p.click('#fgo'); p.wait_for_timeout(700)
    note('err.expired.forecast', p.inner_text('#ferr')); shot(p, 'qa/err-expired-session-forecast.png', el="section:has(#fchart)")
    note('err.expired.shot_full', shot(p, 'qa/err-expired-session-full.png', full=False))
    # 502 / 429 style errors from /api/ask
    p.evaluate("sid=null")

# ------------------------------------------------------------------ F: empty insights / no-metric states
for fname, tag in [('no_insights.csv', 'no-insights'), ('text_only.csv', 'text-only')]:
    with env(width=1440, height=900) as e:
        p = e.goto(); upload(p, DATA / fname, charts=False, forecast=False)
        note(f'empty.{tag}', {'ins': p.inner_text('#ins'), 'sum': p.inner_text('#sum'), 'recs': p.inner_text('#recs'), 'kpis': p.inner_text('#kpis'),
                              'charts': p.evaluate("document.querySelectorAll('#charts > *').length"), 'meta': p.inner_text('#meta'), 'fnote': p.inner_text('#ferr')})
        shot(p, f'qa/empty-insights-{tag}-1440-full.png'); shot(p, f'qa/empty-insights-{tag}-1440-fold.png', full=False)

# ------------------------------------------------------------------ G: Plotly CDN blocked (what the sandbox really looks like / conference wifi)
with env(width=1440, height=900, plotly='blocked') as e:
    p = e.goto(); p.click('#demo'); p.wait_for_selector('#app', state='visible'); p.wait_for_timeout(1500)
    note('cdn-blocked.typeof_Plotly', p.evaluate('typeof Plotly'))
    note('cdn-blocked.charts_children', p.evaluate("document.querySelectorAll('#charts > *').length"))
    note('cdn-blocked.fchart_html_len', p.evaluate("document.querySelector('#fchart').innerHTML.length"))
    note('cdn-blocked.shot', shot(p, 'qa/cdn-blocked-dashboard-full.png'))
    note('cdn-blocked.log', e.log.summary())
    # same dashboard but a user asks a question -> chart can't draw either
    mock_ask(p, {'sql': 'SELECT product, SUM(amount) AS total FROM data GROUP BY 1 ORDER BY 2 DESC', 'chart': {'type': 'bar', 'x': 'product', 'y': 'total'},
                 'columns': ['product', 'total'], 'rows': [['Hoodie', 6200000], ['Mug', 801000]], 'verified': True, 'answer': 'Hoodie sold the most.', 'caveats': ''})
    ask(p); note('cdn-blocked.ask_log', e.log.summary()['pageerrors'][-2:])

# ------------------------------------------------------------------ H: Google Fonts blocked -> system fallback
with env(width=1440, height=900, fonts='fallback') as e:
    p = e.goto(); load_demo(p)
    note('fonts-fallback.shot', shot(p, 'qa/dashboard-demo-1440-system-font-fallback-fold.png', full=False))
    note('fonts-fallback.hero', None)
    note('fonts-fallback.computed', p.evaluate("getComputedStyle(document.querySelector('.kpi strong')).fontFamily + ' | loaded=' + [...document.fonts].filter(f=>f.status==='loaded').length"))

save_json('flow_results.json', results)
print('DONE')
