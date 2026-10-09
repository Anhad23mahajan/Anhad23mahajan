"""Task 3: functional bug repros for static/index.html -> bugs.json (+ shots/bugs/*.png).
Run: /home/user/work/ui/pwvenv/bin/python /home/user/work/ui/scripts/04_bugs.py
Races are produced by an in-page fetch wrapper (window.__delayFn) so no Python-side blocking is involved.
"""
import sys, traceback; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *

M = json.loads((ROOT / 'mocks.json').read_text())
B = {}
def rec(k, v): B[k] = v; print('==', k, '\n  ', json.dumps(v, ensure_ascii=False, default=str)[:700])

DELAY_INIT = """(() => { const of = window.fetch; window.__delayFn = null; window.__calls = [];
  window.fetch = async (u, o) => { u = String(u); let tag = ''; try { if (o && o.body && typeof o.body === 'string') tag = JSON.parse(o.body).question || ''; else if (o && o.body && o.body.get) tag = o.body.get('file').name } catch (e) {}
    window.__calls.push([u, tag, Math.round(performance.now())]); const d = window.__delayFn ? window.__delayFn(u, tag) : 0; if (d) await new Promise(r => setTimeout(r, d)); return of(u, o) } })();"""

def fresh(p_env_kw=None, **kw):
    return env(**(p_env_kw or {}), **kw)

def guarded(name, fn):
    try: fn()
    except Exception as ex: rec(name + '.TEST_ERROR', traceback.format_exc()[-600:])

# ---------------------------------------------------------------- fmt() / esc() / date regex: evaluate the page's own functions
def t_fmt():
    with env() as e:
        p = e.goto()
        cases = [0, 0.05, 0.0536, 0.5, 1, 12.345, 999.96, 1000, 1234, 9999.5, 10000, 10500, -10500, 12500, -12500, 99999, 999999, 1000000, 1500000, 9960000, 10000000, 2548000000, 1e12, -0.5, -0.4, -999.96, 4802950, 9046, 'NaN', None, '12', 'abc', True]
        out = []
        for c in cases:
            r = p.evaluate("""c => { try { const v = c === 'NaN' ? NaN : c; return String(fmt(v)) } catch (e) { return 'THROWS ' + e.message } }""", c)
            out.append([c, r])
        rec('fmt_table', out)
        rec('kpi_delta_zero_negative', p.evaluate("[(-0.3).toFixed(0), (0.4).toFixed(0), (-0.0).toFixed(0)]"))
        rec('esc_table', p.evaluate("""['<', '>', '&', '"', "'", '`', null, undefined, 0, 'a&amp;b'].map(s => [String(s), esc(s)])"""))
        rec('date_regex', p.evaluate("""['2024-01-01T00:00:00','2024-01-01','2024-25','2023-24 season','2024-Q1','Jan 2024','01/02/2024','2024','1234-56-AB','2024-W05','12-2024'].map(s => [s, /^\\d{4}-\\d{2}/.test(s)])"""))
        # static scan of innerHTML templates: which ${...} interpolations are NOT passed through esc()
        src = pathlib.Path('/home/user/Anhad23mahajan/lumen/static/index.html').read_text()
        sinks = []
        for m in re.finditer(r'(innerHTML\s*=|\.innerHTML\s*=\s*|html\s*\+?=)\s*(.*)', src):
            pass
        interps = re.findall(r'\$\{([^{}]|\{[^{}]*\})*\}', src)  # crude: capture whole ${...}
        allx = [m.group(0) for m in re.finditer(r'\$\{(?:[^{}]|\{[^{}]*\})*\}', src)]
        unesc = sorted({x for x in allx if 'esc(' not in x})
        rec('template_interpolations_without_esc', unesc)
        rec('template_interpolation_count', {'total': len(allx), 'without_esc': len(unesc)})
guarded('fmt', t_fmt)

# ---------------------------------------------------------------- 422 -> [object Object]; periods handling
def t_forecast_invalid():
    with env() as e:
        p = e.goto(); load_demo(p)
        p.fill('#fp', '2.5')
        with p.expect_response('**/api/forecast') as r: p.click('#fgo')
        p.wait_for_timeout(300)
        rec('forecast_float_periods', {'http': r.value.status, 'ui_error_text': p.inner_text('#ferr'), 'server_detail_type': type(r.value.json()['detail']).__name__})
guarded('forecast_invalid', t_forecast_invalid)

# ---------------------------------------------------------------- double-click / Enter-spam on Ask; stale answers
def t_ask_races():
    with env() as e:
        p = e.page; p.add_init_script(DELAY_INIT); p.goto(BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); load_demo(p)
        def route_q(route):
            q = json.loads(route.request.post_data)['question']; payload = dict(M['bar']); payload['answer'] = f'ANSWER FOR {q}'
            route.fulfill(status=200, content_type='application/json', body=json.dumps(payload))
        p.route('**/api/ask', route_q)
        # (a) real double click with the mouse
        p.evaluate("window.__calls.length = 0"); p.fill('#q', 'dbl'); p.dblclick('#go', force=True); p.wait_for_timeout(1500)
        rec('ask_dblclick_mouse_requests', len([c for c in p.evaluate('window.__calls') if '/api/ask' in c[0]]))
        # (b) stale answer: slow A then fast B
        p.evaluate("window.__calls.length = 0; window.__delayFn = (u, t) => (u.includes('/api/ask') && t === 'A-slow') ? 1800 : 0; 0")
        p.fill('#q', 'A-slow'); p.press('#q', 'Enter'); p.wait_for_timeout(150)
        p.fill('#q', 'B-fast'); p.press('#q', 'Enter'); p.wait_for_timeout(2600)
        rec('ask_stale_answer_overwrites_newer', {'question_box': p.input_value('#q'), 'answer_shown': p.inner_text('#ans .a'), 'requests': [c[1] for c in p.evaluate('window.__calls')]})
        shot(p, 'bugs/stale-answer.png', el='section:has(#q)')
        # (c) answer for dataset A lands on dataset B's dashboard
        p.evaluate("window.__calls.length = 0; window.__delayFn = (u, t) => (u.includes('/api/ask') && t === 'DEMO-Q') ? 2200 : 0; 0")
        p.fill('#q', 'DEMO-Q'); p.press('#q', 'Enter'); p.wait_for_timeout(200)
        p.click('#again'); p.set_input_files('#file', str(DATA / 'donations.csv')); wait_dashboard(p)
        before = p.inner_text('#ans'); p.wait_for_timeout(2500)
        rec('ask_answer_from_previous_dataset_after_switch', {'ans_before_arrival': before, 'ans_after_arrival': p.inner_text('#ans')[:140], 'dashboard_meta': p.inner_text('#meta'), 'q_input_persisted': p.input_value('#q')})
        shot(p, 'bugs/stale-answer-after-dataset-switch.png', full=False)
guarded('ask_races', t_ask_races)

def t_upload_race():
    with env() as e:
        p = e.page; p.add_init_script(DELAY_INIT); p.goto(BASE + '/'); p.evaluate('document.fonts.ready.then(()=>0)')
        p.evaluate("window.__delayFn = (u, t) => (u.includes('/api/upload') && t === 'donations.csv') ? 2500 : 0; 0")
        p.set_input_files('#file', str(DATA / 'donations.csv')); p.wait_for_timeout(250)
        p.set_input_files('#file', str(DATA / 'no_dates.csv')); p.wait_for_timeout(1000)
        mid = p.inner_text('#meta'); p.wait_for_timeout(3500)
        rec('upload_race_first_slow_second_fast', {'shown_after_1s (second file)': mid, 'shown_after_4.5s (final)': p.inner_text('#meta'), 'second_file_was_last_chosen': 'no_dates.csv'})
        rec('busy_drop_zone_accepts_keyboard_and_programmatic_input', {'pointer_events_during_busy': 'none via .busy; keyboard Enter/Space and input.change are unaffected'})
guarded('upload_race', t_upload_race)

# ---------------------------------------------------------------- leaks: resize listeners + detached nodes + heap
def t_leak():
    with sync_playwright() as pw:
        e = Env(pw); p = e.goto(); cdp = e.ctx.new_cdp_session(p)
        def n_resize():
            oid = cdp.send('Runtime.evaluate', {'expression': 'window'})['result']['objectId']
            ls = cdp.send('DOMDebugger.getEventListeners', {'objectId': oid})['listeners']
            return sum(1 for l in ls if l['type'] == 'resize')
        def heap():
            cdp.send('HeapProfiler.collectGarbage'); return round(cdp.send('Runtime.getHeapUsage')['usedSize'] / 1e6, 2)
        rows = [{'cycle': 0, 'resize_listeners': n_resize(), 'plots_in_dom': 0, 'heap_mb': heap()}]
        for i in range(1, 9):
            if i > 1: p.click('#again')
            p.click('#demo'); wait_dashboard(p, settle=300)
            rows.append({'cycle': i, 'resize_listeners': n_resize(), 'plots_in_dom': p.evaluate("document.querySelectorAll('.js-plotly-plot').length"), 'heap_mb': heap()})
        mock_ask(p, M['bar']);
        for i in range(5): ask(p, f'q{i}')
        rows.append({'cycle': 'after 5 asks', 'resize_listeners': n_resize(), 'plots_in_dom': p.evaluate("document.querySelectorAll('.js-plotly-plot').length"), 'heap_mb': heap()})
        rec('leak_resize_listeners_and_heap_per_upload', rows)
        rec('leak_global_drop_listeners', {'window+document listeners for dragover/drop': 'none registered outside #drop (see below)'})
        oid = cdp.send('Runtime.evaluate', {'expression': 'document'})['result']['objectId']
        rec('document_listener_types', sorted({l['type'] for l in cdp.send('DOMDebugger.getEventListeners', {'objectId': oid})['listeners']}))
        oid = cdp.send('Runtime.evaluate', {'expression': 'window'})['result']['objectId']
        rec('window_listener_types', sorted({l['type'] for l in cdp.send('DOMDebugger.getEventListeners', {'objectId': oid})['listeners']}))
        e.close()
guarded('leak', t_leak)

# ---------------------------------------------------------------- resize responsiveness
def t_resize():
    with env(width=1440, height=900) as e:
        p = e.goto(); load_demo(p)
        res = []
        for w in [1440, 1100, 820, 600, 390, 1440]:
            p.set_viewport_size({'width': w, 'height': 900}); p.wait_for_timeout(900)
            res.append({'viewport': w, 'plots': p.evaluate("[...document.querySelectorAll('.js-plotly-plot')].map(g=>[Math.round(g._fullLayout.width), Math.round(g.parentElement.getBoundingClientRect().width)])"),
                        'page_hscroll_px': p.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")})
        rec('resize_plot_width_vs_container', res)
guarded('resize', t_resize)

# ---------------------------------------------------------------- #again button behaviour
def t_again():
    with env(width=1440, height=900) as e:
        p = e.goto(); load_demo(p)
        p.fill('#q', 'leftover question'); p.evaluate("document.querySelector('#ans').innerHTML='<p class=a>stale answer</p>'")
        p.evaluate("window.scrollTo(0, document.body.scrollHeight)"); p.wait_for_timeout(300)
        top = p.evaluate("document.querySelector('#again').getBoundingClientRect().bottom")
        sy = p.evaluate("scrollY")
        rec('again_button_not_reachable_when_scrolled', {'scrollY': sy, 'button_bottom_in_viewport_px': round(top), 'header_position': p.evaluate("getComputedStyle(document.querySelector('header')).position")})
        p.evaluate("document.querySelector('#again').click()"); p.wait_for_timeout(300)
        p.evaluate("document.querySelector('#demo').click()"); wait_dashboard(p)
        rec('again_then_reload_dashboard_state_reset', {'q_value': p.input_value('#q'), 'ans_html': p.inner_text('#ans')[:60], 'tab_state': p.evaluate("document.querySelector('.tab.active').innerText")})
guarded('again', t_again)

# ---------------------------------------------------------------- XSS sinks with hostile cell values
def t_xss():
    with env() as e:
        p = e.goto(); dialogs = []; p.on('dialog', lambda d: (dialogs.append(d.message), d.dismiss()))
        upload(p, DATA / 'injection.csv'); p.wait_for_timeout(500)
        rec('xss_injection_csv', {'window.__xss': p.evaluate('window.__xss'), 'dialogs': dialogs, 'pageerrors': e.log.pageerrors,
                                   'td_title_attrs_intact': p.evaluate("[...document.querySelectorAll('#preview-box td[title]')].map(t=>t.getAttribute('title')).filter(t=>/[<>\"']/.test(t)).slice(0,3)"),
                                   'injected_img_or_script_elements_in_page': p.evaluate("document.querySelectorAll('#app img, #app script, #app a[href^=javascript]').length"),
                                   'plotly_labels_innerHTML': p.evaluate("[...document.querySelectorAll('#charts .ytick text')].map(t=>t.innerHTML.slice(0,90))"),
                                   'plotly_rendered_links_in_chart': p.evaluate("document.querySelectorAll('#charts a').length"),
                                   'insight_titles': p.evaluate("[...document.querySelectorAll('.ins b')].map(b=>b.innerText)")})
        shot(p, 'bugs/xss-injection-dashboard.png')
        # mocked ask with html in answer/rows
        mock_ask(p, M['html-in-text']); ask(p, 'x')
        rec('xss_ask_mock', {'window.__xss': p.evaluate('window.__xss'), 'dialogs': dialogs, 'answer_dom_has_script_or_img': p.evaluate("document.querySelectorAll('#ans script, #ans img, #ans b, #ans i').length"),
                              'answer_text': p.inner_text('#ans .a')})
guarded('xss', t_xss)

# ---------------------------------------------------------------- small-valued metrics (rates): KPI + hover rounding + narrative
def t_small():
    with env() as e:
        p = e.goto(); upload(p, DATA / 'small_rates.csv')
        rec('small_rates_kpis', p.evaluate("[...document.querySelectorAll('.kpi')].map(k=>k.innerText.replace(/\\n/g,' | '))"))
        rec('small_rates_summary', p.inner_text('#sum'))
        # hover the line chart in the middle
        p.locator('#charts .js-plotly-plot').first.scroll_into_view_if_needed()
        p.evaluate("Plotly.Fx.hover(document.querySelector('#charts .js-plotly-plot'), [{curveNumber:0, pointNumber:5}]); 0"); p.wait_for_timeout(500)
        hv = p.evaluate("[...document.querySelectorAll('#charts .hoverlayer .hovertext text')].map(t=>t.textContent)")
        rec('small_rates_hover_text_line', hv)
        shot(p, 'bugs/small-rates-kpi-hover.png', clip={'x': 0, 'y': 60, 'width': 1440, 'height': 760})
        # bar label for small values
        rec('small_rates_bar_labels', p.evaluate("[...document.querySelectorAll('#charts .barlayer text')].map(t=>t.textContent)"))
guarded('small', t_small)

# ---------------------------------------------------------------- starter charts with negatives/long labels at two widths
def t_neg_long():
    for w in (1440, 390):
        with env(width=w, height=900) as e:
            p = e.goto(); upload(p, DATA / 'negatives_long_labels.csv')
            m = p.evaluate("[...document.querySelectorAll('#charts .js-plotly-plot')].map(g=>({w:Math.round(g._fullLayout.width), plot_w:Math.round(g._fullLayout._size.w), left_margin:Math.round(g._fullLayout._size.l), ranges: g._fullLayout.xaxis.range.map(Number).map(x=>+x.toFixed(0)), data_min: Math.min(...(g.data[0].x.length && typeof g.data[0].x[0]==='number' ? g.data[0].x : [0]))}))")
            rec(f'starter_negatives_long_labels_{w}', m)
            bar = p.locator('#charts .js-plotly-plot').nth(1); bar.scroll_into_view_if_needed()
            shot(p, f'bugs/starter-bar-negatives-long-labels-{w}.png', el='section:has(#charts)')
guarded('neg_long', t_neg_long)

# ---------------------------------------------------------------- result table truncation at 50 rows; Enter on IME; long unbroken text
def t_misc():
    with env() as e:
        p = e.goto(); load_demo(p)
        big = dict(M['table']); big['rows'] = [[f'2025-01-{(i % 28) + 1:02d}T00:00:00', 'Hoodie', 'North', 1, 900, 900 + i] for i in range(80)]
        mock_ask(p, big); ask(p, 'x'); p.evaluate("document.querySelector('#ans details').open = true")
        rec('ask_table_rows_rendered_for_80_row_result', {'tr_count_incl_header': p.evaluate("document.querySelectorAll('#ans details table tr').length"), 'note_about_truncation_in_dom': 'showing' in p.inner_text('#ans').lower()})
        rec('ask_input_has_maxlength', p.evaluate("document.querySelector('#q').maxLength"))
        # long unbroken single answer overflow
        mock_ask(p, M['long-unbroken-single']); ask(p, 'y')
        rec('big_text_overflow', p.evaluate("(b=>({scrollW:b.scrollWidth, clientW:b.clientWidth, overflowing: b.scrollWidth>b.clientWidth+1}))(document.querySelector('#ans .big'))"))
        shot(p, 'bugs/big-unbroken-text.png', el='section:has(#q)')
guarded('misc', t_misc)

# ---------------------------------------------------------------- preview: boolean/dates in cleaned view
def t_preview():
    with env() as e:
        p = e.goto(); upload(p, DATA / 'donations.csv')
        rec('preview_cleaned_first_row', p.evaluate("[...document.querySelectorAll('#preview-box tbody tr:first-child td')].map(t=>t.innerText)"))
        p.click('#tab-raw')
        rec('preview_raw_first_row', p.evaluate("[...document.querySelectorAll('#preview-box tbody tr:first-child td')].map(t=>t.innerText)"))
        rec('preview_dtype_labels_shown_to_users', p.evaluate("[...document.querySelectorAll('#preview-box th small')].map(s=>s.innerText)"))
guarded('preview', t_preview)

save_json('bugs.json', B)
print('DONE')
