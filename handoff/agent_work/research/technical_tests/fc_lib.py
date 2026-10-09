import warnings, time, itertools
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.forecasting.theta import ThetaModel

def mk(y, m=12):
    return pd.Series(np.asarray(y, float), index=pd.date_range("2000-01-01", periods=len(y), freq="MS"))

# ---------- baselines
def f_naive(y, h, m): return np.repeat(y.iloc[-1], h), None
def f_snaive(y, h, m):
    if len(y) < m: return f_naive(y, h, m)
    last = y.values[-m:]; return np.array([last[i % m] for i in range(h)]), None

# ---------- the app's current method (copied from analytics.forecast)
def f_app(y, h, m):
    seasonal = "add" if len(y) >= 2 * m else None
    try:
        fit = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal=seasonal, seasonal_periods=m if seasonal else None).fit()
    except Exception:
        fit = ExponentialSmoothing(y, trend="add").fit()
    fc = fit.forecast(h).values
    sd = float(np.std(fit.resid)) if len(fit.resid) else 0.0
    hh = np.sqrt(np.arange(1, h + 1))
    lo, hi = fc - 1.96 * sd * hh, fc + 1.96 * sd * hh
    if y.min() >= 0: lo = np.maximum(lo, 0)
    return fc, (lo, hi)

# ---------- ETSModel with AICc selection
def ets_candidates(n, m, positive):
    errs = ["add", "mul"] if positive else ["add"]
    trends = [(None, False), ("add", False), ("add", True)]
    seas = [None]
    if n >= 2 * m: seas += (["add", "mul"] if positive else ["add"])
    for e, (t, d), s in itertools.product(errs, trends, seas):
        yield dict(error=e, trend=t, damped_trend=d, seasonal=s)

def f_ets(y, h, m, return_info=False, criterion="aicc"):
    positive = bool((y > 0).all())
    best = None
    for c in ets_candidates(len(y), m, positive):
        try:
            mod = ETSModel(y, seasonal_periods=m if c["seasonal"] else None, initialization_method="estimated", **c)
            res = mod.fit(disp=False, maxiter=200)
            score = getattr(res, criterion)
            if not np.isfinite(score): continue
            if best is None or score < best[0]: best = (score, res, c)
        except Exception:
            continue
    if best is None: return f_snaive(y, h, m)
    res = best[1]
    pred = res.get_prediction(start=len(y), end=len(y) + h - 1)
    sf = pred.summary_frame(alpha=0.05)
    fc = sf["mean"].values
    lo, hi = sf["pi_lower"].values, sf["pi_upper"].values
    if not (np.isfinite(lo).all() and np.isfinite(hi).all()): lo = hi = None
    out = (fc, (lo, hi) if lo is not None else None)
    return (out + (best[2],)) if return_info else out

def f_theta(y, h, m):
    ds = len(y) >= 2 * m
    mod = ThetaModel(y, period=m if ds else None, deseasonalize=ds, method="additive" if ds else "auto")
    res = mod.fit()
    fc = res.forecast(h).values
    try:
        pi = res.prediction_intervals(h, alpha=0.05); lo, hi = pi.iloc[:, 0].values, pi.iloc[:, 1].values
    except Exception:
        lo = hi = None
    return fc, ((lo, hi) if lo is not None else None)

def f_comb(y, h, m):
    a = f_ets(y, h, m)[0]; b = f_theta(y, h, m)[0]; c = f_snaive(y, h, m)[0]
    return (a + b + c) / 3, None
def f_comb2(y, h, m):
    a = f_ets(y, h, m)[0]; b = f_theta(y, h, m)[0]
    return (a + b) / 2, None

METHODS = {"naive": f_naive, "snaive": f_snaive, "app_HW": f_app, "ETS_AICc": f_ets, "Theta": f_theta, "Comb(ETS,Theta)": f_comb2, "Comb(ETS,Theta,sNaive)": f_comb}

def mase_scale(y, m):
    k = m if len(y) > m else 1
    return np.mean(np.abs(y.values[k:] - y.values[:-k])) or np.nan

# ---------- fast, defensible candidate: (log-)STL seasonal adjustment + non-seasonal ETS chosen by AICc, with model-based PIs
from statsmodels.tsa.seasonal import STL
def f_stl_ets(y, h, m, return_info=False):
    n = len(y); positive = bool((y > 0).all())
    use_log = positive
    z = np.log(y) if use_log else y.copy()
    seas_future = np.zeros(h)
    if n >= 2 * m:
        stl = STL(z, period=m, robust=True).fit()
        S = stl.seasonal.values
        a = z - S
        last = S[-m:]
        seas_future = np.array([last[i % m] for i in range(h)])
    else:
        a = z
    best = None
    for tr, dm in [(None, False), ("add", False), ("add", True)]:
        try:
            res = ETSModel(a, error="add", trend=tr, damped_trend=dm, initialization_method="estimated").fit(disp=False, maxiter=100)
            sc = res.aicc
            if np.isfinite(sc) and (best is None or sc < best[0]): best = (sc, res, (tr, dm))
        except Exception:
            continue
    if best is None: return f_snaive(y, h, m)
    sf = best[1].get_prediction(start=n, end=n + h - 1).summary_frame(alpha=0.05)
    mean = sf["mean"].values + seas_future; lo = sf["pi_lower"].values + seas_future; hi = sf["pi_upper"].values + seas_future
    if use_log: mean, lo, hi = np.exp(mean), np.exp(lo), np.exp(hi)
    out = (mean, (lo, hi))
    return (out + (best[2],)) if return_info else out

def f_comb3(y, h, m):
    a = f_stl_ets(y, h, m)[0]; b = f_theta(y, h, m)[0]
    return (a + b) / 2, None

METHODS_FAST = {"naive": f_naive, "snaive": f_snaive, "app_HW": f_app, "Theta": f_theta, "STL+ETS(AICc)": f_stl_ets, "Comb(STL+ETS,Theta)": f_comb3}
