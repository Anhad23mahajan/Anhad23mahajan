import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

df = pd.DataFrame({"product":["A","B"], "amount":[1,2]})

tests = [
    ("query() read_csv nested", "select * from query('select * from read_csv(''/etc/passwd'')')"),
    ("query() attach nested", "select * from query('attach '':memory:'' as x2')"),
    ("query() SET nested (try disable external access)", "select * from query('SET enable_external_access=true')"),
    ("query() install nested", "select * from query('INSTALL httpfs')"),
    ("query() pragma nested", "select * from query('PRAGMA enable_external_access=true')"),
    ("query() lock_configuration bypass attempt", "select * from query('SET lock_configuration=false')"),
    ("query() create table nested", "select * from query('CREATE TABLE t2 AS SELECT 1')"),
    ("query() copy nested (exfil attempt)", "select * from query('COPY data TO ''/tmp/exfil.csv''')"),
    ("query_table on information_schema", "select * from query_table('information_schema.tables')"),
    ("query_table on pragma_version", "select * from query_table('pragma_version()')"),
]

for name, sql in tests:
    print("="*80); print(name); print("SQL:", sql)
    try:
        g = llm.guard(sql)
        print("guard: PASSED")
    except ValueError as e:
        print("guard: BLOCKED:", e)
        continue
    try:
        res = llm.run_sql(df, sql, timeout=5)
        print("run_sql: EXECUTED shape=", res.shape)
        print(res.head(5))
    except Exception as e:
        print("run_sql ERROR:", type(e).__name__, e)
