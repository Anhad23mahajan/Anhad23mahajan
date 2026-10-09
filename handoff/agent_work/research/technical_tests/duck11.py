import duckdb, pandas as pd, threading, time
df = pd.DataFrame({"x":[1,2,3],"y":["a","b","c"], "d": pd.to_datetime(["2026-01-01","2026-02-01","2026-03-01"])})
cfg = {"threads": 2, "memory_limit": "512MB", "autoload_known_extensions": False, "autoinstall_known_extensions": False, "allow_community_extensions": False}
con = duckdb.connect(":memory:", config=cfg)
for stmt in ["SET temp_directory=''", "SET disabled_filesystems='LocalFileSystem'", "SET enable_external_access=false", "SET lock_configuration=true"]:   # ORDER MATTERS
    con.execute(stmt)
con.register("data", df)
print("select:", con.execute("select y, sum(x) s, date_trunc('month', d) m from data group by all order by m").df().shape)
print(".df() ok; stmt types:", [s.type.name for s in con.extract_statements("select 1")])
for s in ["SELECT * FROM df", "SELECT * FROM read_csv('/etc/hostname')", "SELECT * FROM '/etc/hostname'", "COPY data TO '/tmp/o.csv'", "INSTALL httpfs", "LOAD spatial", "ATTACH '/tmp/a.db'", "SET threads=8", "SELECT * FROM glob('/*')", "SELECT * FROM sniff_csv('/etc/hostname')", "SELECT * FROM read_text('/etc/hostname')", "PRAGMA database_list", "SELECT * FROM duckdb_settings() WHERE name='memory_limit'"]:
    try: r = con.execute(s).fetchall(); print(" ALLOWED :", s, str(r)[:50])
    except Exception as e: print(" blocked :", s, "->", type(e).__name__, str(e).splitlines()[0][:80])
print("spill disabled -> sort 30M under 512MB:", end=" ")
try: print(con.execute("SELECT count(*) FROM (SELECT i, random() r FROM range(30000000) t(i) ORDER BY r)").fetchall())
except Exception as e: print(type(e).__name__, str(e).splitlines()[0][:100])
t = threading.Timer(1.0, con.interrupt); t.start(); s = time.time()
try: con.execute("WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT count(*) FROM t").fetchall()
except Exception as e: print("watchdog:", type(e).__name__, "%.2fs" % (time.time()-s))
t.cancel(); print("reusable:", con.execute("select count(*) from data").fetchall())
