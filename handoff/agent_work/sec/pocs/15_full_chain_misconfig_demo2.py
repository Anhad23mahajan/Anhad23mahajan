import sys, duckdb
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.main as M
import app.llm as llm
import pandas as pd

M.SESSIONS["victim-sid"] = pd.DataFrame({"secret_customer_email": ["victim@example.com"], "card_last4": ["4242"]})
M.SESSIONS["attacker-sid"] = pd.DataFrame({"product": ["A"], "amount": [1]})

# Define a function with app.main's OWN module globals (so SESSIONS is a true frame-global
# exactly as in the real ask() endpoint), to faithfully reproduce the real call stack:
# main.ask()'s frame -> llm.run_sql()'s frame -> con.execute().
exec("""
def real_style_ask(session_id, question_sql, timeout=10):
    df = get_df(session_id)   # uses app.main.get_df, app.main.SESSIONS -- real code path
    return llm.run_sql(df, question_sql, timeout=timeout)
""", M.__dict__)

real_connect = duckdb.connect
def misconfigured_run_sql(df, sql, timeout=10):
    s = llm.guard(sql)
    con = real_connect(":memory:")
    con.register("data", df)
    con.execute("SET python_scan_all_frames=true")   # misconfiguration under test
    # enable_external_access left at its library default (true) in this misconfigured variant
    try:
        return con.execute(f"SELECT * FROM ({s}) LIMIT 1000").df()
    finally:
        con.close()
llm.run_sql = misconfigured_run_sql

try:
    leaked = M.real_style_ask("attacker-sid", "select * from SESSIONS")
    print("LEAKED (scan_all_frames=true, external_access=true):")
    print(leaked)
except Exception as e:
    print("blocked:", type(e).__name__, e)

print()
print("=== Now the SAME attack against the REAL, unmodified llm.run_sql (shipped defaults) ===")
import importlib
importlib.reload(llm)  # restore the real run_sql / guard
try:
    leaked2 = llm.run_sql(M.SESSIONS["attacker-sid"], "select * from SESSIONS", timeout=5)
    print("LEAKED:", leaked2)
except Exception as e:
    print("blocked (expected with shipped defaults):", type(e).__name__, e)
