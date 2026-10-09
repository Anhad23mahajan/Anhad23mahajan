import duckdb, pandas as pd
con = duckdb.connect(":memory:")
con.execute("SET enable_external_access=false")
con.execute("SET lock_configuration=true")
df = pd.DataFrame({"a":[1,2]})
con.register("data", df)

# Does query() support ;-separated multi-statement at all, bare, no wrapper?
for sql in [
    "select * from query('SET memory_limit=\"999MB\"; SELECT 1 as ok')",
    "select * from query('SELECT 1 as a; SELECT 2 as b')",
    "select * from query('select * from read_csv(''/etc/hostname'')')",
]:
    print("="*70); print(sql)
    try:
        print(con.execute(sql).df())
    except Exception as e:
        print("ERR", type(e).__name__, e)

# Also: does lock_configuration actually block SET after being set, even via query()/pragma?
print("="*70, "direct SET after lock_configuration=true")
try:
    con.execute("SET enable_external_access=true")
    print("SET succeeded(!)")
except Exception as e:
    print("SET blocked:", type(e).__name__, e)
