# Paste right after `app = FastAPI(title="Lumen")` in app/main.py.   (effort S, risk low)
# ---8<---
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1024)      # index.html 25 KB -> 8 KB, plotly 1.07 MB -> 354 KB

# A strict CSP is also a verifiable "private by default" claim: the browser itself refuses to talk to any third party.
# Plotly needs inline <style> (SVG style attributes) but NOT unsafe-eval.
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")


@app.middleware("http")
async def security_and_cache_headers(request, call_next):
    resp = await call_next(request)
    resp.headers["Content-Security-Policy"] = CSP
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/assets/vendor/"):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp
