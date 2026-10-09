"""BUG-19..24  insights() logic.
run: /home/user/work/venv/bin/python -I r07_insights_logic.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
rng = np.random.default_rng(0)
hdr("A) best-correlation selection: 'abs(best[1])' is always truthy so the LAST column with |r|>0.5 wins, not the strongest")
n = 400; x = rng.normal(0, 1, n); amount = 100 + 20 * x + rng.normal(0, 3, n)
df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n), "amount": amount, "strong_driver": x * 10 + rng.normal(0, 1, n), "weak_driver": 0.8 * x + rng.normal(0, 1, n)})
print("corr(amount, strong_driver) = %.2f ; corr(amount, weak_driver) = %.2f" % (df.amount.corr(df.strong_driver), df.amount.corr(df.weak_driver)))
p, ins, ch = analyse(A.preprocess_df(df)); print("Lumen says:", [i["title"] + " | " + i["detail"][:90] for i in ins if "moves with" in i["title"]])
hdr("B) 'driver' insight: fixed 35% threshold flags pure noise with 3 categories; and shares can exceed 100% with negative values")
n = 600; df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n), "channel": rng.choice(["A", "B", "C"], n), "amount": rng.uniform(10, 100, n)})
p, ins, ch = analyse(A.preprocess_df(df)); print("uniform random categories:", [i["title"] for i in ins if i["kind"] == "driver"], "| true shares:", (df.groupby("channel").amount.sum() / df.amount.sum()).round(3).to_dict())
df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=300), "fund": np.tile(["Gala", "Appeal", "Refunds"], 100), "amount": np.tile([100, 60, -150], 100) + rng.normal(0, 1, 300)})
p, ins, ch = analyse(A.preprocess_df(df)); print("with a refunds category:", [(i["title"], i["detail"][:70]) for i in ins if i["kind"] == "driver"])
hdr("C) direction is judged 'good' for any increase, even for cost metrics ('Find out what changed and repeat it.')")
n = 365; df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n), "expenses": np.linspace(100, 160, n) + rng.normal(0, 5, n)})
p, ins, ch = analyse(A.preprocess_df(df)); print([(i["severity"], i["title"], i["action"]) for i in ins])
hdr("D) wording and number formatting")
df = pd.DataFrame({"date": ["2025-01-31", "2025-02-28"], "amount": [1200, 900]}); p, ins, ch = analyse(A.preprocess_df(df)); print("2-row file:", [i["detail"] for i in ins])
n = 200; v = np.abs(rng.normal(0.05, 0.005, n)); v[100:103] = 0.5
df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=n), "conversion_rate": v}); p, ins, ch = analyse(A.preprocess_df(df)); print("rate ~0.05 with a spike to 0.5:", [i["detail"] for i in ins if i["kind"] == "anomaly"], "| KPI values:", [round(k["value"], 4) for k in p["kpis"][1:3]])
hdr("E) data-quality warnings crowd out the real findings / dominate the 'What matters most' summary")
n = 300; cols = {"date": pd.date_range("2024-01-01", periods=n), "amount": rng.integers(100, 900, n) * np.linspace(1, 2, n)}
for i in range(9): cols[f"opt_field_{i}"] = np.where(rng.random(n) < .7, None, "x")
p, ins, ch = analyse(A.preprocess_df(pd.DataFrame(cols))); print("insights returned (cap 8):", [i["title"] for i in ins]); print("narrative summary:", llm.narrate(ins, {})["summary"][:160])
print("-> the real finding ('amount is up ..%') is cut off:", not any("is up" in i["title"] for i in ins))
