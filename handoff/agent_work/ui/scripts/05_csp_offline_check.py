"""Patched copy (port 8113): with the strict CSP header ACTIVE and BOTH cdn.plot.ly + Google Fonts hard-blocked, does everything still work,
and are there any CSP violations or third-party requests?   Run: pwvenv/bin/python scripts/05_csp_offline_check.py
"""
import sys, os; sys.path.insert(0, '/home/user/work/ui/scripts'); os.environ['LUMEN_URL'] = 'http://localhost:8113'
from common import *
with env(width=1440, height=900, plotly='blocked', fonts='fallback', bypass_csp=False) as e:
    p = e.page
    p.add_init_script("window.__csp=[]; document.addEventListener('securitypolicyviolation', ev => window.__csp.push(ev.violatedDirective + ' ' + ev.blockedURI.slice(0,60)))")
    p.goto(BASE + '/'); p.wait_for_timeout(800)
    p.click('#demo')
    for _ in range(60):
        if p.evaluate("() => document.querySelectorAll('.js-plotly-plot').length") >= 4: break
        p.wait_for_timeout(250)
    p.wait_for_timeout(500)
    # exercise ask (mocked) + forecast change + tab switch under CSP
    M = json.loads((ROOT / 'mocks.json').read_text()); mock_ask(p, M['bar'])
    p.fill('#q', 'x'); p.click('#go'); p.wait_for_timeout(1200)
    p.select_option('#fv', 'quantity'); p.fill('#fp', '12'); p.click('#fgo'); p.wait_for_timeout(1500)
    p.click('#tab-raw'); p.wait_for_timeout(200)
    third = sorted({re.match(r'https?://[^/]+', r['url']).group(0) for r in e.log.requests if re.match(r'https?://', r['url']) and not r['url'].startswith(BASE)})
    res = {'plotly_loaded': p.evaluate("() => typeof Plotly"), 'plots_drawn': p.evaluate("() => document.querySelectorAll('.js-plotly-plot').length"),
           'fonts': p.evaluate("() => [...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family)"),
           'csp_violations': p.evaluate("() => window.__csp"), 'third_party_requests_attempted': third, 'log': e.log.summary(),
           'answer_chart_drawn': p.evaluate("() => !!document.querySelector('#rc .main-svg')")}
    print(json.dumps(res, indent=1))
    shot(p, 'after/csp-offline-dashboard.png', full=False)
    save_json('csp_offline_check.json', res)
