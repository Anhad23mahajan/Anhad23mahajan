import sys
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.main as M
import pandas as pd

M.SESSIONS.clear()
victim_sid = "victim-session"
M.SESSIONS[victim_sid] = pd.DataFrame({"x":[1]})

def start_session_sim(sid):
    if len(M.SESSIONS) > 50: M.SESSIONS.pop(next(iter(M.SESSIONS)))
    M.SESSIONS[sid] = pd.DataFrame({"x":[1]})

for i in range(60):
    start_session_sim(f"attacker-{i}")
    if victim_sid not in M.SESSIONS:
        print(f"victim evicted after attacker session #{i+1} (total sessions created by attacker: {i+1})")
        break
else:
    print("victim survived 60 attacker sessions; total now:", len(M.SESSIONS))
print("final session count:", len(M.SESSIONS))
