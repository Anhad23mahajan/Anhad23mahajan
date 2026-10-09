"""Re-test the mobile overflow fix with the CSS present *before* first render (Plotly sizes itself at draw time)."""
import sys; sys.path.insert(0, '/home/user/work/ui/scripts')
from common import *
FIX = sys.argv[1] if len(sys.argv) > 1 else '@media(max-width:960px){#app{grid-template-columns:minmax(0,1fr)}}'
res = {}
for w in [320, 360, 390, 414, 480, 600, 640, 700, 820]:
    with env(width=w, height=900) as e:
        p = e.page
        p.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=%s;document.head.appendChild(s)})" % json.dumps(FIX))
        p.goto(BASE + '/'); load_demo(p)
        r = p.evaluate("""(()=>{const W=document.documentElement.clientWidth;const bad=[];document.querySelectorAll('body *').forEach(el=>{if(el.closest('.js-plotly-plot'))return;const r=el.getBoundingClientRect();if(r.width&&r.right>W+1){let c=false;for(let q=el.parentElement;q&&q!==document.body;q=q.parentElement){if(/(auto|scroll|hidden)/.test(getComputedStyle(q).overflowX)){c=true;break}}if(!c)bad.push(el.tagName.toLowerCase()+(el.id?'#'+el.id:'')+'.'+String(el.className).split(' ')[0]+':'+Math.round(r.right))}});return {sw:document.documentElement.scrollWidth,cw:W,bad:bad.slice(0,5)}})()""")
        res[w] = r
        if w in (390, 320): shot(p, f'qa/dashboard-demo-{w}-WITH-overflow-fix-full.png')
        if w == 390: shot(p, 'qa/dashboard-demo-390-WITH-overflow-fix-fold.png', full=False)
print(json.dumps(res, indent=0))
