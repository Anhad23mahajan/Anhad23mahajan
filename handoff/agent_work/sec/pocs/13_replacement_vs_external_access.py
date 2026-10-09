import duckdb, pandas as pd
mydf = pd.DataFrame({"x":[1,2,3]})

print("=== explicit con, enable_external_access left default (true) ===")
con1 = duckdb.connect(":memory:")
try:
    print(con1.execute("select * from mydf").df())
except Exception as e:
    print("FAIL:", type(e).__name__, e)

print("=== explicit con, enable_external_access=false ===")
con2 = duckdb.connect(":memory:")
con2.execute("SET enable_external_access=false")
try:
    print(con2.execute("select * from mydf").df())
except Exception as e:
    print("FAIL:", type(e).__name__, e)
