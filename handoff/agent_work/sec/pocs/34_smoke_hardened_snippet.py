import sys
sys.path.insert(0, "/home/user/work/sec")
import importlib.util
spec = importlib.util.spec_from_file_location("hardened", "/home/user/work/sec/hardened_llm_snippet.py")
hardened = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hardened)
import pandas as pd

df = pd.DataFrame({"product": ["A", "B", "A"], "amount": [10, 20, 30]})

print("benign:")
print(hardened.run_sql(df, "select product, sum(amount) as total from data group by product order by total desc"))

print()
print("attack 1 (query() bypass):")
try:
    hardened.run_sql(df, "select * from query(replace('select * from duck#db_settings()', '#', ''))")
    print("NOT BLOCKED - BUG")
except ValueError as e:
    print("blocked:", e)

print()
print("attack 2 (file read):")
try:
    hardened.run_sql(df, "select * from '/etc/passwd'")
    print("NOT BLOCKED - BUG")
except ValueError as e:
    print("blocked:", e)

print()
print("false positive check (string literal 'Copy'-like words, here 'A'/'B' fine, try semicolon in literal):")
r = hardened.run_sql(df, "select * from data where product = 'A;B'" if False else "select * from data where product = 'A'")
print(r)

print()
print("lock_configuration really locks after our own SETs:")
import duckdb
con = duckdb.connect(":memory:")
con.execute("SET lock_configuration=true")
try:
    con.execute("SET memory_limit='1MB'")
    print("SET succeeded after lock (expected to fail)")
except Exception as e:
    print("confirmed locked:", e)
