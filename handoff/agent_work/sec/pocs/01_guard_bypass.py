import sys, json
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

df = pd.DataFrame({"product":["A","B"], "amount":[1,2]})

tests = [
    # name, sql
    ("file-as-table /etc/passwd", "select * from '/etc/passwd'"),
    ("file-as-table csv glob", "select * from '/etc/*.conf'"),
    ("read_csv direct", "select * from read_csv('/etc/passwd')"),
    ("read_csv_auto", "select * from read_csv_auto('/etc/passwd')"),
    ("read_text", "select * from read_text('/etc/passwd')"),
    ("read_blob", "select * from read_blob('/etc/passwd')"),
    ("getenv", "select getenv('PATH')"),
    ("current_setting", "select current_setting('enable_external_access')"),
    ("duckdb_settings", "select * from duckdb_settings()"),
    ("duckdb_extensions", "select * from duckdb_extensions()"),
    ("information_schema", "select * from information_schema.tables"),
    ("pragma_version", "select * from pragma_version()"),
    ("sniff_csv", "select * from sniff_csv('/etc/passwd')"),
    ("read_ndjson", "select * from read_ndjson('/etc/passwd')"),
    ("read_json_auto", "select * from read_json_auto('/etc/passwd')"),
    ("parquet_scan", "select * from parquet_scan('/etc/passwd')"),
    ("iceberg_scan", "select * from iceberg_scan('/etc/passwd')"),
    ("delta_scan", "select * from delta_scan('/etc/passwd')"),
    ("query_table", "select * from query_table('data')"),
    ("query()", "select * from query('select 1')"),
    ("glob()", "select * from glob('/etc/*')"),
    # bypass tricks
    ("comment split read_csv", "select * from read/**/_csv('/etc/passwd')"),
    ("case bypass READ_CSV", "select * from READ_CSV('/etc/passwd')"),
    ("quoted identifier read_csv", 'select * from "read_csv"(\'/etc/passwd\')'),
    ("newline in keyword", "select * from read_csv\n('/etc/passwd')"),
    ("string concat PRAGMA-like", "select 1 as x -- pragma\n"),
    ("unicode homoglyph read_csv (cyrillic е)", "select * from rеad_csv('/etc/passwd')"),
    ("set via SET-like select", "select current_setting('memory_limit')"),
    ("attach db", "attach ':memory:' as x"),
    ("multi-stmt stacked", "select 1; select * from read_csv('/etc/passwd')"),
    ("pragma via select", "select * from pragma_database_list()"),
    ("pg_ function", "select * from pg_timezone_names()"),
]

results = []
for name, sql in tests:
    entry = {"name": name, "sql": sql}
    try:
        g = llm.guard(sql)
        entry["guard"] = "PASSED (not blocked)"
        try:
            res = llm.run_sql(df, sql, timeout=5)
            entry["run_sql"] = f"EXECUTED, shape={res.shape}, sample={res.head(2).to_dict('records')}"
        except Exception as e:
            entry["run_sql"] = f"EXECUTION ERROR: {type(e).__name__}: {e}"
    except ValueError as e:
        entry["guard"] = f"BLOCKED: {e}"
    results.append(entry)

for r in results:
    print("="*80)
    print(r["name"])
    print("SQL:", r["sql"])
    print("guard:", r["guard"])
    if "run_sql" in r:
        print("run_sql:", r["run_sql"])
