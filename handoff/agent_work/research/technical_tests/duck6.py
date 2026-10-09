import duckdb, time, threading, resource, sys
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
def run(label, sql, fire=2.0, presets=("SET memory_limit='300MB'",)):
    con = duckdb.connect(":memory:")
    for p in presets: con.execute(p)
    fired = {}
    def f(): fired["t"] = time.time(); con.interrupt()
    tm = threading.Timer(fire, f); tm.start(); t0 = time.time()
    try: r = con.execute(sql).fetchall(); out = f"finished OK {str(r)[:40]}"
    except Exception as e: out = f"{type(e).__name__}: {str(e).splitlines()[0][:70]}"
    t1 = time.time(); tm.cancel()
    lat = (t1 - fired["t"]) if "t" in fired else None
    print(f"[{label:34s}] total {t1-t0:6.2f}s | latency {('%.3fs' % lat) if lat is not None else 'n/a'} | {out}", flush=True)
    con.close()
run("generate_series unnest 2e9", "SELECT count(*) FROM (SELECT unnest(generate_series(1, 2000000000)))")
run("pre-fire: tiny query", "SELECT 42", fire=1.0)
run("list_reduce heavy", "SELECT list_sum(list_transform(range(100000000), x -> x*2))")
con = duckdb.connect(":memory:")
tm = threading.Timer(1.0, con.interrupt); tm.start()
try: con.execute("SELECT count(*) FROM range(1000000) a, range(1000000) b WHERE a.range+b.range=5").fetchall()
except Exception as e: print("interrupted:", type(e).__name__)
tm.cancel()
print("connection reusable after interrupt:", con.execute("select 1").fetchall())
con.interrupt()
print("idle interrupt then next query:", con.execute("select 2").fetchall())
print("peak RSS MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
