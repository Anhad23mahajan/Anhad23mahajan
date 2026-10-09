"""Targeted before/after checks against the patched copy (LUMEN_URL=:8113). Writes after_verify.json"""
import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
M = json.loads((ROOT / 'mocks.json').read_text()); R = {}
DELAY = open('/home/user/work/ui/scripts/04_bugs.py').read().split('DELAY_INIT = """')[1].split('"""')[0]
with env() as e:
    p = e.page; p.add_init_script(DELAY); p.goto(BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); load_demo(p)
    p.route('**/api/ask', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({**M['bar'], 'answer': 'ANSWER FOR ' + json.loads(r.request.post_data)['question']})))
    p.evaluate("window.__calls.length=0; window.__delayFn=(u,t)=>(u.includes('/api/ask')&&t==='A-slow')?1800:0; 0")
    p.fill('#q', 'A-slow'); p.press('#q', 'Enter'); p.wait_for_timeout(150); p.fill('#q', 'B-fast'); p.press('#q', 'Enter'); p.wait_for_timeout(2600)
    R['newer_question_supersedes'] = {'answer_shown': p.inner_text('#ans .a'), 'requests': [c[1] for c in p.evaluate('window.__calls')]}
    p.evaluate("window.__calls.length=0; window.__delayFn=null; 0"); p.fill('#q', 'same'); [p.press('#q', 'Enter') for _ in range(3)]; p.wait_for_timeout(1500)
    R['triple_enter_same_question_requests'] = len([c for c in p.evaluate('window.__calls') if '/api/ask' in c[0]])
    # forecast periods
    out = {}
    for v in ['2.5', '0', '', '-3', '100', '7']:
        p.fill('#fp', v)
        with p.expect_response('**/api/forecast') as ri: p.click('#fgo')
        p.wait_for_timeout(300); out[v or '(empty)'] = {'http': ri.value.status, 'field_now': p.input_value('#fp'), 'err': p.inner_text('#ferr'), 'note': p.inner_text('#fnote')[:60]}
    R['forecast_periods'] = out
    # band markers
    p.fill('#fp', '6'); 
    with p.expect_response('**/api/forecast'): p.click('#fgo')
    p.wait_for_timeout(500)
    R['forecast_band_marker_points'] = p.evaluate("document.querySelectorAll('#fchart .scatterlayer .trace:nth-child(2) .points path').length")
    # keyboard busy: 3 presses on forecast button
    cnt = {'n': 0}; p.route('**/api/forecast', lambda r: (cnt.__setitem__('n', cnt['n'] + 1), r.continue_())[-1])
    p.focus('#fgo'); p.keyboard.press('Enter'); p.keyboard.press('Enter'); p.keyboard.press('Space'); p.wait_for_timeout(2500)
    R['forecast_3_keypresses_requests'] = cnt['n']
    # a11y
    R['a11y'] = p.evaluate("""() => ({tabs:[...document.querySelectorAll('.tab')].map(t=>[t.getAttribute('role'),t.getAttribute('aria-selected')]), tablist: !!document.querySelector('[role=tablist]'),
       chart_labels:[...document.querySelectorAll('#charts [role=img]')].map(c=>c.getAttribute('aria-label')), fchart_label:(document.querySelector('#fchart').getAttribute('aria-label')||'').slice(0,90),
       ans_live: document.querySelector('#ans').getAttribute('aria-live'), favicon: !!document.querySelector('link[rel~=icon]'), h3_focus_after_render: null})""")
    p.press('#tab-processed', 'ArrowLeft'); R['arrow_left_selects_raw'] = p.evaluate("document.querySelector('#tab-raw').getAttribute('aria-selected')")
    R['log'] = e.log.summary()
with env() as e:
    p = e.goto(); p.click('#demo'); wait_dashboard(p)
    R['focus_after_render'] = p.evaluate("document.activeElement.id + ' / ' + document.activeElement.tagName")
    p.evaluate("sid='dead'"); p.fill('#q', 'x'); p.click('#go'); p.wait_for_timeout(600); R['expired_ask'] = p.inner_text('#qerr')
    p.click('#fgo'); p.wait_for_timeout(600); R['expired_forecast'] = p.inner_text('#ferr')
    p.unroute_all() if hasattr(p, 'unroute_all') else None
with env() as e:
    p = e.goto(); p.route('**/api/upload', lambda r: r.abort('connectionrefused')); p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_timeout(800)
    R['network_down_message'] = p.inner_text('#uerr')
    p.unroute('**/api/upload'); p.route('**/api/upload', lambda r: r.fulfill(status=500, body='<html>x</html>', content_type='text/html')); p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_timeout(800)
    R['http500_message'] = p.inner_text('#uerr')
# plotly missing (vendored file blocked by a network failure) -> graceful message instead of blank panels
with env() as e:
    p = e.page; p.route(re.compile(r'/assets/vendor/plotly'), lambda r: r.abort('failed')); p.goto(BASE + '/'); p.click('#demo'); p.wait_for_selector('#app', state='visible'); p.wait_for_timeout(1500)
    R['plotly_missing'] = {'charts_text': p.inner_text('#charts'), 'ferr': p.inner_text('#ferr'), 'pageerrors': e.log.pageerrors}
    shot(p, 'plotly-missing-graceful.png')
# disabled forecast + dates-no-metric
with env() as e:
    p = e.goto(); upload(p, DATA / 'dates_no_metric.csv', charts=False, forecast=False)
    R['dates_no_metric_forecast'] = {'disabled': p.is_disabled('#fgo'), 'ferr': p.inner_text('#ferr'), 'btn_bg': p.evaluate("getComputedStyle(document.querySelector('#fgo')).backgroundColor")}
    shot(p, 'forecast-dates-no-metric-disabled.png', el='section:has(#fchart)')
save_json('verify.json', R); print(json.dumps(R, indent=1, ensure_ascii=False)[:5000])
