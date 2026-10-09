import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd
df = pd.DataFrame({"product":["Copy","Set","Load"], "amount":[1,2,3]})

legit = [
    ("column named set", "select set from data"),  # unlikely col name but test keyword collision
    ("string literal Copy", "select * from data where product = 'Copy'"),
    ("string literal with semicolon-like note", "select * from data where product = 'Note: a;b'"),
    ("alias named load", "select amount as load from data"),
    ("column named call (quoted)", 'select "call" from data'),
    ("comment containing SQL keyword", "select amount from data -- export this please"),
    ("legit CTE named import_data", "with import_data as (select * from data) select * from import_data"),
    ("string literal containing word drop", "select * from data where product = 'Drop shipping'"),
    ("string literal containing word delete", "select * from data where product = 'Deleted item'"),
    ("column create_date style name", "select create_date from data"),
    ("order by with export-like alias", "select amount as exported_total from data order by exported_total"),
]
for name, sql in legit:
    print("="*70); print(name); print("SQL:", sql)
    try:
        llm.guard(sql)
        print("guard: PASS (correct - legit query allowed)")
    except ValueError as e:
        print("guard: REJECTED (false positive!):", e)
