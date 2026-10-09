"""Independent recomputation of every number the built-in demo shows (KPIs, insights, charts, forecast sanity) + 'known spike is not surfaced'.
run: /home/user/work/venv/bin/python -I r11_demo_numbers.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
d = A.demo_df(); p = A.profile(d); ins = A.insights(d, p); ch = A.starter_charts(d, p)
m = d.set_index("order_date").amount.resample("MS").sum()
checks = []
def chk(name, got, truth, tol=1e-6): checks.append((name, got, truth, abs(got - truth) <= max(1e-9, abs(truth) * tol)))
k = {x["label"]: x for x in p["kpis"]}
chk("rows", k["Rows analysed"]["value"], len(d)); chk("total amount", k["Total amount"]["value"], d.amount.sum())
chk("latest full month (Dec 2025)", k["Latest full month"]["value"], m.iloc[-1]); chk("delta vs Nov (%)", k["Latest full month"]["delta"], (m.iloc[-1] - m.iloc[-2]) / m.iloc[-2] * 100)
chk("best month value", k["Best month"]["value"], m.max()); print("best month:", k["Best month"]["note"], "| true:", m.idxmax().strftime("%b %Y"))
first, last = m.iloc[:8].mean(), m.iloc[-8:].mean(); chk("trend % (first8 vs last8)", float(ins[0]["title"].split("up ")[1].split("%")[0]), round((last - first) / first * 100))
share = d.groupby("product").amount.sum(); chk("Hoodie share %", float([i for i in ins if "Hoodie" in i["title"]][0]["title"].split("drives ")[1].split("%")[0]), round(share.max() / share.sum() * 100))
r = d.amount.corr(d.unit_price); chk("corr(amount, unit_price)", float([i for i in ins if "moves with" in i["title"]][0]["detail"].split("correlation ")[1].split(")")[0]), round(r, 2)); print("corr(amount, quantity) =", round(d.amount.corr(d.quantity), 2), " corr(amount, unit_price) =", round(r, 2))
line = [c for c in ch if c["type"] == "line"][0]; chk("chart points = 24 months", len(line["y"]), 24); chk("chart sum == total", sum(line["y"]), d.amount.sum())
for name, got, truth, ok in checks: print(f"{'ok ' if ok else 'BAD'} {name:34s} lumen={got:,.3f} truth={truth:,.3f}")
hdr("The demo's docstring promises 'one spike' (2025-03-14, 5x orders). Does any insight surface it?")
daily = d.groupby("order_date").size(); print("daily orders on spike day:", int(daily.loc["2025-03-14"]), "vs median", int(daily.median()), "| max other day:", int(daily.drop(pd.Timestamp("2025-03-14")).max()))
print("insight titles:", [i["title"] for i in ins]); print("mentions March 14 / any anomaly:", any(i["kind"] == "anomaly" for i in ins))
print("March 2025 monthly total", int(m.loc["2025-03-01"]), "vs Feb", int(m.loc["2025-02-01"]), "Apr", int(m.loc["2025-04-01"]), "(spike is diluted in a monthly bucket)")
hdr("Forecast on demo (24 months => exactly 2 seasonal cycles, 18 fitted params)")
f = A.clean(A.forecast(d, "order_date", "amount", 6)); print("forecast:", [round(v) for v in f["forecast"]["y"]]); print("band    :", [(round(l), round(u)) for l, u in zip(f["forecast"]["lower"], f["forecast"]["upper"])]); print(f["note"])
