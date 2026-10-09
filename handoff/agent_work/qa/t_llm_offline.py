"""Exercise the non-LLM half of /api/ask (guard, DuckDB sandbox, answer() post-processing, JSON encoding) with a mocked Gemini.
Run in each venv:  <venv>/bin/python -I t_llm_offline.py"""
import sys, os, json, time, warnings
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
os.environ["GEMINI_API_KEY"] = "fake-key-for-offline-test"
import pandas as pd
from fastapi.testclient import TestClient
from app import main, llm, analytics as A
D = "/home/user/work/qa/fixtures/data/"
print("pandas", pd.__version__)
cl = TestClient(main.app, raise_server_exceptions=False)

def load(name): return A.load_df(open(D + name, "rb").read(), name)
def session(name):
    df = load(name); sid = "t_" + name; main.SESSIONS[sid] = df; return sid, df

plans = []
def fake_json(prompt):
    return plans.pop(0)
llm._json = fake_json

_orig_run = llm.run_sql
def _wrapped(df, sql, timeout=10):
    try: return _orig_run(df, sql, timeout)
    except Exception as e:
        print("     [run_sql raised]", type(e).__name__, str(e).replace("\n", " ")[:140]); raise
llm.run_sql = _wrapped

def ask(fixture, sql, chart=None, verified=True, answer="ok"):
    sid, df = session(fixture)
    plans[:] = [{"sql": sql, "chart": chart or {"type": "table"}}, {"answers_question": verified, "answer": answer, "caveats": ""}]
    r = cl.post("/api/ask", json={"session_id": sid, "question": "q"})
    try: body = r.json()
    except Exception: body = r.text[:150]
    short = json.dumps(body)[:260] if isinstance(body, (dict, list)) else body
    print(f"[{fixture}] {sql[:90]!r}\n     -> {r.status_code} {short}")
    return r

print("\n=== schema_text under this pandas")
df = load("pct_bool_thousands.csv"); print(llm.schema_text(df))
print("\n=== answer() post-processing with real DuckDB over the processed frames")
ask("donations.csv", "SELECT date_trunc('month', date) AS month, sum(amount) AS total FROM data GROUP BY 1 ORDER BY 1 LIMIT 3", {"type": "line", "x": "month", "y": "total"})
ask("donations.csv", "SELECT campaign, sum(amount) AS total FROM data GROUP BY 1 ORDER BY 2 DESC", {"type": "bar", "x": "campaign", "y": "total"})
ask("pct_bool_thousands.csv", "SELECT paid, repeat_customer, count(*) AS n FROM data GROUP BY 1,2 ORDER BY 1,2")
ask("donations.csv", "SELECT max(date) - min(date) AS span FROM data")                       # INTERVAL
ask("donations.csv", "SELECT CAST(sum(amount) AS DECIMAL(18,2)) AS t FROM data")              # DECIMAL
ask("donations.csv", "SELECT amount / 0 AS inf_val, NULL AS n, sum(amount) FILTER (WHERE amount < 0) AS empty_sum FROM data LIMIT 2")  # inf / NULL / NaN
ask("donations.csv", "SELECT count(*) AS n FROM data", {"type": "number", "x": "n", "y": "n"})
ask("donations.csv", "SELECT list(DISTINCT channel) AS chans FROM data")                         # LIST type
ask("donations.csv", "SELECT {'a': 1} AS s")                                                    # STRUCT
ask("donations.csv", "SELECT CAST(date AS DATE) AS d FROM data LIMIT 2")                        # DATE
ask("donations.csv", "SELECT strftime(date, '%Y-%m') AS ym, sum(amount) FROM data GROUP BY 1 ORDER BY 1 LIMIT 2")
ask("donations.csv", "SELECT 'a--b' AS s FROM data LIMIT 1")                                    # '--' inside a literal
ask("donations.csv", "SELECT * FROM data WHERE donor LIKE '%;%' LIMIT 1")                      # ';' inside a literal
ask("donations.csv", "SELECT * FROM data WHERE campaign = 'Set up' LIMIT 1")                  # word 'set' inside a literal
ask("edge_reserved_cols.csv", 'SELECT "group", sum("set") AS s FROM data GROUP BY 1')           # column named set
ask("edge_reserved_cols.csv", 'SELECT "group", sum("order") AS s FROM data GROUP BY 1')         # column named order (allowed?)
ask("edge_reserved_cols.csv", 'SELECT "update", count(*) FROM data GROUP BY 1')                # column named update
ask("edge_reserved_cols.csv", 'SELECT sum("load"), sum("export"), sum("call") FROM data')
ask("hindi_headers.csv", 'SELECT "शहर", sum("र_श") AS total FROM data GROUP BY 1')               # sanitised hindi names
print("\n=== sandbox / guard probes (run_sql directly)")
df = load("donations.csv")
probes = ["SELECT * FROM '/etc/hostname'", 'SELECT * FROM "/etc/passwd"', "SELECT * FROM read_text('/etc/passwd')", "SELECT * FROM glob('/*')",
          "SELECT current_setting('enable_external_access')", "SELECT * FROM pragma_database_size()", "SELECT * FROM pragma_table_info('data')", "SELECT version()",
          "SELECT * FROM information_schema.tables", "SELECT * FROM duckdb_settings()", "SELECT getenv('HOME')", "SELECT * FROM range(3)",
          "SELECT 1; SELECT 2", "SELECT 1 /* x */ ; DROP TABLE data", "WITH x AS (SELECT 1) SELECT * FROM x", "(SELECT 1)", "  \n select 1", "SELECT * FROM data a, data b, data c, data d LIMIT 1",
          "SELECT repeat('x', 100000000) AS big", "SELECT count(*) FROM range(100000000000)", "SELECT 1 FROM data WHERE 1=1 -- hi", "SELECT 'x' INTO t", "SELECT * FROM data UNION ALL SELECT * FROM read_csv('x')",
          "EXPLAIN SELECT 1", "DESCRIBE data", "SHOW TABLES", "SUMMARIZE data", "PIVOT data ON channel USING sum(amount)", "FROM data SELECT count(*)", "SELECT * FROM data TABLESAMPLE 1%"]
for p in probes:
    t = time.time()
    try: r = llm.run_sql(df, p, timeout=3); out = f"OK rows={len(r)} cols={list(r.columns)[:3]}"
    except Exception as e: out = f"{type(e).__name__}: {str(e)[:110]}"
    print(f"  {time.time()-t:5.1f}s {p[:70]!r:75s} {out}")
