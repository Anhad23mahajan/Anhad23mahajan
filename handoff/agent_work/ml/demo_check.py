"""demo_check.py - how do the old and new forecasters do on the app's own demo data, at the app's real operating point?

demo_df() draws days sequentially from one RNG, so extending the same generator beyond 2025-12-31 reproduces the first 731 days
exactly and then yields 'future truth' from the same process.  We forecast Jan-Jun 2026 monthly (and the next 14 days / 6 weeks)
from the 24 months the app would see, and score against that truth.   python demo_check.py
"""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.simplefilter("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import bench_forecast as B
import forecasting as FC
from app import analytics as A


def demo_ext(seed=7, end="2026-06-30"):
    """Verbatim copy of analytics.demo_df with a later end date (same RNG stream => identical first 731 days)."""
    rng = np.random.default_rng(seed)
    prods = {"Hoodie": 900, "Tote bag": 250, "Notebook": 120, "Mug": 300, "Sticker pack": 60}
    weights = np.array([.38, .17, .2, .15, .1]); regions = ["North", "South", "Campus", "Online"]
    rows = []
    for day in pd.date_range("2024-01-01", end):
        winter = 1 + .5 * np.cos((day.dayofyear - 20) / 365 * 2 * np.pi)
        n = rng.poisson(8 * winter * (1 + (day - pd.Timestamp("2024-01-01")).days / 900) * (1.3 if day.dayofweek >= 5 else 1))
        if day == pd.Timestamp("2025-03-14"): n *= 5
        for _ in range(n):
            p = rng.choice(list(prods), p=weights); q = int(rng.integers(1, 4))
            rows.append((day, p, rng.choice(regions, p=[.2, .15, .35, .3]), q, prods[p], q * prods[p]))
    return pd.DataFrame(rows, columns=["order_date", "product", "region", "quantity", "unit_price", "amount"])


ext = demo_ext()
base = A.demo_df()
assert ext[ext.order_date <= "2025-12-31"].reset_index(drop=True).equals(base.reset_index(drop=True)), "generator mismatch"
print(f"history rows {len(base)}, extended rows {len(ext)} (identical first {len(base)} rows: verified)")

res = []
for name, kind in [("monthly amount (what the app forecasts)", "M"), ("weekly amount", "W"), ("daily amount", "D")]:
    if kind == "M":
        s_hist, freq = A.period_series(base, "order_date", "amount")
        truth = ext.set_index("order_date").amount.resample("MS").sum().loc["2026-01-01":"2026-06-01"].to_numpy(float)
        H = 6
    elif kind == "W":
        s_all = ext.set_index("order_date").amount.resample("W").sum()
        s_hist = s_all.loc[:"2025-12-28"].iloc[1:]
        truth = s_all.loc["2026-01-04":].iloc[:6].to_numpy(float)
        freq, H = "W", 6
    else:
        s_all = ext.set_index("order_date").amount.resample("D").sum()
        s_hist = s_all.loc[:"2025-12-31"].iloc[-120:]
        truth = s_all.loc["2026-01-01":].iloc[:14].to_numpy(float)
        freq, H = "D", 14
    y, idx, m = s_hist.to_numpy(float), s_hist.index, B.M_OF[freq]
    scale = float(np.mean(np.abs(np.diff(y))))
    for mname, fn in [("hw_current", B.m_hw_current), ("naive", B.m_naive), ("snaive", B.m_snaive), ("theta", B.m_theta), ("ets_auto", B.m_ets_auto), ("new", B.m_new)]:
        o = fn(y, idx, H, m, freq)
        res.append(dict(series=name, method=mname, MAE=np.mean(np.abs(truth - o["point"])), MASE=np.mean(np.abs(truth - o["point"])) / scale,
                        in80=np.mean((truth >= o["lo80"]) & (truth <= o["hi80"])), in95=np.mean((truth >= o["lo95"]) & (truth <= o["hi95"])),
                        model=o.get("cfg", "")))
df = pd.DataFrame(res)
print(df.round(3).to_string(index=False))
df.to_csv(HERE / "results" / "demo_check.csv", index=False)
r = FC.forecast_series(A.period_series(base, "order_date", "amount")[0], 6, "MS")
print("\nnew forecaster on the app's monthly demo series:", r["model_name"], "|", r["baseline_comparison"], "| confidence", r["confidence"])
print("forecast:", r["forecast"]["y"]); print("truth   :", [round(v, 2) for v in ext.set_index("order_date").amount.resample("MS").sum().loc["2026-01-01":"2026-06-01"].to_numpy(float)])
print("95% band:", list(zip(r["forecast"]["lower95"], r["forecast"]["upper95"])))
print("caveats:", *r["caveats"], sep="\n - ")
