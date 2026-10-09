import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
with env(width=1440, height=900) as e:
    p = e.goto()
    print('title', p.title(), 'Plotly' , p.evaluate('typeof Plotly'), 'fonts', p.evaluate("[...document.fonts].map(f=>f.family+':'+f.status)"))
    shot(p, 'smoke/hero.png', full=False)
    load_demo(p)
    shot(p, 'smoke/demo.png')
    print(json.dumps(e.log.summary(), indent=1)[:1500])
    print(p.evaluate("[...document.querySelectorAll('#charts .js-plotly-plot')].length"))
