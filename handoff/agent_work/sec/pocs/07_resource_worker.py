import sys, time, resource, json
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

name = sys.argv[1]
sql = sys.argv[2]
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 10
nrows = int(sys.argv[4]) if len(sys.argv) > 4 else 100

df = pd.DataFrame({"a": list(range(nrows)), "b": [f"row{i}" for i in range(nrows)]})

t0 = time.time()
status = "unknown"
err = ""
shape = None
try:
    llm.guard(sql)
except ValueError as e:
    status = "GUARD_BLOCKED"
    err = str(e)
else:
    try:
        res = llm.run_sql(df, sql, timeout=timeout)
        status = "EXECUTED"
        shape = list(res.shape)
    except Exception as e:
        status = f"RUNTIME_ERROR:{type(e).__name__}"
        err = str(e)[:300]
elapsed = time.time() - t0
peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
print(json.dumps({"name": name, "status": status, "elapsed_s": round(elapsed, 2),
                   "peak_rss_mb": round(peak_rss_mb, 1), "shape": shape, "err": err}))
