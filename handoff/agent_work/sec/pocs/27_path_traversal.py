import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from fastapi.testclient import TestClient
import app.main as M

client = TestClient(M.app)

paths_to_try = [
    "/assets/index.html",                       # legit baseline
    "/assets/../app/main.py",                     # naive traversal
    "/assets/..%2f..%2fapp%2fmain.py",            # url-encoded traversal
    "/assets/%2e%2e/%2e%2e/app/main.py",
    "/assets/../../etc/passwd",
    "/assets/....//....//etc/passwd",
    "/assets/..\\..\\app\\main.py",
]
for p in paths_to_try:
    r = client.get(p)
    body_preview = r.text[:120].replace("\n"," ")
    print(f"{p!r:55} -> status={r.status_code} len={len(r.text)} preview={body_preview!r}")
