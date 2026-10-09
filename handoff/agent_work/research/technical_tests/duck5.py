import duckdb, time, threading, resource
def run(label, sql, fire=2.0, presets=("SET memory_limit='300MB'",), fetch="fetchall"):
    con = duckdb.connect(":memory:")
    for p in presets: con.execute(p)
    fired = {}
    def f():
        fired["t"] = time.time(); con.interrupt()
    tm = threading.Timer(fire, f); tm.start()
    t0 = time.time()
    try:
        r = getattr(con.execute(sql), fetch)(); out = f"finished OK {str(r)[:40]}"
    except Exception as e:
        out = f"{type(e).__name__}: {str(e).splitlines()[0][:60]}"
    t1 = time.time(); tm.cancel()
    lat = (t1 - fired["t"]) if "t" in fired else None
    print(f"[{label:38s}] total {t1-t0:6.2f}s | interrupt latency {('%.3fs' % lat) if lat is not None else 'n/a (finished before timer)'} | {out}", flush=True)
    try: con.close()
    except Exception as e: print("   close:", e)

print("interrupt fired at 2.0s in every case", flush=True)
run("unbounded recursive CTE", "WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT count(*) FROM t")
run("cross join 1e6x1e6", "SELECT count(*) FROM range(1000000) a, range(1000000) b WHERE a.range+b.range=5")
run("sum(range(1e12))", "SELECT sum(range) FROM range(1000000000000)")
run("regexp on long string", "SELECT regexp_matches(repeat('a', 5000000) || 'b', '(a+)+$')")
run("many small string repeats (CPU)", "SELECT count(*) FROM range(100000000) t(i) WHERE length(repeat('ab', 100 + i % 5)) > 0")
run("window over 50M rows", "SELECT max(s) FROM (SELECT sum(i) OVER (ORDER BY i ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) s FROM range(50000000) t(i))", presets=("SET memory_limit='2GB'",))
run("single huge repeat (3e9 chars)", "SELECT length(repeat('x', 3000000000))", fire=1.0)
run("list_transform/generate_series big", "SELECT count(*) FROM (SELECT unnest(generate_series(1, 2000000000)))")
run("pre-fire: tiny query", "SELECT 42", fire=1.0)
# interrupt then reuse the same connection?
con = duckdb.connect(":memory:")
tm = threading.Timer(1.0, con.interrupt); tm.start()
try: con.execute("SELECT count(*) FROM range(1000000) a, range(1000000) b WHERE a.range+b.range=5").fetchall()
except Exception as e: print("interrupted:", type(e).__name__)
tm.cancel()
print("connection reusable after interrupt:", con.execute("select 1").fetchall())
# interrupt when idle is a no-op for next query?
con.interrupt()
print("idle interrupt then next query:", con.execute("select 2").fetchall())
print("peak RSS MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
