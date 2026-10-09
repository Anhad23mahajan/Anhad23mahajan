"""Does a big /api/upload freeze the whole server (health check, /api/demo, other uploads)?
usage: t_eventloop_block.py BASE"""
import sys, time, threading, httpx
BASE = sys.argv[1]
big = open("/home/user/work/qa/fixtures/data/big_200k.csv", "rb").read()
res = {}
def up():
    t = time.time(); r = httpx.post(BASE + "/api/upload", files={"file": ("big.csv", big)}, timeout=120); res["upload"] = (r.status_code, round(time.time() - t, 2))
th = threading.Thread(target=up); th.start(); time.sleep(1.0)
lat = []
for _ in range(5):
    t = time.time()
    try: httpx.get(BASE + "/api/health", timeout=60); lat.append(round(time.time() - t, 2))
    except Exception as e: lat.append(repr(e))
    time.sleep(0.5)
th.join()
print("health latency while a 200k-row upload is processing:", lat)
print("upload:", res)
t = time.time(); httpx.get(BASE + "/api/health"); print("health when idle:", round(time.time() - t, 3))
