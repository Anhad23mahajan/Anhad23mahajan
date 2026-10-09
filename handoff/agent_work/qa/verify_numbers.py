"""Independent ground-truth check of the headline numbers the API reports (reads results_pd3.json + fixtures)."""
import json, re, pandas as pd, numpy as np
R = json.load(open("/home/user/work/qa/results_pd3.json")); R.update(json.load(open("/home/user/work/qa/results_pd3_big.json"))); D = "/home/user/work/qa/fixtures/data/"
def kpi(f, label_start="Total"):
    for k in R[f]["summary"]["kpis"]:
        if k["label"].startswith(label_start): return k["value"]
rows = []
def chk(name, f, truth, got):
    ok = got is not None and abs(got - truth) <= max(0.01, abs(truth) * 1e-6)
    rows.append((name, f, round(truth, 2), None if got is None else round(got, 2), "ok" if ok else "WRONG"))
# donations: plain
d = pd.read_csv(D + "donations.csv"); chk("donations total", "donations.csv", d.amount.sum(), kpi("donations.csv"))
# expenses: parentheses = negative, -$ = negative
e = pd.read_csv(D + "expenses_currency.csv")
def num(s):
    s = s.strip(); neg = s.startswith("(") or s.startswith("-"); v = float(re.sub(r"[^0-9.]", "", s)); return -v if neg else v
chk("expenses total (parentheses/-$ negative)", "expenses_currency.csv", e.amount.map(num).sum(), kpi("expenses_currency.csv"))
# european with thousands
eu = pd.read_csv(D + "european.csv", sep=";", decimal=",", thousands="."); chk("european (1.234,56)", "european.csv", eu.Betrag.sum(), kpi("european.csv"))
eu2 = pd.read_csv(D + "european_nothousands.csv", sep=";", decimal=","); chk("european (1234,56)", "european_nothousands.csv", eu2.Betrag.sum(), kpi("european_nothousands.csv"))
# thousands separators / INR lakh
t = pd.read_csv(D + "thousands_text.csv", thousands=","); chk("thousands text", "thousands_text.csv", t.revenue.sum(), kpi("thousands_text.csv"))
il = pd.read_csv(D + "inr_lakh.csv"); chk("INR lakh", "inr_lakh.csv", il.revenue.str.replace(r"[₹,]", "", regex=True).astype(float).sum(), kpi("inr_lakh.csv"))
# excel TOTAL row
x = pd.read_excel(D + "total_row_literal.xlsx"); body = x[x.Date != "TOTAL"]; chk("xlsx with TOTAL row", "total_row_literal.xlsx", body.Amount.sum(), kpi("total_row_literal.xlsx"))
# multi-sheet: all data
ms = pd.concat(pd.read_excel(D + "multi_sheet_data_first.xlsx", sheet_name=None).values()); chk("xlsx two sheets (2024+2025)", "multi_sheet_data_first.xlsx", ms.sales.sum(), kpi("multi_sheet_data_first.xlsx"))
# truncation at 200k
b = pd.read_csv(D + "big_250k_truncation.csv"); chk("250k-row file total", "big_250k_truncation.csv", b.amount.sum(), kpi("big_250k_truncation.csv"))
# dd/mm/yyyy: months present
dm = pd.read_csv(D + "ambig_dmy_halfyear.csv"); true_months = pd.to_datetime(dm.date, format="%d/%m/%Y").dt.to_period("M").nunique()
got_months = [c for c in R["ambig_dmy_halfyear.csv"]["summary"]["charts"] if c["type"] == "line"][0]["n"]
rows.append(("dd/mm/yyyy file: #monthly points (true span Jan-Jun = 6, last partial dropped?)", "ambig_dmy_halfyear.csv", true_months, got_months, "WRONG" if got_months != true_months else "ok"))
w = max(len(r[0]) for r in rows)
for r in rows: print(f"{r[0]:{w}s} | {r[1]:32s} | truth={r[2]:>16,} | api={r[3]!s:>16} | {r[4]}")
