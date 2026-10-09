import sys, os; sys.path.insert(0, '/home/user/work/ui/scripts'); os.environ['LUMEN_URL'] = 'http://localhost:8113'
from common import *
with env(width=1440, height=900, plotly='blocked', fonts='fallback') as e:      # BOTH CDNs blocked: must still work
    p = e.goto()
    print('Plotly', p.evaluate('typeof Plotly'), 'fonts', p.evaluate("[...document.fonts].map(f=>f.family+':'+f.status)"))
    load_demo(p)
    print('charts', p.evaluate("document.querySelectorAll('.js-plotly-plot').length"))
    third = sorted({re.match(r'https?://[^/]+', r['url']).group(0) for r in e.log.requests if not r['url'].startswith(BASE) and not r['url'].startswith('data:')})
    print('third-party origins requested:', third)
    print(json.dumps(e.log.summary(), indent=1)[:1500])
    shot(p, 'smoke-patched-demo.png')
