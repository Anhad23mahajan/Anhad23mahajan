"""BUG-32/33/34  SQL guard false positives (columns named set/load/update/export/call, ';' or 'set' inside literals, '--' in literals) and /api/ask error classification.
run: /home/user/work/venv/bin/python -I r12_sql_guard_and_ask.py   (no Gemini key needed: llm.guard / llm.run_sql are called directly)"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
import re
df = load("donations.csv")
tests = [("column named set", 'SELECT sum("set") FROM data'), ("column named load", 'SELECT sum("load") FROM data'), ("column named update", 'SELECT "update" FROM data'), ("column named export", 'SELECT "export" FROM data'), ("column named call", 'SELECT "call" FROM data'),
         ("literal 'Set up'", "SELECT * FROM data WHERE campaign = 'Set up'"), ("literal containing ;", "SELECT * FROM data WHERE donor LIKE '%;%'"), ("literal containing --", "SELECT 'a--b' AS s"), ("literal 'Import duty'", "SELECT * FROM data WHERE campaign = 'Import duty'"),
         ("column named order (quoted)", 'SELECT sum("order") FROM data'), ("window fn / QUALIFY-free CTE", "WITH t AS (SELECT campaign, sum(amount) a FROM data GROUP BY 1) SELECT * FROM t ORDER BY a DESC")]
for label, sql in tests:
    try: g = llm.guard(sql); out = "allowed" + ("" if g == sql else f" BUT SQL IS REWRITTEN to {g!r}")
    except ValueError as e: out = "BLOCKED: " + str(e)
    print(f"{label:32s} {sql[:62]!r:66s} {out}")
hdr("ask() error classification: regex on the exception text")
import app.main as M, inspect
src = inspect.getsource(M.ask)
pats = re.findall(r'if re.search\(r"([^"]+)"', src) + re.findall(r'elif re.search\(r"([^"]+)"', src)
samples = ["500 INTERNAL. {'error': {'code': 500, 'message': 'An internal error has occurred. Request id: 7f2403a9c'}}", "504 DEADLINE_EXCEEDED. Request took 40.31 s", "Model returned invalid JSON near position 4031"]
for s in samples:
    hit = [p for p in pats if re.search(p, s, re.I)]; print(f"   {s[:80]!r:84s} -> first matching rule: {hit[0] if hit else 'none (generic 502)'}")
print("   -> any text that merely contains the digits 401/403/429/503/404 is reported to the user as 'API key rejected' / 'quota used up' / 'busy' / 'model not found'")
