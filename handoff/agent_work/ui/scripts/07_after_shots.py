import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
with env(width=1440, height=900) as e:
    p = e.goto(); upload(p, DATA / 'donations.csv'); shot(p, 'qa/donations-1440-full.png')
    print('aside clipped:', p.evaluate("(a=>[a.scrollHeight,a.clientHeight])(document.querySelector('aside'))"))
for w in (390, 820):
    with env(width=w, height=844) as e:
        p = e.goto(); load_demo(p); shot(p, f'qa/demo-{w}-full.png'); shot(p, f'qa/demo-{w}-fold.png', full=False)
        print(w, p.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]"))
with env(width=390, height=844) as e:
    p = e.goto(); shot(p, 'qa/hero-390.png', full=False)
with env(width=320, height=700) as e:
    p = e.goto(); load_demo(p); print(320, p.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")); shot(p, 'qa/demo-320-fold.png', full=False)
