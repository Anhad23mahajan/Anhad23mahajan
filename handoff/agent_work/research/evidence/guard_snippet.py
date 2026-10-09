# app/guard.py  (NEW file; ~25 lines). In-memory is fine because the app runs ONE worker.
import os, time, threading
from collections import defaultdict, deque
from fastapi import Request

PER_IP = int(os.getenv("AI_PER_IP", "5"))        # AI questions allowed per IP ...
WINDOW = int(os.getenv("AI_WINDOW_S", "600"))    # ... per this many seconds
DAILY  = int(os.getenv("AI_DAILY_CAP", "40"))    # hard global cap per UTC day (protects the Gemini quota)
_hits, _day, _lock = defaultdict(deque), {"d": None, "n": 0}, threading.Lock()

def client_ip(request: Request) -> str:
    return (request.headers.get("x-forwarded-for") or request.client.host or "?").split(",")[0].strip()

def ai_allowed(request: Request) -> bool:
    now = time.time(); today = time.strftime("%Y-%m-%d", time.gmtime(now)); ip = client_ip(request)
    with _lock:
        if _day["d"] != today: _day.update(d=today, n=0)
        if _day["n"] >= DAILY: return False
        q = _hits[ip]
        while q and now - q[0] > WINDOW: q.popleft()
        if len(q) >= PER_IP: return False
        q.append(now); _day["n"] += 1
        return True
