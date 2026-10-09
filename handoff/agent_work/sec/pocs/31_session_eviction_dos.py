import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.main as M
import pandas as pd

M.SESSIONS.clear()
victim_sid = "victim-session"
M.SESSIONS[victim_sid] = pd.DataFrame({"x":[1]})
print("victim session present before flood:", victim_sid in M.SESSIONS)

# Attacker creates 50 new sessions (e.g. by hitting /api/demo or /api/upload repeatedly)
for i in range(50):
    sid = f"attacker-{i}"
    if len(M.SESSIONS) > 50: M.SESSIONS.pop(next(iter(M.SESSIONS)))
    M.SESSIONS[sid] = pd.DataFrame({"x":[1]})

print("victim session present after 50 attacker sessions:", victim_sid in M.SESSIONS)
print("total sessions now:", len(M.SESSIONS))
