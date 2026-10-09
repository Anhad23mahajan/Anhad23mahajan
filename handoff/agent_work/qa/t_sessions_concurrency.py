"""Session eviction + concurrency + memory per big session. usage: t_sessions_concurrency.py BASE SERVER_PID"""
import sys, time, json, os, concurrent.futures as cf, httpx
BASE, PID = sys.argv[1], int(sys.argv[2])
D = "/home/user/work/qa/fixtures/data/"
small = open(D + "clean.xlsx", "rb").read(); csv = open(D + "donations.csv", "rb").read()
def rss(): return int([l for l in open(f"/proc/{PID}/status") if l.startswith("VmRSS")][0].split()[1]) // 1024
def up(data, name="a.csv"):
    t = time.time(); r = httpx.post(BASE + "/api/upload", files={"file": (name, data)}, timeout=300); return r.status_code, (r.json().get("session_id") if r.status_code == 200 else r.text[:100]), round(time.time() - t, 2)
def alive(sid):
    r = httpx.post(BASE + "/api/forecast", json={"session_id": sid, "date_col": "date", "value_col": "amount", "periods": 3}, timeout=60); return r.status_code
print("RSS at start MB:", rss())
# --- eviction: first session, then N more uploads
first = up(csv)[1]; sids = [first]
print("first session alive:", alive(first))
for i in range(1, 60):
    sids.append(up(csv)[1])
    if alive(first) == 400 and "first_evicted_after" not in globals():
        first_evicted_after = i; print(f"first session evicted after {i} additional uploads (i.e. {i+1} total sessions created)")
        break
alive_n = sum(1 for s in sids if alive(s) == 200); print("sessions still alive among those created:", alive_n, "of", len(sids))
# --- FIFO not LRU: keep touching session X (simulating an active user) while others upload
active = up(csv)[1]
for i in range(60):
    up(csv)
    if i % 5 == 0: pass
    # the 'active' user keeps using their session every iteration
    st = alive(active)
    if st != 200: print(f"ACTIVE user's session evicted although in continuous use; after {i+1} other uploads (status {st})"); break
else: print("active session survived 60 uploads")
# --- failed uploads still consume a slot? (start_session registers before profile/insights run)
import importlib, sys as _s
# --- concurrency: 10 parallel small uploads
t = time.time()
with cf.ThreadPoolExecutor(10) as ex: out = list(ex.map(lambda _: up(csv), range(10)))
print("10 parallel donations.csv uploads: wall", round(time.time() - t, 2), "statuses", sorted({o[0] for o in out}), "distinct sids", len({o[1] for o in out}), "latencies", sorted(o[2] for o in out))
# --- memory per big session
big = open(D + "big_200k.csv", "rb").read(); r0 = rss()
for i in range(3): up(big)
print(f"RSS after 3 x 200k-row sessions: +{rss() - r0} MB  (~{(rss() - r0)//3} MB per session); total {rss()} MB")
# --- 5 parallel big uploads: serialisation
t = time.time()
with cf.ThreadPoolExecutor(5) as ex: out = list(ex.map(lambda _: up(big), range(5)))
print("5 parallel 200k uploads: wall", round(time.time() - t, 2), "latencies", sorted(o[2] for o in out), "RSS", rss())
