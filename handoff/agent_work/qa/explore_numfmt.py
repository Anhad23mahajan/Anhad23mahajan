"""Which text-number formats does try_parse_numeric get right? Each case = 30 filler '100.50' rows + the probe values, expected value shown."""
import sys, warnings
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import pandas as pd, numpy as np
from app import analytics as A
warnings.simplefilter("ignore")
cases = [("$1,234.50", 1234.5), ("-$1,234.50", -1234.5), ("($1,234.50)", -1234.5), ("(1,234.50)", -1234.5), ("$-1,234.50", -1234.5), ("-1,234.50", -1234.5),
         ("1,234.50-", -1234.5), ("−1,234.50", -1234.5), ("1,234.50 CR", 1234.5), ("1,234.50 DR", -1234.5), ("USD 1,234.50", 1234.5), ("Rs. 1,234.50", 1234.5), ("Rs 1,234.50", 1234.5),
         ("₹ 1,234.50", 1234.5), ("₹1,23,450", 123450), ("€ 1.234,50", 1234.5), ("1.234,50", 1234.5), ("1234,50", 1234.5), ("1 234,50", 1234.5), ("1'234.50", 1234.5),
         ("12.5%", 12.5), ("-12.5%", -12.5), ("(12.5%)", -12.5), ("1e3", 1000), ("1,5", 1.5), ("1,234", 1234), ("0,5", 0.5), ("12 345", 12345), ("N/A", np.nan), ("#DIV/0!", np.nan), ("-", 0), ("—", np.nan), ("TBD", np.nan), ("$ 1,234.50", 1234.5), ("1234.50$", 1234.5), ("1,234.50 USD", 1234.5)]
print("pandas", pd.__version__)
print(f"{'input':16s} {'parsed':>14s} {'expected':>12s}")
bad = 0
for raw, exp in cases:
    df = pd.DataFrame({"v": ["100.50"] * 30 + [raw] * 5, "x": range(35)})
    out = A.preprocess_df(df)["v"]
    got = out.iloc[-1] if pd.api.types.is_numeric_dtype(out) else f"<text col: {out.iloc[-1]!r}>"
    ok = (isinstance(got, (int, float, np.floating)) and ((np.isnan(got) and np.isnan(exp)) or (not np.isnan(got) and not np.isnan(exp) and abs(got - exp) < 1e-9)))
    if not ok: bad += 1
    print(f"{raw!r:16s} {str(got):>14s} {exp!s:>12s} {'' if ok else '  <-- WRONG'}")
print("wrong:", bad, "of", len(cases))
