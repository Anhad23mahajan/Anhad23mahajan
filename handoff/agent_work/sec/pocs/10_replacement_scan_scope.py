import sys, duckdb
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.main as M
import pandas as pd

# Simulate two tenants' sessions exactly as app.main does
M.SESSIONS["victim-sid"] = pd.DataFrame({"secret_customer_email": ["victim@example.com"], "ssn": ["111-22-3333"]})
attacker_df = pd.DataFrame({"product": ["A", "B"], "amount": [1, 2]})

import app.llm as llm

# Attack 1: default config (python_scan_all_frames=false, as shipped) -- try to reach
# app.main.SESSIONS (a module global in a DIFFERENT module, up the real call stack:
# main.ask() -> llm.answer() -> llm.run_sql() -> con.execute()).
for sql in ["select * from SESSIONS", "select * from M.SESSIONS", "select * from sessions"]:
    print("="*70, "\nDEFAULT CONFIG attempt:", sql)
    try:
        llm.guard(sql)
        res = llm.run_sql(attacker_df, sql, timeout=5)
        print("LEAKED:", res)
    except Exception as e:
        print("blocked/failed:", type(e).__name__, e)

# Attack 2: local-frame variable access within run_sql's OWN frame (df is the parameter name)
print("="*70, "\nLocal-frame test: SELECT * FROM df (same frame as con.execute)")
try:
    res = llm.run_sql(attacker_df, "select * from df", timeout=5)
    print("Resolved via replacement scan (same object, not a leak since it's the caller's own df):")
    print(res)
except Exception as e:
    print("failed:", type(e).__name__, e)

# Attack 3: what if python_scan_all_frames were (mis)configured true? Prove the mechanism
# itself is real so the recommendation is to NEVER enable this.
print("="*70, "\nWith python_scan_all_frames=TRUE (hypothetical misconfiguration) via manual con")
con = duckdb.connect(":memory:")
con.register("data", attacker_df)
con.execute("SET enable_external_access=false")
con.execute("SET python_scan_all_frames=true")
def inner_exec(sql):
    return con.execute(sql).df()
def simulate_ask():
    # SESSIONS is visible as a global two frames up from here if all-frames scanning is on
    return inner_exec("select * from SESSIONS")
try:
    # Need SESSIONS visible somewhere on the stack -- put it as a local here to mimic main.ask()
    SESSIONS_LOCAL = M.SESSIONS
    def simulate_ask2():
        SESSIONS = SESSIONS_LOCAL  # local var named SESSIONS, like main.py's module global would appear
        return inner_exec("select * from SESSIONS")
    leaked = simulate_ask2()
    print("LEAKED cross-tenant dict with all_frames=true:")
    print(leaked)
except Exception as e:
    print("failed:", type(e).__name__, e)
