import sys, time, resource, json, threading
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import duckdb, pandas as pd
import app.llm as llm

name, sql, mem_limit, timeout = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
s = llm.guard(sql)
con = duckdb.connect(":memory:")
con.register("data", pd.DataFrame({"a": [1, 2, 3]}))
con.execute("SET enable_external_access=false")
con.execute(f"SET memory_limit='{mem_limit}'")
con.execute("SET lock_configuration=true")
timer = threading.Timer(timeout, con.interrupt); timer.start()
t0 = time.time()
try:
    res = con.execute(f"SELECT * FROM ({s}) LIMIT 1000").df()
    status, shape, err = "EXECUTED", list(res.shape), ""
except Exception as e:
    status, shape, err = f"ERROR:{type(e).__name__}", None, str(e)[:200]
finally:
    timer.cancel(); con.close()
elapsed = time.time() - t0
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
print(json.dumps({"name": name, "mem_limit": mem_limit, "status": status, "elapsed_s": round(elapsed, 2),
                   "peak_rss_mb": round(peak, 1), "shape": shape, "err": err}))
