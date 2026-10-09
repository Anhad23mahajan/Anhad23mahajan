"""Does the server buffer an entire oversized body in RAM before returning 413? usage: t_big_body.py BASE PID MB"""
import sys, time, threading, httpx, os
BASE, PID, MB = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
def rss(): return int([l for l in open(f"/proc/{PID}/status") if l.startswith("VmRSS")][0].split()[1]) // 1024
peak = [rss()]; stop = False
def poll():
    while not stop: peak[0] = max(peak[0], rss()); time.sleep(0.02)
th = threading.Thread(target=poll); th.start()
def gen():
    chunk = b"date,amount\n" + b"2025-01-01,5\n" * 80000
    for _ in range(MB): yield chunk[:1024 * 1024] if len(chunk) >= 1024 * 1024 else chunk.ljust(1024 * 1024, b"x")
t = time.time()
r = httpx.post(BASE + "/api/upload", files={"file": ("big.csv", b"".join(gen()))}, timeout=300)
dt = time.time() - t; stop = True; th.join()
print(f"upload of {MB} MiB -> {r.status_code} {r.text[:60]} in {dt:.1f}s; server RSS before={peak[0] and rss()} MB, peak during request={peak[0]} MB")
