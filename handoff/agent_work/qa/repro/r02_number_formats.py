"""BUG-02/03  text-number parsing: decimal-comma values silently 10x-100x wrong; '($1,234.50)' and '-$1,234.50' silently dropped (NaN).
run: /home/user/work/venv/bin/python -I r02_number_formats.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
import numpy as np
cases = [("$1,234.50", 1234.5), ("-$1,234.50", -1234.5), ("($1,234.50)", -1234.5), ("(1,234.50)", -1234.5), ("1,234.50-", -1234.5), ("−1,234.50", -1234.5), ("1,234.50 CR", 1234.5),
         ("USD 1,234.50", 1234.5), ("Rs. 1,234.50", 1234.5), ("1,234.50 USD", 1234.5), ("€ 1.234,50", 1234.5), ("1.234,50", 1234.5), ("1234,50", 1234.5), ("1 234,50", 1234.5), ("1,5", 1.5), ("0,5", 0.5), ("1'234.50", 1234.5)]
print(f"{'input':16s} {'parsed':>12s} {'expected':>10s}")
for raw, exp in cases:
    out = A.preprocess_df(pd.DataFrame({"v": ["100.50"] * 30 + [raw] * 5, "x": range(35)}))["v"]
    got = out.iloc[-1] if pd.api.types.is_numeric_dtype(out) else "<stays text>"
    ok = isinstance(got, (float, np.floating)) and not np.isnan(got) and abs(got - exp) < 1e-9
    print(f"{raw!r:16s} {str(got):>12s} {exp:>10} {'' if ok else '  <-- WRONG' + (' (silently dropped as NaN)' if isinstance(got, float) and np.isnan(got) else '')}")
print()
d = pd.read_csv(DATA / "expenses_currency.csv"); 
def num(s):
    neg = s.startswith("(") or s.startswith("-"); v = float(__import__("re").sub(r"[^0-9.]", "", s)); return -v if neg else v
truth = d.amount.map(num).sum(); got = load("expenses_currency.csv").amount.sum(); pos_only = d.amount.map(num).clip(lower=0).sum()
print(f"expenses_currency.csv  true total = {truth:,.2f} | Lumen total = {got:,.2f} | sum of positive rows only = {pos_only:,.2f}  (refund rows written ($x) or -$x are dropped)")
print("NaN cells created in 'amount':", int(load("expenses_currency.csv").amount.isna().sum()), "of", len(d), "-> no warning is shown to the user")
eu = pd.read_csv(DATA / "european.csv", sep=";", decimal=",", thousands="."); print(f"european.csv (6.287,82 style)  true total = {eu.Betrag.sum():,.2f} | Lumen = {load('european.csv').betrag.sum():,.2f}")
eu2 = pd.read_csv(DATA / "european_nothousands.csv", sep=";", decimal=","); print(f"european_nothousands.csv (6287,82 style) true total = {eu2.Betrag.sum():,.2f} | Lumen = {load('european_nothousands.csv').betrag.sum():,.2f}")
