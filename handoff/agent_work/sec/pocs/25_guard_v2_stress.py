import sys
sys.path.insert(0, "/home/user/work/sec")
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import guard_v2
import pandas as pd

df = pd.DataFrame({"a":[1,2,3], "b":["x","y","z"]})

cases = [
    ("subquery-in-select-list hitting read_csv",
     "select (select count(*) from read_csv('/etc/passwd')) as x from data", "REJECT"),
    ("where-in-subquery hitting bad table",
     "select * from data where a in (select a from other_table)", "REJECT"),
    ("union branch hitting read_csv",
     "select a from data union all select * from read_csv('/etc/passwd')", "REJECT"),
    ("recursive CTE self-reference only (legit)",
     "with recursive t(n) as (select 1 union all select n+1 from t where n < 5) select * from t", "ALLOW"),
    ("recursive CTE smuggling table function",
     "with recursive t(n) as (select 1 union all select n+1 from t, read_csv('/etc/passwd') where n < 5) select * from t", "REJECT"),
    ("legit nested CTEs only touching data", 
     "with a as (select * from data), b as (select * from a where a.a > 1) select * from b join a on 1=1", "ALLOW"),
    ("deeply nested parens (100) -- parser/walker robustness", "select " + "("*100 + "1" + ")"*100 + " as x", "ALLOW"),
    ("join data with info_schema",
     "select * from data d join information_schema.tables t on 1=1", "REJECT"),
    ("values-as-table (not data)",
     "select * from (values (1),(2)) as t(x)", "REJECT"),
    ("scalar subquery current_setting smuggle",
     "select (select current_setting('memory_limit')) as x from data", "REJECT"),
]

for name, sql, expect in cases:
    try:
        guard_v2.guard(sql)
        result = "ALLOW"
    except guard_v2.GuardError as e:
        result = "REJECT"
        msg = str(e)
    status = "OK" if result == expect else "MISMATCH!!"
    print(f"[{status}] {name}: expected={expect} got={result}" + (f" ({msg})" if result=='REJECT' else ""))
