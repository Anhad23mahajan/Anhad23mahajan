import duckdb, pandas as pd, os, sys
D = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/duck"
os.chdir(D)
df = pd.DataFrame({"x":[1,2,3],"y":["a","b","c"]})

def fresh(*presets, register=True):
    con = duckdb.connect(":memory:")
    if register: con.register("data", df)
    for p in presets: con.execute(p)
    return con

def t(label, presets, sql, register=True):
    try:
        con = fresh(*presets, register=register)
        r = con.execute(sql).fetchall()
        out = f"ALLOWED -> {str(r)[:70]}"
    except Exception as e:
        out = f"BLOCKED -> {type(e).__name__}: {str(e).splitlines()[0][:110]}"
    print(f"[{label}] {sql[:60]!r:64s} {out}")

EA = ["SET enable_external_access=false"]
print("=== A. enable_external_access ===")
for sql in [f"SELECT * FROM read_csv('{D}/secret.csv')", f"SELECT * FROM '{D}/secret.csv'", "SELECT count(*) FROM glob('/etc/*')",
            "SELECT * FROM read_text('/etc/hostname')", f"COPY (SELECT 1) TO '{D}/out.csv'", "INSTALL httpfs", "LOAD json",
            f"ATTACH '{D}/x.duckdb' AS x", "ATTACH ':memory:' AS m2", "SELECT * FROM read_parquet('https://example.com/a.parquet')",
            "SELECT getenv('HOME')", "SELECT * FROM duckdb_settings() LIMIT 1", "SELECT current_setting('enable_external_access')",
            "SELECT * FROM df", "SELECT * FROM data", "PRAGMA database_list", "EXPORT DATABASE '/tmp/xx'",
            "SELECT * FROM duckdb_extensions() LIMIT 1", "SELECT * FROM sniff_csv('/etc/hostname')", "SELECT * FROM read_blob('/etc/hostname')"]:
    t("default ", [], sql)
    t("ext=off ", EA, sql)
