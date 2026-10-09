import duckdb, pandas as pd
SECRET_GLOBAL = pd.DataFrame({"s":["other user's data"]})   # module-level global (like another request's df)
def inner(con, sql):
    return con.execute(sql).fetchall()
def run(sql, presets=(), via_helper=False):
    local_df = pd.DataFrame({"s":["local var"]})
    con = duckdb.connect(":memory:")
    for p in presets: con.execute(p)
    try:
        return (inner(con, sql) if via_helper else con.execute(sql).fetchall())
    except Exception as e:
        return f"{type(e).__name__}: {str(e).splitlines()[0][:80]}"
print("=== replacement scans (SELECT * FROM <python var>) ===")
for label, presets in [("default",[]),("python_enable_replacements=false",["SET python_enable_replacements=false"]),("enable_external_access=false",["SET enable_external_access=false"]), ("python_scan_all_frames=true",["SET python_scan_all_frames=true"])]:
    print(f" {label:34s} local_df: {run('select * from local_df', presets)}")
    print(f" {'':34s} SECRET_GLOBAL: {run('select * from SECRET_GLOBAL', presets)}")
    print(f" {'':34s} local_df via helper frame: {run('select * from local_df', presets, via_helper=True)}")
