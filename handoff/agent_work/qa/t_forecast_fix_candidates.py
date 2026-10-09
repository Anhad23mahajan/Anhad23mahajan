"""Coverage of candidate interval fixes vs current code, n_hist=24 (the demo's configuration).
A: current (resid std * sqrt(h));  B: statsmodels ETSModel analytic prediction intervals;  C: sd inflated by sqrt(n/(n-k)) with k=#fitted params
usage: <venv>/bin/python -I t_forecast_fix_candidates.py [n_series]"""
import sys, warnings
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import numpy as np, pandas as pd
from app import analytics as A
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
warnings.simplefilter("ignore")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60; H = 6; n = 24
def gen(kind, rng):
    t = np.arange(n + H)
    if kind == "stationary": y = 1000 + rng.normal(0, 100, n + H)
    elif kind == "trend": y = 1000 + 20 * t + rng.normal(0, 100, n + H)
    elif kind == "random_walk": y = 1000 + np.cumsum(rng.normal(5, 80, n + H))
    elif kind == "seasonal": y = 1000 + 10 * t + 300 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 60, n + H)
    else: y = (1000 + 10 * t) * (1 + .3 * np.sin(2 * np.pi * t / 12)) * np.exp(rng.normal(0, .08, n + H))
    return pd.Series(np.maximum(y, 1), index=pd.date_range("2020-01-01", periods=n + H, freq="MS"))
rng = np.random.default_rng(5)
print(f"{'scenario':14s} {'A current':>10s} {'B ETS analytic':>15s} {'C inflated sd':>14s}   (95% nominal, n_hist={n}, {N} series)")
for kind in ["stationary", "trend", "random_walk", "seasonal", "seasonal_mult"]:
    ca, cb, cc = [], [], []
    for _ in range(N):
        y = gen(kind, rng); s, truth = y.iloc[:n], y.iloc[n:].values
        # A
        fit = ExponentialSmoothing(s, trend="add", damped_trend=True, seasonal="add", seasonal_periods=12).fit(); fc = fit.forecast(H).values
        sd = float(np.std(fit.resid)); h = np.sqrt(np.arange(1, H + 1)); lo, hi = fc - 1.96 * sd * h, fc + 1.96 * sd * h
        ca.append(((truth >= lo) & (truth <= hi)).mean())
        k = len(fit.params_formatted) if hasattr(fit, "params_formatted") else 16
        sdc = sd * np.sqrt(n / max(n - k, 3)); loc, hic = fc - 1.96 * sdc * h, fc + 1.96 * sdc * h
        cc.append(((truth >= loc) & (truth <= hic)).mean())
        try:
            m = ETSModel(s, error="add", trend="add", damped_trend=True, seasonal="add", seasonal_periods=12).fit(disp=False)
            sf = m.get_prediction(start=n, end=n + H - 1).summary_frame(alpha=0.05)
            cb.append(((truth >= sf["pi_lower"].values) & (truth <= sf["pi_upper"].values)).mean())
        except Exception: pass
    print(f"{kind:14s} {np.mean(ca)*100:9.1f}% {np.mean(cb)*100:14.1f}% {np.mean(cc)*100:13.1f}%")
