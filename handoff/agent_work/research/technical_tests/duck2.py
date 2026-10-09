import duckdb, pandas as pd, os
D = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/duck"
os.chdir(D)
df = pd.DataFrame({"x":[1,2,3]})
def attempt(con, sql):
    try:
        r = con.execute(sql).fetchall(); return f"OK {str(r)[:50]}"
    except Exception as e:
        return f"{type(e).__name__}: {str(e).splitlines()[0][:100]}"

print("=== B. lock_configuration ===")
con = duckdb.connect(":memory:"); con.register("data", df)
for s in ["SET enable_external_access=false", "SET lock_configuration=true"]: con.execute(s)
for s in ["SET enable_external_access=true", "SET memory_limit='4GB'", "SET threads=8", "SET lock_configuration=false",
          "RESET enable_external_access", "PRAGMA memory_limit='4GB'", "SET allowed_directories=['/']", "SET allowed_paths=['/etc/hostname']",
          "SELECT * FROM duckdb_settings() WHERE name='memory_limit'", "CALL enable_logging()", "SET autoinstall_known_extensions=true", "SET python_enable_replacements=true",
          "SET temp_directory='/tmp/zz'", "SET disabled_filesystems=''", "SET custom_extension_repository='http://evil'", "SET home_directory='/root'"]:
    print(f"  after lock: {s:60s} -> {attempt(con, s)}")

print("=== C. order: must set limits BEFORE lock; allowed_directories before/after ext=false ===")
con = duckdb.connect(":memory:")
print(" set allowed_directories while ext=true:", attempt(con, f"SET allowed_directories=['{D}/']"))
print(" then ext=false:", attempt(con, "SET enable_external_access=false"))
print(" read in allowed dir:", attempt(con, f"SELECT * FROM read_csv('{D}/secret.csv')"))
print(" read outside:", attempt(con, "SELECT * FROM read_csv('/etc/hostname')"))
print(" now try to change allowed_directories (no lock):", attempt(con, "SET allowed_directories=['/']"))
con2 = duckdb.connect(":memory:")
print(" ext=false first, then set allowed_paths:", attempt(con2, "SET enable_external_access=false"), attempt(con2, f"SET allowed_paths=['{D}/secret.csv']"))
print(" read allowed path:", attempt(con2, f"SELECT * FROM read_csv('{D}/secret.csv')"))
print(" path traversal ../ :", attempt(con2, f"SELECT * FROM read_csv('{D}/../duck/secret.csv')"))
print(" symlink case n/a")
# ext=false but can it be re-enabled without lock?
con3 = duckdb.connect(":memory:"); con3.execute("SET enable_external_access=false")
print(" re-enable without lock:", attempt(con3, "SET enable_external_access=true"))
con4 = duckdb.connect(":memory:"); con4.execute("SET enable_external_access=false"); con4.execute("SET lock_configuration=true")
print(" re-enable with lock:", attempt(con4, "SET enable_external_access=true"))
