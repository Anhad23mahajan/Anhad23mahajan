"""API edge cases against a live server. usage: t_api_edges.py BASE   (prints a table; no assertions, read the output)"""
import sys, json, time, socket, io, concurrent.futures as cf, httpx
BASE = sys.argv[1]; HOST, PORT = BASE.split("//")[1].split(":"); PORT = int(PORT)
D = "/home/user/work/qa/fixtures/data/"
c = httpx.Client(base_url=BASE, timeout=120)
def show(label, r):
    body = r.text[:230].replace("\n", " ")
    print(f"{label:58s} -> {r.status_code} {body}")
def up(name, fname=None, data=None):
    data = data if data is not None else open(D + name, "rb").read()
    return c.post("/api/upload", files={"file": (fname or name, data)})
sid = up("donations.csv").json()["session_id"]
print("== forecast edge cases")
def fc(label, **kw):
    body = {"session_id": sid, "date_col": "date", "value_col": "amount", "periods": 6}; body.update(kw)
    show(label, c.post("/api/forecast", json=body))
fc("wrong session id", session_id="deadbeef")
fc("nonexistent value col", value_col="nope")
fc("nonexistent date col", date_col="nope")
fc("text value col (campaign)", value_col="campaign")
fc("text value col (donor)", value_col="donor")
fc("date col that is not a date (amount)", date_col="amount")
fc("date col is text (campaign)", date_col="campaign")
fc("value col == date col", value_col="date")
fc("periods=0", periods=0); fc("periods=-5", periods=-5); fc("periods=10**9", periods=10**9); fc("periods=6.5", periods=6.5); fc("periods='abc'", periods="abc")
fc("periods=null", periods=None)
show("forecast missing fields {}", c.post("/api/forecast", json={}))
show("forecast body not json", c.post("/api/forecast", content=b"hello", headers={"content-type": "application/json"}))
r = c.post("/api/forecast", json={"session_id": sid}); print("   422 detail type:", type(r.json().get("detail")).__name__, "(frontend does new Error(j.detail) -> shows:", str(r.json().get("detail"))[:40] + "...)")
print("== ask validation (no key => 503 expected)")
show("ask wrong session", c.post("/api/ask", json={"session_id": "zzz", "question": "hi"}))
show("ask empty question", c.post("/api/ask", json={"session_id": sid, "question": ""}))
show("ask 10k char question", c.post("/api/ask", json={"session_id": sid, "question": "a" * 10000}))
show("ask missing question", c.post("/api/ask", json={"session_id": sid}))
show("ask question=null", c.post("/api/ask", json={"session_id": sid, "question": None}))
print("== upload shape errors")
show("upload field is a string, not a file", c.post("/api/upload", data={"file": "hello"}))
show("upload with no field", c.post("/api/upload", data={"x": "y"}))
show("upload JSON body", c.post("/api/upload", json={"file": "x"}))
show("upload zero-byte file", up("e.csv", data=b""))
show("upload 1 byte", up("e.csv", data=b"a"))
show("upload binary garbage .csv", up("g.csv", data=bytes(range(256)) * 20))
show("upload PDF header", up("x.pdf", data=b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n"))
show("upload JSON file", up("x.json", data=b'[{"date":"2025-01-01","amount":5},{"date":"2025-01-02","amount":6}]'))
show("upload zip containing csv", up("x.zip", data=__import__("zipfile").ZipFile(io.BytesIO(), "w") and (lambda b: (__import__("zipfile").ZipFile(b, "w").writestr("a.csv", "a,b\n1,2\n"), b.getvalue())[1])(io.BytesIO())))
show("upload xlsx-named plain CSV", up("donations.csv", fname="donations.xlsx"))
show("upload csv-named xlsx", up("clean.xlsx", fname="clean.csv"))
show("upload filename=None-ish ('')", up("donations.csv", fname=""))
show("upload filename with path ../../x.csv", up("donations.csv", fname="../../x.csv"))
show("upload tsv", up("tsv.tsv", data=b"date\tamount\n2025-01-01\t5\n2025-01-02\t7\n"))
show("upload pipe-sep", up("p.csv", data=b"date|amount\n2025-01-01|5\n2025-01-02|7\n"))
show("upload no trailing newline single line csv", up("s.csv", data=b"a,b,c"))
show("upload CRLF + quotes", up("crlf.csv", data=b'date,amount,note\r\n2025-01-01,5,"a, b"\r\n2025-01-02,7,"c"\r\n'))
print("== methods / paths")
for m, p in [("HEAD", "/"), ("OPTIONS", "/"), ("HEAD", "/api/health"), ("OPTIONS", "/api/upload"), ("GET", "/api/upload"), ("GET", "/api/demo"), ("DELETE", "/api/upload"), ("GET", "/nonexistent"), ("GET", "/docs"), ("GET", "/openapi.json"), ("GET", "/assets/"), ("GET", "/assets"), ("GET", "/assets/index.html"), ("HEAD", "/assets/index.html")]:
    r = c.request(m, p); print(f"{m:8s}{p:28s} -> {r.status_code} len={len(r.content)} {r.headers.get('content-type','')[:30]} allow={r.headers.get('allow','')}")
print("== /assets traversal (raw socket, no client-side path normalisation)")
def raw(path):
    s = socket.create_connection((HOST, PORT)); s.settimeout(5)
    s.sendall(f"GET {path} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode()); out = b""
    try:
        while True:
            d = s.recv(65536)
            if not d: break
            out += d
    except Exception: pass
    s.close(); head, _, body = out.partition(b"\r\n\r\n"); return head.split(b"\r\n")[0].decode(), len(body), body[:60]
for p in ["/assets/../app/main.py", "/assets/%2e%2e/app/main.py", "/assets/..%2fapp%2fmain.py", "/assets/%2e%2e%2fapp%2fmain.py", "/assets/..%5capp%5cmain.py", "/assets/....//app/main.py",
          "/assets//etc/passwd", "/assets/%2fetc%2fpasswd", "/assets/../../../../etc/passwd", "/assets/%2e%2e/%2e%2e/%2e%2e/etc/passwd", "/assets/..;/app/main.py", "/assets/index.html%00.png",
          "/assets/.%2e/app/main.py", "/assets/%252e%252e/app/main.py", "/..%2fapp%2fmain.py", "/assets/\\..\\app\\main.py"]:
    st, ln, b = raw(p); print(f"{p:50s} -> {st} len={ln} {b[:40]!r}")
