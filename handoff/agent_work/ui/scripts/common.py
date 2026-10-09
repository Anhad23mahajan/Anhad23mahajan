"""Shared Playwright helpers for the Lumen UI QA scripts.

Run any script with:  /home/user/work/ui/pwvenv/bin/python /home/user/work/ui/scripts/<script>.py
Backend (own port, because :8012 was already taken by another process):
  cd /home/user/Anhad23mahajan/lumen && env -u GEMINI_API_KEY /home/user/work/venv/bin/uvicorn app.main:app --port 8112

Nothing under /home/user/Anhad23mahajan/lumen is modified.  Sandbox constraints handled here:
  * cdn.plot.ly is unreachable  -> plotly-basic-2.35.2 (identical version, from npm) is served through page.route()
  * fonts.googleapis.com / gstatic unreachable -> the same two families (Figtree, Bricolage Grotesque, from
    @fontsource-variable on npm) are served through page.route(), so screenshots look like production.
    Use fonts='fallback' to see what happens with system fonts (or when Google Fonts is blocked).
"""
import os, re, json, glob, time, pathlib, contextlib
from playwright.sync_api import sync_playwright, Page

ROOT = pathlib.Path('/home/user/work/ui')
TAG = os.environ.get('LUMEN_TAG', '')            # e.g. LUMEN_TAG=after LUMEN_URL=http://localhost:8113 -> shots/after/..., after_*.json
SHOTS = ROOT / 'shots' / TAG if TAG else ROOT / 'shots'
DATA = ROOT / 'data'
BASE = os.environ.get('LUMEN_URL', 'http://localhost:8112')
CHROME = sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome'))[0]
PLOTLY_URL_RE = re.compile(r'^https://cdn\.plot\.ly/plotly-basic-2\.35\.2\.min\.js')
PLOTLY_JS = (ROOT / 'vendor/plotly-basic-2.35.2.min.js').read_bytes()
FONT_BRICOLAGE = (ROOT / 'vendor/fonts/bricolage-grotesque-latin-opsz-normal.woff2').read_bytes()
FONT_FIGTREE = (ROOT / 'vendor/fonts/figtree-latin-wght-normal.woff2').read_bytes()
FONT_CSS = ("@font-face{font-family:'Bricolage Grotesque';font-style:normal;font-weight:200 800;font-display:swap;"
            "src:url(https://fonts.gstatic.com/s/lumenlocal/bricolage.woff2) format('woff2')}"
            "@font-face{font-family:'Figtree';font-style:normal;font-weight:300 900;font-display:swap;"
            "src:url(https://fonts.gstatic.com/s/lumenlocal/figtree.woff2) format('woff2')}")


class Log:
    """Everything the page does that a QA engineer cares about."""
    def __init__(self):
        self.console, self.pageerrors, self.failed, self.responses, self.requests = [], [], [], [], []
        self.t0 = time.time()

    def summary(self):
        return {
            'console_errors': [m for m in self.console if m['type'] == 'error'],
            'console_warnings': [m for m in self.console if m['type'] == 'warning'],
            'pageerrors': self.pageerrors,
            'failed_requests': self.failed,
            'http_errors': [r for r in self.responses if r['status'] >= 400],
        }


def attach_log(page: Page) -> Log:
    log = Log()
    page.on('console', lambda m: log.console.append({'type': m.type, 'text': m.text[:400], 'loc': (m.location or {}).get('url', '')[-80:]}))
    page.on('pageerror', lambda e: log.pageerrors.append(str(e)[:400]))
    page.on('requestfailed', lambda r: log.failed.append({'url': r.url[:140], 'err': (r.failure or '')}))
    page.on('request', lambda r: log.requests.append({'url': r.url, 'type': r.resource_type, 'method': r.method}))
    page.on('response', lambda r: log.responses.append({'url': r.url, 'status': r.status}))
    return log


def setup_routes(page: Page, plotly='local', fonts='local'):
    """plotly: 'local' | 'blocked' (simulates offline / captive-portal / conference wifi)
       fonts : 'local' | 'fallback' (Google Fonts blocked -> system fonts)"""
    def plotly_h(route):
        if plotly == 'blocked': return route.abort('internetdisconnected')
        route.fulfill(status=200, body=PLOTLY_JS, headers={'content-type': 'application/javascript', 'access-control-allow-origin': '*', 'cache-control': 'public, max-age=31536000'})
    def fcss_h(route):
        if fonts == 'fallback': return route.abort('internetdisconnected')
        route.fulfill(status=200, body=FONT_CSS, headers={'content-type': 'text/css'})
    def fgs_h(route):
        if fonts == 'fallback': return route.abort('internetdisconnected')
        body = FONT_BRICOLAGE if 'bricolage' in route.request.url else FONT_FIGTREE
        route.fulfill(status=200, body=body, headers={'content-type': 'font/woff2', 'access-control-allow-origin': '*'})
    page.route(PLOTLY_URL_RE, plotly_h)
    page.route(re.compile(r'^https://fonts\.googleapis\.com/'), fcss_h)
    page.route(re.compile(r'^https://fonts\.gstatic\.com/'), fgs_h)


class Env:
    def __init__(self, pw, width=1440, height=900, scale=1, plotly='local', fonts='local', mobile=False, bypass_csp=True, **ctx_kw):
        self.browser = pw.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--disable-dev-shm-usage'])
        self.ctx = self.browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=scale, is_mobile=mobile, has_touch=mobile, bypass_csp=bypass_csp, **ctx_kw)
        self.page = self.ctx.new_page()
        self.log = attach_log(self.page)
        setup_routes(self.page, plotly, fonts)
        self.page.set_default_timeout(20000)

    def goto(self, path='/'):
        self.page.goto(BASE + path, wait_until='load')
        self.page.evaluate('document.fonts.ready.then(()=>0)')
        return self.page

    def close(self):
        self.ctx.close(); self.browser.close()


@contextlib.contextmanager
def env(**kw):
    with sync_playwright() as pw:
        e = Env(pw, **kw)
        try: yield e
        finally: e.close()


# ---------------------------------------------------------------- page actions
def wait_dashboard(page: Page, charts=True, forecast=True, settle=500):
    page.wait_for_selector('#app', state='visible')
    if charts: page.wait_for_function("document.querySelectorAll('#charts .js-plotly-plot').length>0 || (window.Plotly===undefined)")
    if forecast: page.wait_for_function("document.querySelector('#fchart.js-plotly-plot')!==null || document.querySelector('#ferr').textContent.length>0 || window.Plotly===undefined")
    page.evaluate('document.fonts.ready.then(()=>0)')
    page.wait_for_timeout(settle)


def load_demo(page: Page, **kw):
    page.click('#demo'); wait_dashboard(page, **kw)


def upload(page: Page, path, **kw):
    page.set_input_files('#file', str(path)); wait_dashboard(page, **kw)


def shot(page: Page, name: str, full=True, clip=None, el=None, sub=None):
    """Save a PNG under shots/ (name may include a sub-folder) and return its path."""
    p = SHOTS / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if el is not None:
        page.locator(el).first.screenshot(path=str(p))
    elif clip is not None:
        page.screenshot(path=str(p), clip=clip, full_page=True)
    else:
        page.screenshot(path=str(p), full_page=full)
    return str(p)


def box(page, selector):
    b = page.locator(selector).first.bounding_box()
    return b


def clip_around(page, selector, pad=0):
    page.locator(selector).first.scroll_into_view_if_needed()
    b = page.evaluate("""s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.left+scrollX,y:r.top+scrollY,width:r.width,height:r.height}}""", selector)
    return {'x': max(0, b['x'] - pad), 'y': max(0, b['y'] - pad), 'width': b['width'] + 2 * pad, 'height': b['height'] + 2 * pad}


def mock_ask(page: Page, payload=None, status=200, delay_ms=0, handler=None):
    """Intercept /api/ask. payload mirrors llm.answer(): sql, chart{type,x,y}, columns, rows, verified, answer, caveats."""
    def h(route):
        if handler: return handler(route)
        if delay_ms: time.sleep(delay_ms / 1000)
        route.fulfill(status=status, content_type='application/json', body=json.dumps(payload))
    page.route('**/api/ask', h)


def ask(page: Page, q='What were total sales?', wait=True):
    page.fill('#q', q); page.click('#go')
    if wait: page.wait_for_function("document.querySelector('#ans .a')!==null || document.querySelector('#qerr').textContent.length>0")
    page.wait_for_timeout(700)


def save_json(name, obj):
    p = ROOT / (f'{TAG}_{name}' if TAG else name)
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str))
    return p


def hide_scroll_clip(page):
    """For cropped screenshots only: let the sticky <aside> show all its content (it is max-height:100vh-28px; overflow:auto)."""
    page.add_style_tag(content='aside{max-height:none!important;overflow:visible!important;position:static!important}')
