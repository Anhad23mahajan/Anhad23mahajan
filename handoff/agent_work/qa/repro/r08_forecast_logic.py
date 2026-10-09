"""BUG-25..29  forecast(): negative forecasts with inverted band, mismatched comparison window, forecasts from zero-padded sparse data, NaN/null output, under-covering interval.
run: /home/user/work/venv/bin/python -I r08_forecast_logic.py   (calibration: see ../t_forecast_backtest.py)"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
import json
def fc(df, periods=6, v="amount"):
    f = A.clean(A.forecast(df, "date", v, periods)); return f
hdr("A) non-negative history (6 months of sales ending low) -> negative forecast, 'lower' clipped ABOVE the forecast line")
f = fc(load("ambig_dmy_halfyear.csv"), v="sales") if False else fc(csv_df("date,sales\n" + "\n".join(f"{d:%Y-%m-%d},{max(0, 3000 - 250 * i)}" for i, d in enumerate(pd.date_range("2024-01-15", periods=11, freq="MS"))) + "\n"), 6, "sales")
print("history tail:", f["history"]["y"][-4:]); print("forecast y    :", f["forecast"]["y"]); print("forecast lower:", f["forecast"]["lower"]); print("forecast upper:", f["forecast"]["upper"])
print("any forecast < 0:", any(y < 0 for y in f["forecast"]["y"]), "| lower > y at some point:", any(l > y for l, y in zip(f["forecast"]["lower"], f["forecast"]["y"])))
print("note:", f["note"])
hdr("B) comparison window mismatch: 10 months of history, periods=24 -> 'last 24' is only 10 months")
dates = pd.date_range("2024-01-15", periods=10, freq="MS"); df = csv_df("date,amount\n" + "\n".join(f"{d:%Y-%m-%d},1000" for d in dates) + "\n2024-10-31,0\n")
f = fc(df, 24); print("history points:", len(f["history"]["x"]), "| forecast points:", len(f["forecast"]["x"]), "| flat 1000/month history, forecast ~", f["forecast"]["y"][0]); print("note:", f["note"], " <- true growth is ~0%")
hdr("C) 2 data rows 28 days apart: zero-filled to 29 daily points, then forecast 'works'")
f = fc(load("edge_two_rows.csv")); print("history non-zero points:", sum(1 for v in f["history"]["y"] if v), "of", len(f["history"]["y"])); print("forecast y:", f["forecast"]["y"]); print("note:", f["note"])
hdr("D) inf / 1e300 in data: forecast arrays contain nulls (NaN) and warnings; HTTP 200")
for name in ("edge_inf_values.csv", "edge_huge_values.csv"):
    try: f = fc(load(name)); print(name, "forecast y:", f["forecast"]["y"][:3], "lower:", f["forecast"]["lower"][:2])
    except Exception as e: print(name, "->", type(e).__name__, e)
hdr("E) interval calibration on the demo: re-forecast the last 6 months of the demo data from the first 18")
d = A.demo_df(); p = A.profile(d); s, freq = A.period_series(d, "order_date", "amount"); print("demo has", len(s), "monthly points; holding out last 6 and fitting on", len(s) - 6)
cut = s.index[-7] + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1)
train = d[d.order_date < cut]; f = A.forecast(train, "order_date", "amount", 6); truth = s.iloc[-6:].values
print("truth   :", truth.round(0).tolist()); print("forecast:", np.round(f["forecast"]["y"]).tolist()); print("lower   :", np.round(f["forecast"]["lower"]).tolist()); print("upper   :", np.round(f["forecast"]["upper"]).tolist())
print("truth inside band:", [(l <= t <= u) for l, t, u in zip(f["forecast"]["lower"], truth, f["forecast"]["upper"])])
