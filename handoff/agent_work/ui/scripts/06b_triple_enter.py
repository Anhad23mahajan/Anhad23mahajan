import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
M = json.loads((ROOT / 'mocks.json').read_text())
DELAY = open('/home/user/work/ui/scripts/04_bugs.py').read().split('DELAY_INIT = """')[1].split('"""')[0]
for base in ('http://localhost:8112', 'http://localhost:8113'):
    import common; common.BASE = base
    with env() as e:
        p = e.page; p.add_init_script(DELAY); p.goto(base + '/'); p.evaluate('document.fonts.ready.then(()=>0)'); load_demo(p)
        p.route('**/api/ask', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(M['bar'])))
        p.evaluate("window.__calls.length=0; window.__delayFn=(u,t)=>u.includes('/api/ask')?600:0; 0")
        p.fill('#q', 'same'); [p.press('#q', 'Enter') for _ in range(3)]; p.wait_for_timeout(1800)
        print(base, 'ask requests from 3 Enter presses:', len([c for c in p.evaluate('window.__calls') if '/api/ask' in c[0]]))
