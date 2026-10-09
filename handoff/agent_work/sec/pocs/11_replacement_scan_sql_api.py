import duckdb, pandas as pd
con = duckdb.connect(":memory:")
con.execute("SET enable_external_access=false")
mydf = pd.DataFrame({"x":[1,2,3]})
print("python_enable_replacements default:", con.execute("select current_setting('python_enable_replacements')").fetchone())

print("--- con.execute('select * from mydf') ---")
try:
    print(con.execute("select * from mydf").df())
except Exception as e:
    print("FAIL:", type(e).__name__, e)

print("--- con.sql('select * from mydf') ---")
try:
    print(con.sql("select * from mydf").df())
except Exception as e:
    print("FAIL:", type(e).__name__, e)
