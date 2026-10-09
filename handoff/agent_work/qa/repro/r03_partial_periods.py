"""BUG-04/05/06  partial first/last periods: false 'Latest full week' drop + false anomaly; partial first month inflates trend; complete month dropped.
run: /home/user/work/venv/bin/python -I r03_partial_periods.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
def show(name, true_note):
    df = load(name); p, ins, ch = analyse(df); print(f"--- {name}   ({true_note})")
    for k in p["kpis"][1:]: print("   KPI", {a: (round(b, 1) if isinstance(b, float) else b) for a, b in k.items()})
    line = [c for c in ch if c["type"] == "line"][0]; print("   chart", line["title"], "last points:", line["y"][-3:], "| first points:", line["y"][:2])
    for i in ins: print("   INSIGHT", i["severity"], "|", i["title"], "|", i["detail"][:110])
hdr("A) 73 days, ~1000/day, flat, Mon 3 Mar .. Wed 14 May: weekly bins; last bin is only Mon-Wed")
show("daily_70d_midweek.csv", "truth: flat ~7000/week; no trend, no anomaly, last week incomplete")
hdr("B) 12 months flat ~500/day starting 28 Mar 2024 (first month has 4 days)")
show("starts_mid_month.csv", "truth: flat; the 4-day March bucket makes 'up 27%' and 'Unusual month'")
hdr("C) daily data 1 Nov 2024 .. 30 Dec 2025 (Dec 31 simply had no sale)")
show("ends_dec30.csv", "truth: December 2025 has 30/31 days and is the latest month; Lumen drops it")
hdr("D) donations.csv: 2 years of donations, last donation on 30 Dec 2024; December is the biggest month")
d = load("donations.csv"); print("   last donation date:", d.date.max().date()); show("donations.csv", "truth: Dec 2024 should be in the chart; it is dropped as 'incomplete'")
hdr("E) tz-aware / 120 days of 12-hourly rows ending Wed 30 Apr 12:00 -> weekly bins")
show("tz_utc.csv", "truth: last week is 3.5 days; shown as 'Latest full week -70%' and anomaly")
