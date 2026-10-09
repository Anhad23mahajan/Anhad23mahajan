import sys, time, resource
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from fastapi.testclient import TestClient
import app.main as M
client = TestClient(M.app)
size_mb = 500
size = size_mb*1024*1024
t0=time.time()
r = client.post("/api/upload", files={"file": ("big.csv", b"a"*size, "text/csv")})
t1=time.time()
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0
print(f"upload size={size_mb}MB -> status={r.status_code} time={t1-t0:.2f}s peak_rss={peak:.0f}MB (ratio {peak/size_mb:.1f}x)")
