import duckdb, time, os, resource, threading
D = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/duck/mem"
os.makedirs(D, exist_ok=True); os.chdir(D)
def run(label, presets, sql, wd=15):
    con = duckdb.connect(":memory:")
    for p in presets: con.execute(p)
    tm = threading.Timer(wd, con.interrupt); tm.start()
    t=time.time()
    try:
        r = con.execute(sql).fetchall(); out=f"OK {str(r)[:60]}"
    except Exception as e:
        out=f"{type(e).__name__}: {str(e).splitlines()[0][:150]}"
    tm.cancel()
    print(f"[{label}] {time.time()-t:5.2f}s {out}", flush=True)
    con.close()
mem = ["SET memory_limit='200MB'"]
print("=== memory_limit (watchdog interrupt at 15s) ===", flush=True)
run("giant string  ", mem, "SELECT length(repeat('x', 1000000000))")
run("list agg 50M  ", mem, "SELECT len(list(i)) FROM range(50000000) t(i)")
run("sort 30M rows ", mem, "SELECT count(*) FROM (SELECT i, random() r FROM range(30000000) t(i) ORDER BY r)")
print(" .tmp created in cwd?", os.path.exists(".tmp"), os.listdir("."), flush=True)
run("ext=false: sort 30M (spill allowed?)", mem+["SET enable_external_access=false"], "SELECT count(*) FROM (SELECT i, random() r FROM range(30000000) t(i) ORDER BY r)")
run("temp_directory='' : sort 30M", mem+["SET temp_directory=''"], "SELECT count(*) FROM (SELECT i, random() r FROM range(30000000) t(i) ORDER BY r)")
run("max_temp_directory_size=1MB: sort 30M", mem+["SET max_temp_directory_size='1MB'"], "SELECT count(*) FROM (SELECT i, random() r FROM range(30000000) t(i) ORDER BY r)")
run("recursive CTE unbounded (count)", mem, "WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT count(*) FROM t")
run("cross join 1e6 x 1e6 filtered count", mem, "SELECT count(*) FROM range(1000000) a, range(1000000) b WHERE a.range+b.range=5")
print("peak RSS MB:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024, flush=True)
