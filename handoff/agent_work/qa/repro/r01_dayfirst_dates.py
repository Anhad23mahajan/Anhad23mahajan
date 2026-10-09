"""BUG-01  dd/mm/yyyy dates are parsed with MIXED conventions (month-first unless the day is >12).
run: /home/user/work/venv/bin/python -I r01_dayfirst_dates.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
hdr("A) dd/mm/yyyy file covering 1 Jan - 30 Jun 2025 (180 rows, 1 per day, sales=100)")
days = pd.date_range("2025-01-01", "2025-06-30")
txt = "date,sales\n" + "\n".join(f"{d:%d/%m/%Y},100" for d in days)
df = csv_df(txt); print("parsed min/max:", df.date.min().date(), df.date.max().date(), "| expected 2025-01-01 .. 2025-06-30")
print("distinct months in parsed data:", df.date.dt.to_period("M").nunique(), "(expected 6)")
print("sample of raw -> parsed:"); 
for raw, got in list(zip(txt.splitlines()[1:], df.date))[:16:3] + list(zip(txt.splitlines()[1:], df.date))[12:15]: print("   ", raw.split(",")[0], "->", got.date())
p, ins, ch = analyse(df); line = [c for c in ch if c["type"] == "line"][0]
print("chart:", line["title"], "x-points:", len(line["x"]), line["x"][0], "..", line["x"][-1], "(a 6-month span (<=180 days) is bucketed WEEKLY: expect ~25 weekly points spanning Jan-Jun; the broken parse spans 11 months and is bucketed MONTHLY)")
print("insights:", [i["title"] for i in ins])
hdr("B) fully-ambiguous file: 12 rows 01/04/2025 .. 12/04/2025 (a user in India/Europe means 1-12 April)")
txt = "date,sales\n" + "\n".join(f"{d:%d/%m/%Y},100" for d in pd.date_range("2025-04-01", periods=12))
df = csv_df(txt); print("parsed:", [str(x.date()) for x in df.date][:12])
p, ins, ch = analyse(df); print("freq chosen:", [c.get("freq") for c in ch], "(expected D: 12 consecutive days) KPIs:", [(k["label"]) for k in p["kpis"]])
