"""Calibration backtest of analytics.forecast(): does the '95% range' contain the truth ~95% of the time?
usage: <venv>/bin/python -I t_forecast_backtest.py [n_series]"""
import sys, warnings, time
sys.dont_write_bytecode = True
import os; sys.path.insert(0, os.environ.get("LUMEN_DIR", "/home/user/Anhad23mahajan/lumen"))
import numpy as np, pandas as pd
from app import analytics as A
warnings.simplefilter("ignore")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
H = 6

def make_monthly(kind, n, rng):
    t = np.arange(n); idx = pd.date_range("2020-01-01", periods=n, freq="MS")
    if kind == "stationary": y = 1000 + rng.normal(0, 100, n)
    elif kind == "trend": y = 1000 + 20 * t + rng.normal(0, 100, n)
    elif kind == "random_walk": y = 1000 + np.cumsum(rng.normal(5, 80, n))
    elif kind == "seasonal": y = 1000 + 10 * t + 300 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 60, n)
    elif kind == "seasonal_mult": y = (1000 + 10 * t) * (1 + .3 * np.sin(2 * np.pi * t / 12)) * np.exp(rng.normal(0, .08, n))
    return idx, np.maximum(y, 1)

def backtest(kind, n_hist, rng):
    cover = []; width_ratio = []; errs = []; neg = 0; ok = 0
    for _ in range(N):
        idx, y = make_monthly(kind, n_hist + H, rng)
        # build raw event rows so period_series() resamples back to exactly these monthly sums (one row per month, mid-month)
        df = pd.DataFrame({"date": idx[:n_hist] + pd.Timedelta(days=14), "amount": y[:n_hist]})
        # make sure the last month isn't dropped as 'partial': add a month-end row of 0 value
        df = pd.concat([df, pd.DataFrame({"date": [idx[n_hist - 1] + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)], "amount": [0.0]})], ignore_index=True)
        try: f = A.forecast(df, "date", "amount", H)
        except Exception as e: continue
        ok += 1; lo = np.array(f["forecast"]["lower"]); hi = np.array(f["forecast"]["upper"]); fc = np.array(f["forecast"]["y"]); truth = y[n_hist:]
        cover.append(((truth >= lo) & (truth <= hi))); errs.append(np.abs(fc - truth) / truth); neg += int((fc < 0).any())
    c = np.array(cover)
    return ok, c.mean(), c.mean(axis=0), np.mean(errs)

rng = np.random.default_rng(1)
print(f"pandas {pd.__version__}; {N} simulated monthly series per cell; nominal coverage 95% (per-horizon h=1..{H} shown)")
print(f"{'scenario':16s} {'n_hist':>6s} {'ok':>4s} {'coverage':>9s}  per-horizon coverage             MAPE")
for kind in ["stationary", "trend", "random_walk", "seasonal", "seasonal_mult"]:
    for n_hist in [int(x) for x in os.environ.get('NH', '12,24,36').split(',')]:
        t = time.time(); ok, cov, ph, mape = backtest(kind, n_hist, rng)
        print(f"{kind:16s} {n_hist:6d} {ok:4d} {cov*100:8.1f}%  {np.round(ph*100).astype(int)}  {mape*100:5.1f}%   ({time.time()-t:.0f}s)")
