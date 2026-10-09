import duckdb
con = duckdb.connect(":memory:")
con.execute("SET enable_external_access=false")
for sql in ["select read_text('/etc/hostname') as x",
            "select read_blob('/etc/hostname') as x"]:
    print(sql)
    try:
        print(con.execute(sql).fetchall())
    except Exception as e:
        print("ERR", type(e).__name__, e)
    print()

# also with external access ON to see it actually can read as scalar in principle
con2 = duckdb.connect(":memory:")
print("--- external_access default (true) ---")
try:
    print(con2.execute("select read_text('/etc/hostname') as x").fetchall())
except Exception as e:
    print("ERR", type(e).__name__, e)
