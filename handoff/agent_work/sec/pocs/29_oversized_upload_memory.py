import sys, time, resource
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from fastapi.testclient import TestClient
import app.main as M

client = TestClient(M.app)

for size_mb in [30, 200]:
    size = size_mb * 1024 * 1024
    t0 = time.time()
    r = client.post("/api/upload", files={"file": ("big.csv", b"a" * size, "text/csv")})
    t1 = time.time()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    print(f"upload size={size_mb}MB -> status={r.status_code} body={r.json()} "
          f"time={t1-t0:.2f}s peak_rss_so_far={peak:.0f}MB")
