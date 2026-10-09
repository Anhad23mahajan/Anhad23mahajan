"""More candidate fixes for the interval: n=24 and n=36, seasonal on/off, with/without sd inflation sqrt(n/(n-k)), k = free params.
usage: <venv>/bin/python -I t_forecast_fix_candidates2.py [n_series]"""
import sys, warnings
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
warnings.simplefilter("ignore")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40; H = 6
def gen(kind, n, rng):
    t = np.arange(n + H)
    if kind == "stationary": y = 1000 + rng.normal(0, 100, n + H)
    elif kind == "trend": y = 1000 + 20 * t + rng.normal(0, 100, n + H)
    elif kind == "random_walk": y = 1000 + np.cumsum(rng.normal(5, 80, n + H))
    elif kind == "seasonal": y = 1000 + 10 * t + 300 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 60, n + H)
    else: y = (1000 + 10 * t) * (1 + .3 * np.sin(2 * np.pi * t / 12)) * np.exp(rng.normal(0, .08, n + H))
    return pd.Series(np.maximum(y, 1), index=pd.date_range("2020-01-01", periods=n + H, freq="MS"))
def run(y, n, seasonal, inflate):
    s, truth = y.iloc[:n], y.iloc[n:].values
    fit = ExponentialSmoothing(s, trend="add", damped_trend=True, seasonal="add" if seasonal else None, seasonal_periods=12 if seasonal else None).fit(); fc = fit.forecast(H).values
    sd = float(np.std(fit.resid))
    if inflate:
        k = int(len(fit.params_formatted)); sd *= np.sqrt(n / max(n - k, 3))
    h = np.sqrt(np.arange(1, H + 1)); return ((truth >= fc - 1.96 * sd * h) & (truth <= fc + 1.96 * sd * h)).mean(), np.mean(np.abs(fc - truth) / truth)
rng = np.random.default_rng(11)
print(f"coverage of nominal-95% band / MAPE ({N} series per cell)")
print(f"{'scenario':14s} {'n':>3s} | {'current(seas if n>=24)':>22s} | {'seas OFF':>12s} | {'inflate sd':>12s} | {'seas OFF+inflate':>16s}")
for n in (24, 36):
    for kind in ["stationary", "trend", "random_walk", "seasonal", "seasonal_mult"]:
        res = {k: [] for k in ("cur", "off", "inf", "offinf")}
        for _ in range(N):
            y = gen(kind, n, rng)
            res["cur"].append(run(y, n, True, False)); res["off"].append(run(y, n, False, False)); res["inf"].append(run(y, n, True, True)); res["offinf"].append(run(y, n, False, True))
        f = lambda k: f"{np.mean([a for a, b in res[k]])*100:5.1f}% /{np.mean([b for a, b in res[k]])*100:5.1f}%"
        print(f"{kind:14s} {n:3d} | {f('cur'):>22s} | {f('off'):>12s} | {f('inf'):>12s} | {f('offinf'):>16s}")
