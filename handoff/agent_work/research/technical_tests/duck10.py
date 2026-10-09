import duckdb, pandas as pd, time, threading
df = pd.DataFrame({"x":[1,2,3],"y":["a","b","c"], "d": pd.to_datetime(["2026-01-01","2026-02-01","2026-03-01"])})
cfg = {"threads": 2, "memory_limit": "512MB", "max_temp_directory_size": "256MB",
       "autoinstall_known_extensions": False, "autoload_known_extensions": False,
       "allow_community_extensions": False, "allow_unsigned_extensions": False,
       "enable_external_access": False, "lock_configuration": True}
try:
    con = duckdb.connect(":memory:", config=cfg)
    print("connect(config=...) OK")
    con.register("data", df)
    print("register after lock+ext=false OK:", con.execute("select count(*) from data").fetchall())
    print("df via .df():", con.execute("select * from data limit 2").df().shape)
    print("settings:", con.execute("select name,value from duckdb_settings() where name in ('threads','memory_limit','enable_external_access','lock_configuration','autoload_known_extensions','autoinstall_known_extensions','allow_community_extensions','max_temp_directory_size')").fetchall())
    for s in ["SELECT * FROM df", "SELECT * FROM read_csv('/etc/hostname')", "SET enable_external_access=true", "INSTALL httpfs", "ATTACH '/tmp/a.db'", "COPY data TO '/tmp/o.csv'"]:
        try: con.execute(s).fetchall(); print(" ALLOWED", s)
        except Exception as e: print(" blocked:", s, "->", type(e).__name__)
    # cursor() inherits config? 
    cur = con.cursor()
    try: cur.execute("SET memory_limit='8GB'"); print("cursor can change config?! YES")
    except Exception as e: print("cursor SET blocked:", type(e).__name__)
except Exception as e:
    print("connect with config failed:", type(e).__name__, e)
# registering many times/unregister; 
con.unregister("data"); con.register("data", df); print("re-register ok")
# threads: confirm interrupt watchdog pattern from app works with config
t = threading.Timer(1.0, con.interrupt); t.start(); s=time.time()
try: con.execute("SELECT count(*) FROM range(1000000) a, range(1000000) b WHERE a.range+b.range=5").fetchall()
except Exception as e: print("watchdog:", type(e).__name__, "%.2fs"%(time.time()-s))
t.cancel()
