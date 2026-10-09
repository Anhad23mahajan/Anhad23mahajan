import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from fastapi.testclient import TestClient
import app.main as M

client = TestClient(M.app)

print("=== CORS preflight probe ===")
r = client.options("/api/ask", headers={"Origin":"https://evil.example", "Access-Control-Request-Method":"POST"})
print("status:", r.status_code, "headers:", dict(r.headers))

print()
print("=== Actual cross-origin GET with Origin header ===")
r2 = client.get("/api/health", headers={"Origin":"https://evil.example"})
print("status:", r2.status_code, "ACAO header present:", "access-control-allow-origin" in {k.lower() for k in r2.headers})

print()
print("=== error message leakage: bad session id ===")
r3 = client.post("/api/ask", json={"session_id":"nonexistent","question":"x"})
print(r3.status_code, r3.json())

print()
print("=== error message leakage: malformed upload ===")
r4 = client.post("/api/upload", files={"file": ("bad.csv", b"\xff\xfe\x00not-utf8-garbage\x00\x01\x02", "text/csv")})
print(r4.status_code, r4.json())

print()
print("=== error message leakage: upload too large ===")
big = b"a,b\n" + b"1,2\n"*1 
r5 = client.post("/api/upload", files={"file": ("big.csv", b"x"*(26*1024*1024), "text/csv")})
print(r5.status_code, r5.json())
