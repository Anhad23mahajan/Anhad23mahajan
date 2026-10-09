"""Render every mocked /api/ask response type and record errors/overflow. Screenshots -> shots/ask/*.png
Run: /home/user/work/ui/pwvenv/bin/python /home/user/work/ui/scripts/02_ask_mocks.py
(first run build_mocks.py with the backend venv)
"""
import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *

M = json.loads((ROOT / 'mocks.json').read_text())
out = {}

def route_by_question(route):
    q = json.loads(route.request.post_data)['question']
    route.fulfill(status=200, content_type='application/json', body=json.dumps(M[q]))

MEASURE = """() => {
  const a = document.querySelector('#ans'); const big = document.querySelector('#ans .big'); const rc = document.querySelector('#rc');
  const det = document.querySelector('#ans details');
  const tbl = document.querySelector('#ans table');
  const vis = el => { if(!el) return null; const r = el.getBoundingClientRect(); return {w: Math.round(r.width), h: Math.round(r.height)} };
  return {
    ans_text: a.innerText.slice(0, 160).replace(/\\n+/g, ' | '),
    badge: (document.querySelector('#ans .badge')||{}).innerText || null,
    big: big ? big.innerText : null, big_box: vis(big), big_overflow: big ? big.scrollWidth > big.clientWidth + 1 : null,
    chart_box: vis(rc), chart_has_plotly: rc ? !!rc.querySelector('.main-svg') : null,
    details_open: det ? det.open : null, table_visible_without_click: tbl ? (tbl.offsetParent !== null && det && det.open) : null,
    page_hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    section_overflow: a.scrollWidth > a.clientWidth + 1,
    plot_w: rc && rc._fullLayout ? Math.round(rc._fullLayout._size.w) : null, plot_container_w: rc ? Math.round(rc.getBoundingClientRect().width) : null,
    xss: window.__xss || null
  }
}"""

for vp_name, w, h, mobile in [('1440', 1440, 900, False), ('390', 390, 844, False)]:
    with env(width=w, height=h, mobile=mobile) as e:
        p = e.goto(); p.route('**/api/ask', route_by_question); load_demo(p)
        sec = 'section:has(#q)'
        for key in M:
            n_err_before = len(e.log.pageerrors); n_con_before = len(e.log.console)
            p.fill('#q', key); p.click('#go')
            p.wait_for_function("document.querySelector('#ans .a')!==null || document.querySelector('#qerr').textContent.length>0 || document.querySelector('#ans').children.length>0 && !document.querySelector('#ans .spin')")
            p.wait_for_timeout(900)
            m = p.evaluate(MEASURE)
            m['pageerrors'] = e.log.pageerrors[n_err_before:]
            m['console'] = [c for c in e.log.console[n_con_before:] if c['type'] in ('error', 'warning')]
            m['qerr'] = p.inner_text('#qerr')
            p.locator(sec).scroll_into_view_if_needed()
            m['shot'] = shot(p, f'ask/{vp_name}-{key}.png', el=sec)
            if vp_name == '1440' and key in ('table', 'bar', 'longtext', 'unverified', 'line', 'pie'):
                p.evaluate("document.querySelector('#ans details') && (document.querySelector('#ans details').open = true)"); p.wait_for_timeout(300)
                m['shot_details_open'] = shot(p, f'ask/{vp_name}-{key}-sql-open.png', el=sec)
            out[f'{vp_name}.{key}'] = m
            print(vp_name, key, '| big:', m['big'], '| chart:', m['chart_box'], 'plotly:', m['chart_has_plotly'], '| pageerr:', [x[:60] for x in m['pageerrors']], '| con:', [c['text'][:60] for c in m['console']], '| hscroll:', m['page_hscroll'], '| qerr:', m['qerr'][:60])
    out[f'{vp_name}.log'] = e.log.summary()

save_json('ask_mock_results.json', out)
print('DONE')
