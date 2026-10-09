"""README/UI say uploads are 'never saved'. Does Starlette spool big multipart bodies to disk? Poll the server's open fds during a 24 MB upload.
usage: t_spool_to_disk.py BASE PID"""
import sys, os, time, threading, httpx
BASE, PID = sys.argv[1], int(sys.argv[2])
seen = set()
def poll():
    t_end = time.time() + 12
    while time.time() < t_end:
        try:
            for fd in os.listdir(f"/proc/{PID}/fd"):
                try: tgt = os.readlink(f"/proc/{PID}/fd/{fd}")
                except OSError: continue
                if tgt.startswith("/tmp") or "tmp" in tgt.split("/")[1:2]: seen.add(tgt)
        except OSError: pass
        time.sleep(0.005)
th = threading.Thread(target=poll); th.start()
data = open("/home/user/work/qa/fixtures/data/big_under_25mb_wide.csv", "rb").read()
r = httpx.post(BASE + "/api/upload", files={"file": ("x.csv", data)}, timeout=120); th.join()
print("upload status", r.status_code, "| temp files held open by the server during the upload:", sorted(seen) or "none seen")
