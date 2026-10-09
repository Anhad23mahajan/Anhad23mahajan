"""bench_forecast.py - reproducible rolling-origin benchmark for Lumen's forecaster.

Compares, on synthetic small-organisation business series (+ the repo's demo data):
  naive | snaive | hw_current (exactly analytics.forecast) | ets_auto (AICc grid) | theta | ensemble | new (forecasting.py) | [prophet]
Metrics: MASE (scaled by in-sample naive MAE), zero-safe sMAPE, relative MAE vs seasonal-naive,
         empirical coverage of nominal 80% / 95% intervals, scaled interval score.

Usage (from /home/user/work/ml):
    python bench_forecast.py --tag final --n 360 --seed 2026            # full benchmark (all methods)
    python bench_forecast.py --tag dev --n 120 --seed 1 --methods naive,snaive,hw_current,new   # design loop
Outputs go to results/<tag>/ : raw.csv.gz, meta.csv, series.csv, tables/*.csv, SUMMARY.md
"""
from __future__ import annotations

import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")   # statsmodels' tiny linear algebra is ~50x slower with BLAS thread oversubscription

import argparse
import json
import math
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LUMEN = Path("/home/user/Anhad23mahajan/lumen")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LUMEN))

Z80, Z95 = 1.2815515655446004, 1.959963984540054
M_OF = {"D": 7, "W": 52, "MS": 12}
ALL_METHODS = ["naive", "snaive", "hw_current", "ets_auto", "theta", "ensemble", "new"]


# ============================================================================ synthetic generator
def gen_series(seed: int, i: int):
    """One synthetic small-org series. Returns (values, DatetimeIndex, meta dict). Deterministic in (seed, i)."""
    rng = np.random.default_rng([seed, i])
    freq = str(rng.choice(["D", "W", "MS"], p=[0.30, 0.30, 0.40]))
    lo = {"D": 21, "W": 14, "MS": 14}[freq]
    n = int(round(math.exp(rng.uniform(math.log(lo), math.log(120)))))
    m = M_OF[freq]
    start = pd.Timestamp("2022-01-01") + pd.Timedelta(days=int(rng.integers(0, 365)))
    idx = pd.date_range(start, periods=n, freq=freq)
    if freq == "MS":
        idx = pd.date_range(start.to_period("M").to_timestamp(), periods=n, freq="MS")
    t = np.arange(n, dtype=float)

    count_mode = rng.random() < 0.25
    L = float(rng.uniform(4, 80)) if count_mode else float(np.clip(np.exp(rng.normal(np.log(800), 1.1)), 20, 2e5))

    # trend
    ttype = str(rng.choice(["none", "linear", "damped", "bend", "decline"], p=[0.30, 0.30, 0.12, 0.13, 0.15]))
    tot = {"none": 0.0, "linear": rng.uniform(0.1, 1.0), "damped": rng.uniform(0.2, 0.8),
           "bend": rng.uniform(0.2, 0.8), "decline": -rng.uniform(0.1, 0.45)}[ttype]
    u = t / max(n - 1, 1)
    if ttype == "damped":
        shape = (1 - np.exp(-3 * u)) / (1 - np.exp(-3))
    elif ttype == "bend":
        shape = np.minimum(u / 0.6, 1.0)
    else:
        shape = u
    trend = 1 + tot * shape

    # seasonality
    has_seas = bool(rng.random() < {"D": 0.65, "W": 0.30, "MS": 0.60}[freq])
    amp = float(rng.uniform(0.08, 0.55))
    if freq == "D":
        p = rng.normal(0, 1, 7)
        p = p / np.max(np.abs(p))
        s = amp * p[(np.arange(n) + int(rng.integers(0, 7))) % 7]
    else:
        P = 12.0 if freq == "MS" else 52.18
        ph = rng.uniform(0, 2 * np.pi, 2)
        a2 = rng.uniform(0, 0.5)
        raw = np.sin(2 * np.pi * t / P + ph[0]) + a2 * np.sin(4 * np.pi * t / P + ph[1])
        s = amp * raw / (1 + a2)
    if not has_seas:
        s = np.zeros(n)
    mult = bool(rng.random() < 0.7)
    base = L * trend

    # level shifts
    n_shift = 0
    shift_f = np.ones(n)
    if rng.random() < 0.25 and n >= 20:
        n_shift = int(rng.integers(1, 3))
        for _ in range(n_shift):
            pos = int(rng.uniform(0.25, 0.9) * n)
            shift_f[pos:] *= 1 + rng.choice([-1, 1]) * rng.uniform(0.15, 0.5)
    det = (base * (1 + s) if mult else base + L * s) * shift_f

    # noise
    nlevel = str(rng.choice(["low", "med", "high"], p=[0.3, 0.4, 0.3]))
    sd = {"low": rng.uniform(0.03, 0.07), "med": rng.uniform(0.08, 0.18), "high": rng.uniform(0.2, 0.4)}[nlevel]
    heavy = rng.random() < 0.30
    e = rng.standard_t(4, n) / math.sqrt(2.0) if heavy else rng.normal(0, 1, n)
    if rng.random() < 0.35:
        phi = rng.uniform(0, 0.5)
        for k in range(1, n):
            e[k] = phi * e[k - 1] + math.sqrt(1 - phi ** 2) * e[k]
    y = det * np.clip(1 + sd * e, 0.05, None)
    if count_mode:
        y = rng.poisson(np.clip(y, 0, None)).astype(float)

    # promo spikes
    n_spike = 0
    if rng.random() < 0.30 and n >= 15:
        n_spike = int(rng.integers(1, 5))
        for _ in range(n_spike):
            pos = int(rng.integers(3, n))
            y[pos] *= rng.uniform(1.5, 3.5)
            if rng.random() < 0.3 and pos + 1 < n:
                y[pos + 1] *= rng.uniform(1.3, 2.0)

    # intermittent zeros
    inter = bool(rng.random() < {"D": 0.15, "W": 0.15, "MS": 0.04}[freq])
    if inter:
        y[rng.random(n) < rng.uniform(0.1, 0.5)] = 0.0
    y = np.clip(y, 0, None)
    meta = dict(sid=f"s{i:04d}", kind="synthetic", freq=freq, n=n, m=m, level=round(L, 1), trend=ttype,
                seasonal=has_seas, seas_amp=round(amp if has_seas else 0.0, 3), mult=mult, shifts=n_shift, spikes=n_spike,
                intermittent=inter, noise=nlevel, heavy=heavy, count=count_mode)
    return y, idx, meta


def demo_series():
    """The repo's demo_df aggregated the way the app does (monthly) plus weekly and daily views."""
    import app.analytics as A   # read-only import
    df = A.demo_df()
    out = []
    s_m, f = A.period_series(df, "order_date", "amount")
    out.append(("demo_month_amount", s_m.to_numpy(float), s_m.index, "MS"))
    q = df.groupby("order_date")["quantity"].sum()
    q = q.reindex(pd.date_range(df.order_date.min(), df.order_date.max()), fill_value=0)
    out.append(("demo_month_qty", q.resample("MS").sum().to_numpy(float), q.resample("MS").sum().index, "MS"))
    a = df.groupby("order_date")["amount"].sum().reindex(pd.date_range(df.order_date.min(), df.order_date.max()), fill_value=0.0)
    w = a.resample("W").sum().iloc[1:-1]
    out.append(("demo_week_amount", w.to_numpy(float), w.index, "W"))
    wq = q.resample("W").sum().iloc[1:-1]
    out.append(("demo_week_qty", wq.to_numpy(float), wq.index, "W"))
    d = a.iloc[-120:]
    out.append(("demo_day_amount", d.to_numpy(float), d.index, "D"))
    dq = q.iloc[-120:]
    out.append(("demo_day_qty", dq.to_numpy(float), dq.index, "D"))
    metas = []
    for name, y, idx, fr in out:
        metas.append(dict(sid=name, kind="demo", freq=fr, n=len(y), m=M_OF[fr], level=round(float(np.mean(y)), 1), trend="demo",
                          seasonal=True, seas_amp=np.nan, mult=True, shifts=0, spikes=1 if "day" in name or "week" in name else 0,
                          intermittent=False, noise="demo", heavy=False, count="qty" in name))
    return [(y, idx, mt) for (name, y, idx, fr), mt in zip(out, metas)]


# ============================================================================ forecasting methods
def _floor(arrs, y_train):
    if np.min(y_train) >= 0:
        return [np.maximum(a, 0.0) for a in arrs]
    return arrs


def _pack(point, lo80, hi80, lo95, hi95, y_train):
    point, lo80, hi80, lo95, hi95 = _floor([point, lo80, hi80, lo95, hi95], y_train)
    return dict(point=np.asarray(point, float), lo80=np.asarray(lo80, float), hi80=np.asarray(hi80, float),
                lo95=np.asarray(lo95, float), hi95=np.asarray(hi95, float))


def _gauss_pack(point, sig, y_train):
    return _pack(point, point - Z80 * sig, point + Z80 * sig, point - Z95 * sig, point + Z95 * sig, y_train)


def m_naive(y, idx, H, m, freq):
    hs = np.arange(1, H + 1)
    sd = float(np.std(np.diff(y), ddof=1)) if len(y) > 2 else 0.0
    return _gauss_pack(np.full(H, y[-1]), sd * np.sqrt(hs), y)


def m_snaive(y, idx, H, m, freq):
    n = len(y)
    if n < m + 2 or m == 1:
        return m_naive(y, idx, H, m, freq)
    hs = np.arange(1, H + 1)
    point = y[-m:][(hs - 1) % m]
    sd = float(np.std(y[m:] - y[:-m], ddof=1))
    k = ((hs - 1) // m) + 1
    return _gauss_pack(point, sd * np.sqrt(k), y)


def m_hw_current(y, idx, H, m, freq):
    """Runs the repo's analytics.forecast() verbatim (period_series patched to return the given series)."""
    import app.analytics as A
    s = pd.Series(y, index=idx)
    d = pd.DataFrame({"d": idx, "v": y})
    with mock.patch.object(A, "period_series", lambda *a, **k: (s, freq)):
        r = A.forecast(d, "d", "v", H)
    f = r["forecast"]
    point, lo95, hi95 = np.array(f["y"], float), np.array(f["lower"], float), np.array(f["upper"], float)
    half = hi95 - point
    lo80, hi80 = point - half * Z80 / Z95, point + half * Z80 / Z95
    if np.min(y) >= 0:
        lo80 = np.maximum(lo80, 0)
    return dict(point=point, lo80=lo80, hi80=hi80, lo95=lo95, hi95=hi95)   # as shipped: no extra flooring of the point


def _ets_fit(y, m, error, trend, damped, seasonal):
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
    mod = ETSModel(y, error=error, trend=trend, damped_trend=damped if trend else False, seasonal=seasonal,
                   seasonal_periods=m if seasonal else None)
    return mod.fit(disp=False, maxiter=300)


def ets_auto_select(y, m):
    """Small robust grid over error/trend/damped/seasonal, AICc selection; failures skipped."""
    n = len(y)
    pos = bool(np.min(y) > 0)
    best, best_key = None, np.inf
    errs = ["add", "mul"] if pos else ["add"]
    seas_opts = [None]
    if m > 1 and n >= 2 * m:
        seas_opts += ["add"] + (["mul"] if pos else [])
    for e in errs:
        for trend, damped in ((None, False), ("add", False), ("add", True)):
            for sea in seas_opts:
                if e == "add" and sea == "mul":
                    continue
                try:
                    res = _ets_fit(y, m, e, trend, damped, sea)
                    a = float(res.aicc)
                    if not np.isfinite(a):
                        continue
                    fc = np.asarray(res.forecast(3))
                    if not np.all(np.isfinite(fc)):
                        continue
                    if a < best_key:
                        best, best_key = (res, (e, trend, damped, sea)), a
                except Exception:
                    continue
    return best


def m_ets_auto(y, idx, H, m, freq):
    b = ets_auto_select(y, m)
    if b is None:
        raise RuntimeError("no ETS model converged")
    res, cfg = b
    point = np.asarray(res.forecast(H), float)
    sim = res.simulate(nsimulations=H, anchor="end", repetitions=1000, rng=np.random.default_rng(0))
    sim = np.asarray(sim, float).reshape(H, -1)
    q = np.nanquantile(sim, [0.025, 0.10, 0.90, 0.975], axis=1)
    out = _pack(point, q[1], q[2], q[0], q[3], y)
    out["cfg"] = "/".join(str(c) for c in cfg)
    return out


def m_theta(y, idx, H, m, freq):
    from statsmodels.tsa.forecasting.theta import ThetaModel
    ds = bool(m > 1 and len(y) >= 2 * m)
    res = ThetaModel(y, period=m if ds else None, deseasonalize=ds).fit()
    point = np.asarray(res.forecast(H), float)
    i80 = res.prediction_intervals(steps=H, theta=2, alpha=0.20)
    i95 = res.prediction_intervals(steps=H, theta=2, alpha=0.05)
    return _pack(point, i80["lower"].to_numpy(), i80["upper"].to_numpy(), i95["lower"].to_numpy(), i95["upper"].to_numpy(), y)


def combine(parts):
    return {k: np.mean([p[k] for p in parts], axis=0) for k in ("point", "lo80", "hi80", "lo95", "hi95")}


def m_new(y, idx, H, m, freq):
    import forecasting as FC
    r = FC.forecast_series(pd.Series(y, index=idx), H, freq)
    if r["status"] == "refused":
        raise RuntimeError(r["reason"])
    f = r["forecast"]
    out = dict(point=np.array(f["y"], float), lo80=np.array(f["lower80"], float), hi80=np.array(f["upper80"], float),
               lo95=np.array(f["lower95"], float), hi95=np.array(f["upper95"], float))
    out["cfg"] = r["model"]
    out["conf"] = r["confidence"]
    out["rel_err"] = r["backtest"].get("relative_error")
    return out


def m_prophet(y, idx, H, m, freq):   # optional; only if prophet is importable
    import logging
    logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
    logging.getLogger("prophet").setLevel(logging.ERROR)
    from prophet import Prophet
    df = pd.DataFrame({"ds": idx, "y": y})
    mod = Prophet(interval_width=0.95, weekly_seasonality=(freq == "D"), yearly_seasonality=bool(len(y) >= 2 * (12 if freq == "MS" else 52) and freq != "D"),
                  daily_seasonality=False)
    mod.fit(df)
    fut = pd.DataFrame({"ds": pd.date_range(idx[-1], periods=H + 1, freq=freq)[1:]})
    p95 = mod.predict(fut)
    mod2 = Prophet(interval_width=0.80, weekly_seasonality=(freq == "D"), yearly_seasonality=bool(len(y) >= 2 * (12 if freq == "MS" else 52) and freq != "D"),
                   daily_seasonality=False)
    mod2.fit(df)
    p80 = mod2.predict(fut)
    return _pack(p95["yhat"].to_numpy(), p80["yhat_lower"].to_numpy(), p80["yhat_upper"].to_numpy(), p95["yhat_lower"].to_numpy(), p95["yhat_upper"].to_numpy(), y)


def m_comp(name):
    """Fixed single component from forecasting.py (no selection, zero-width bands): for design analysis only."""
    def f(y, idx, H, m, freq):
        import forecasting as FC
        n = len(y)
        if name in ("ets_s", "ets_s_log") and not (m > 1 and n >= 2 * m):
            raise RuntimeError("not eligible")
        if name == "ets_s_log" and np.min(y) <= 0:
            raise RuntimeError("not eligible")
        if name in ("combo_trend", "combo_seasonal"):
            mem = ["theta", "damped", "ses"] if name == "combo_trend" else ["ets_s", "ets_s_log", "theta", "snaive"]
            fcs = []
            for c in mem:
                try:
                    if c in ("ets_s", "ets_s_log") and not (m > 1 and n >= 2 * m):
                        continue
                    if c == "ets_s_log" and np.min(y) <= 0:
                        continue
                    if c == "snaive" and not (m > 1 and n >= m):
                        continue
                    fcs.append(FC._comp_forecast(c, y, H, m))
                except Exception:
                    pass
            if len(fcs) < 2:
                raise RuntimeError("combo failed")
            fc = np.mean(fcs, axis=0)
        else:
            fc = FC._comp_forecast(name, y, H, m)
        fc = np.maximum(fc, 0) if np.min(y) >= 0 else fc
        return dict(point=fc, lo80=fc, hi80=fc, lo95=fc, hi95=fc)
    return f


METHOD_FN = {"naive": m_naive, "snaive": m_snaive, "hw_current": m_hw_current, "ets_auto": m_ets_auto, "theta": m_theta,
             "new": m_new, "prophet": m_prophet}
for _c in ("ses", "damped", "theta", "ets_s", "ets_s_log", "combo_trend", "combo_seasonal"):
    METHOD_FN["c_" + _c] = m_comp(_c)


def run_method(name, y, idx, H, m, freq, cache):
    """Run one method; on failure fall back to naive for that fold and flag it."""
    t0 = time.perf_counter()
    fb = False
    comp_ms = 0.0
    try:
        if name == "ensemble":
            parts = [cache["ets_auto"], cache["theta"], cache["snaive"]]
            if any(p is None for p in parts):
                raise RuntimeError("component failed")
            out = combine(parts)
            comp_ms = sum(p["ms"] for p in parts)
        else:
            out = METHOD_FN[name](y, idx, H, m, freq)
        if not all(np.all(np.isfinite(out[k])) for k in ("point", "lo80", "hi80", "lo95", "hi95")):
            raise RuntimeError("non-finite output")
    except Exception:
        out = m_naive(y, idx, H, m, freq)
        fb = True
    out["ms"] = 1000 * (time.perf_counter() - t0) + (comp_ms if name == "ensemble" and not fb else 0.0)
    out["fallback"] = fb
    return out


# ============================================================================ evaluation worker
def pick_origins(n, H, k):
    n0 = max(8, int(math.ceil(0.4 * n)))
    last = n - H
    if last < 8:
        return []
    if last <= n0:
        return [last] if last >= 8 else []
    return sorted(set(int(round(v)) for v in np.linspace(n0, last, k)))


def evaluate_series(task):
    y, idx, meta, H, methods, k_orig = task
    warnings.simplefilter("ignore")
    m, freq, n = meta["m"], meta["freq"], len(y)
    rows, metas = [], []
    for t in pick_origins(n, H, k_orig):
        ytr, itr = y[:t], idx[:t]
        scale = float(np.mean(np.abs(np.diff(ytr))))
        yte = y[t:t + H]
        cache = {}
        for name in methods:   # order matters for ensemble components
            if name == "ensemble":
                comp = {}
                for c in ("ets_auto", "theta", "snaive"):
                    comp[c] = cache.get(c)
                res = run_method("ensemble", ytr, itr, H, m, freq, {c: (None if (cache.get(c) is None or cache[c]["fallback"]) else cache[c]) for c in comp})
            else:
                res = run_method(name, ytr, itr, H, m, freq, cache)
            cache[name] = res
            metas.append(dict(sid=meta["sid"], origin=t, n_train=t, method=name, ms=res["ms"], fallback=res["fallback"],
                              cfg=res.get("cfg"), conf=res.get("conf"), rel_err=res.get("rel_err")))
            for h in range(H):
                rows.append((meta["sid"], t, h + 1, name, yte[h], res["point"][h], res["lo80"][h], res["hi80"][h],
                             res["lo95"][h], res["hi95"][h], scale))
    return rows, metas


RAW_COLS = ["sid", "origin", "h", "method", "y", "f", "lo80", "hi80", "lo95", "hi95", "scale"]


# ============================================================================ aggregation
def smape_term(y, f):
    d = np.abs(y) + np.abs(f)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(d > 0, 2 * np.abs(y - f) / d, 0.0)


def add_metrics(raw: pd.DataFrame) -> pd.DataFrame:
    r = raw.copy()
    r["ae"] = (r.y - r.f).abs()
    ok = r.scale > 1e-9
    r["ase"] = np.where(ok, r.ae / r.scale.where(ok, 1.0), np.nan)
    r["smape"] = smape_term(r.y.to_numpy(), r.f.to_numpy()) * 100
    for lev, (lo, hi, al) in {"80": ("lo80", "hi80", 0.20), "95": ("lo95", "hi95", 0.05)}.items():
        r[f"in{lev}"] = ((r.y >= r[lo]) & (r.y <= r[hi])).astype(float)
        w = r[hi] - r[lo]
        pen = (2 / al) * (np.maximum(r[lo] - r.y, 0) + np.maximum(r.y - r[hi], 0))
        r[f"wid{lev}"] = np.where(ok, w / r.scale.where(ok, 1.0), np.nan)
        r[f"is{lev}"] = np.where(ok, (w + pen) / r.scale.where(ok, 1.0), np.nan)
    sn = r[r.method == "snaive"][["sid", "origin", "h", "ae"]].rename(columns={"ae": "ae_sn"})
    r = r.merge(sn, on=["sid", "origin", "h"], how="left")
    return r


def per_series(r: pd.DataFrame) -> pd.DataFrame:
    g = r.groupby(["sid", "method"])
    ps = g.agg(mase=("ase", "mean"), smape=("smape", "mean"), cov80=("in80", "mean"), cov95=("in95", "mean"),
               is95=("is95", "mean"), is80=("is80", "mean"), wid95=("wid95", "mean"), mae=("ae", "mean"), mae_sn=("ae_sn", "mean"),
               zero_frac=("y", lambda v: float(np.mean(v == 0))), n_obs=("y", "size")).reset_index()
    ps["rmae"] = ps.mae / ps.mae_sn.where(ps.mae_sn > 0)
    return ps


def gmean(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v) & (v > 0)]
    return float(np.exp(np.mean(np.log(v)))) if len(v) else np.nan


def overall_table(r, ps):
    rows = []
    for mth, g in ps.groupby("method"):
        rr = r[r.method == mth]
        rows.append(dict(method=mth, series=g.sid.nunique(), obs=len(rr),
                         MASE_median=g.mase.median(), MASE_mean=g.mase.mean(), MASE_trim10=float(np.mean(np.sort(g.mase.dropna())[int(0.1 * g.mase.notna().sum()):int(0.9 * g.mase.notna().sum()) or None])),
                         sMAPE_median=g.smape.median(), relMAE_vs_snaive_gmean=gmean(g.rmae),
                         cov80_pooled=rr.in80.mean(), cov95_pooled=rr.in95.mean(),
                         cov80_median_series=g.cov80.median(), cov95_median_series=g.cov95.median(),
                         scaled_IS95_median=g.is95.median(), scaled_width95_median=g.wid95.median()))
    out = pd.DataFrame(rows).set_index("method")
    return out


def segments(ps, meta, r, orig_meta):
    m = meta.set_index("sid")
    ps = ps.join(m[["freq", "n", "seasonal", "intermittent", "noise", "kind", "spikes", "shifts", "trend", "count"]], on="sid")
    r = r.join(m[["freq", "seasonal", "intermittent", "noise", "kind", "spikes", "shifts", "count"]], on="sid")
    # history length at origin (training length), a per-origin attribute
    r = r.assign(hb=pd.cut(r.origin, [0, 18, 47, 10 ** 6], labels=["short (<=18)", "medium (19-47)", "long (>=48)"]))
    ps_hist = r.groupby(["sid", "method", "hb"], observed=True).agg(mase=("ase", "mean"), smape=("smape", "mean"), cov80=("in80", "mean"),
                                                                   cov95=("in95", "mean")).reset_index()
    segs = {}
    segs["history"] = ps_hist.assign(seg=ps_hist.hb.astype(str))
    segs["seasonal"] = ps.assign(seg=np.where(ps.seasonal, "seasonal", "non-seasonal"))
    segs["freq"] = ps.assign(seg=ps.freq)
    segs["intermittent"] = ps.assign(seg=np.where(ps.intermittent, "intermittent", "continuous"))
    segs["noise"] = ps.assign(seg=ps.noise)
    segs["events"] = ps.assign(seg=np.where((ps.spikes > 0) | (ps.shifts > 0), "has spike/shift", "clean"))
    segs["kind"] = ps.assign(seg=ps.kind)
    out = []
    for name, d in segs.items():
        for (seg, mth), g in d.groupby(["seg", "method"], observed=True):
            rr = r
            out.append(dict(segment_type=name, segment=seg, method=mth, series=g.sid.nunique(), MASE_median=g.mase.median(),
                            sMAPE_median=g.smape.median(), cov80=g.cov80.mean(), cov95=g.cov95.mean()))
    return pd.DataFrame(out)


def pooled_cov_by_segment(r, meta):
    m = meta.set_index("sid")
    rr = r.join(m[["freq", "seasonal", "intermittent", "noise", "kind"]], on="sid")
    rr = rr.assign(hb=pd.cut(rr.origin, [0, 18, 47, 10 ** 6], labels=["short (<=18)", "medium (19-47)", "long (>=48)"]).astype(str))
    out = []
    for name, col in [("history", "hb"), ("seasonal", "seasonal"), ("freq", "freq"), ("intermittent", "intermittent"), ("noise", "noise"), ("kind", "kind")]:
        for (seg, mth), g in rr.groupby([col, "method"]):
            out.append(dict(segment_type=name, segment=str(seg), method=mth, obs=len(g), cov80=g.in80.mean(), cov95=g.in95.mean(),
                            MAE_over_scale=g.ase.mean()))
    return pd.DataFrame(out)


def coverage_by_h(r):
    return r.groupby(["method", "h"]).agg(cov80=("in80", "mean"), cov95=("in95", "mean"), MASE=("ase", "mean")).reset_index()


def paired(ps, a, b, B=4000, seed=0):
    """Per-series MASE ratio a/b: geometric mean with bootstrap CI, win rate, Wilcoxon."""
    from scipy import stats
    x = ps[ps.method == a].set_index("sid").mase
    z = ps[ps.method == b].set_index("sid").mase
    d = pd.concat([x, z], axis=1, keys=["a", "b"]).dropna()
    d = d[(d.a > 0) & (d.b > 0)]
    if len(d) < 5:
        return None
    lr = np.log(d.a / d.b).to_numpy()
    rng = np.random.default_rng(seed)
    bs = np.array([lr[rng.integers(0, len(lr), len(lr))].mean() for _ in range(B)])
    try:
        p = float(stats.wilcoxon(lr).pvalue)
    except Exception:
        p = np.nan
    return dict(a=a, b=b, n=len(d), gmean_ratio=float(np.exp(lr.mean())), ci_lo=float(np.exp(np.quantile(bs, 0.025))),
                ci_hi=float(np.exp(np.quantile(bs, 0.975))), win_rate_a=float(np.mean(lr < 0)), median_ratio=float(np.exp(np.median(lr))),
                wilcoxon_p=p)


def cluster_cov_ci(r, method, col, B=2000, seed=0):
    d = r[r.method == method].groupby("sid")[col].agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    s, c = d["sum"].to_numpy(), d["count"].to_numpy()
    est = s.sum() / c.sum()
    bs = []
    for _ in range(B):
        ii = rng.integers(0, len(s), len(s))
        bs.append(s[ii].sum() / c[ii].sum())
    return est, float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))


def md_table(df: pd.DataFrame, floatfmt="{:.3f}", index=True) -> str:
    d = df.reset_index() if index else df
    cols = list(d.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in d.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if not np.isfinite(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ============================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="dev")
    ap.add_argument("--n", type=int, default=360, help="number of synthetic series")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--methods", default=",".join(ALL_METHODS))
    ap.add_argument("--H", type=int, default=6)
    ap.add_argument("--origins", type=int, default=6)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--long", action="store_true", help="also run horizon-12 pass on monthly series with >= 36 periods")
    ap.add_argument("--no-demo", action="store_true")
    ap.add_argument("--cfg", default="", help="JSON overrides for forecasting.CFG (ablations)")
    ap.add_argument("--prophet-sample", type=int, default=0, help="(unused in main venv) run prophet via a separate venv, then --merge")
    ap.add_argument("--report-only", action="store_true", help="recompute tables from results/<tag>/raw.csv.gz")
    ap.add_argument("--merge", default="", help="comma-separated extra raw.csv.gz/meta.csv.gz prefixes (dirs) to concatenate before reporting")
    a = ap.parse_args()

    methods = [m for m in a.methods.split(",") if m]
    if "ensemble" in methods:   # ensure components precede it
        for c in ("ets_auto", "theta", "snaive"):
            if c not in methods:
                methods.insert(0, c)
        methods = [m for m in methods if m != "ensemble"] + ["ensemble"]
    if a.cfg:
        import forecasting as FC
        FC.CFG.update(json.loads(a.cfg))

    out_dir = HERE / "results" / a.tag
    (out_dir / "tables").mkdir(parents=True, exist_ok=True)

    series = [gen_series(a.seed, i) for i in range(a.n)]
    if not a.no_demo:
        series += demo_series()
    metas = pd.DataFrame([s[2] for s in series])
    if a.report_only:
        raw = pd.read_csv(out_dir / "raw.csv.gz")
        omd = pd.read_csv(out_dir / "meta.csv")
        for d_ in [x for x in a.merge.split(",") if x]:
            raw = pd.concat([raw, pd.read_csv(Path(d_) / "raw.csv.gz")], ignore_index=True)
            omd = pd.concat([omd, pd.read_csv(Path(d_) / "meta.csv")], ignore_index=True)
        report(a, out_dir, raw, omd, metas, tag_h=f"H={a.H}")
        if a.long and (out_dir / "h12" / "raw.csv.gz").exists():
            sub = [s for s in series if s[2]["freq"] == "MS" and s[2]["n"] >= 36]
            d12 = out_dir / "h12"
            report(a, d12, pd.read_csv(d12 / "raw.csv.gz"), pd.read_csv(d12 / "meta.csv"), pd.DataFrame([s[2] for s in sub]), tag_h="H=12 (monthly, >=36 periods)")
        return
    print(f"series: {len(series)} ({metas.kind.value_counts().to_dict()}), freq mix {metas.freq.value_counts().to_dict()}, "
          f"n median {int(metas.n.median())}, min {metas.n.min()}, max {metas.n.max()}", flush=True)

    def run_pass(H, subset, label, meths):
        tasks = [(y, idx, mt, H, meths, a.origins) for (y, idx, mt) in subset]
        rows, mrows = [], []
        t0 = time.time()
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for k, (r_, m_) in enumerate(ex.map(evaluate_series, tasks, chunksize=2)):
                rows += r_
                mrows += m_
                if (k + 1) % 40 == 0:
                    print(f"  [{label}] {k + 1}/{len(tasks)} series, {time.time() - t0:.0f}s", flush=True)
        raw = pd.DataFrame(rows, columns=RAW_COLS)
        return raw, pd.DataFrame(mrows)

    t_start = time.time()
    raw, omd = run_pass(a.H, series, f"H={a.H}", methods)
    raw.to_csv(out_dir / "raw.csv.gz", index=False)
    omd.to_csv(out_dir / "meta.csv", index=False)
    metas.to_csv(out_dir / "series.csv", index=False)
    print(f"evaluation done in {time.time() - t_start:.0f}s; {len(raw)} forecast-point rows", flush=True)

    report(a, out_dir, raw, omd, metas, tag_h=f"H={a.H}")
    if a.long:
        sub = [s for s in series if s[2]["freq"] == "MS" and s[2]["n"] >= 36]
        raw12, omd12 = run_pass(12, sub, "H=12", methods)
        d12 = out_dir / "h12"
        (d12 / "tables").mkdir(parents=True, exist_ok=True)
        raw12.to_csv(d12 / "raw.csv.gz", index=False)
        omd12.to_csv(d12 / "meta.csv", index=False)
        metas12 = pd.DataFrame([s[2] for s in sub])
        report(a, d12, raw12, omd12, metas12, tag_h="H=12 (monthly, >=36 periods)")


def report(a, out_dir, raw, omd, metas, tag_h):
    r = add_metrics(raw)
    ps = per_series(r)
    ov = overall_table(r, ps)
    ov["ms_per_call_mean"] = omd.groupby("method").ms.mean()
    ov["ms_per_call_p95"] = omd.groupby("method").ms.quantile(0.95)
    ov["fallback_rate"] = omd.groupby("method").fallback.mean()
    seg = segments(ps, metas, r, omd)
    pcs = pooled_cov_by_segment(r, metas)
    cbh = coverage_by_h(r)
    ov.to_csv(out_dir / "tables" / "overall.csv")
    seg.to_csv(out_dir / "tables" / "by_segment_median.csv", index=False)
    pcs.to_csv(out_dir / "tables" / "by_segment_pooled_coverage.csv", index=False)
    cbh.to_csv(out_dir / "tables" / "by_horizon.csv", index=False)
    ps.to_csv(out_dir / "tables" / "per_series.csv", index=False)

    lines = [f"# Forecast benchmark - {a.tag} - {tag_h}", "",
             f"Series: {metas.shape[0]} ({metas.kind.value_counts().to_dict()}); origins per series <= {a.origins}; horizon 1..{r.h.max()}; "
             f"seed {a.seed}; forecast points scored: {len(r[r.method == 'naive'])} per method.", "",
             "## Overall (lower MASE/sMAPE is better; coverage should be near 0.80 / 0.95)", "",
             md_table(ov[["series", "MASE_median", "MASE_mean", "sMAPE_median", "relMAE_vs_snaive_gmean", "cov80_pooled", "cov95_pooled",
                          "cov95_median_series", "scaled_IS95_median", "ms_per_call_mean", "fallback_rate"]]), ""]
    if "hw_current" in ps.method.values and "new" in ps.method.values:
        pr = []
        for b in ("hw_current", "snaive", "naive", "ets_auto", "theta", "ensemble"):
            if b in ps.method.values:
                x = paired(ps, "new", b)
                if x:
                    pr.append(x)
        if pr:
            lines += ["## Paired per-series MASE ratio, new / other (<1 means new is better; geometric mean, 95% bootstrap CI over series)", "",
                      md_table(pd.DataFrame(pr).set_index("b")[["n", "gmean_ratio", "ci_lo", "ci_hi", "median_ratio", "win_rate_a", "wilcoxon_p"]]), ""]
        cl = []
        for mth in ("hw_current", "new"):
            if mth in ps.method.values:
                for col, nom in (("in80", 0.80), ("in95", 0.95)):
                    est, lo, hi = cluster_cov_ci(r, mth, col)
                    cl.append(dict(method=mth, nominal=nom, coverage=est, ci_lo=lo, ci_hi=hi))
        lines += ["## Interval coverage with 95% cluster-bootstrap CI (resampling series)", "", md_table(pd.DataFrame(cl).set_index("method")), ""]
    sel = seg[seg.method.isin([m for m in ("naive", "snaive", "hw_current", "ets_auto", "theta", "ensemble", "new") if m in ps.method.values])]
    for st in ("history", "seasonal", "freq", "intermittent", "noise", "events", "kind"):
        d = sel[sel.segment_type == st]
        if d.empty:
            continue
        pv = d.pivot(index="segment", columns="method", values="MASE_median")
        cv95 = pcs[(pcs.segment_type == st) & pcs.method.isin(["hw_current", "new"])].pivot(index="segment", columns="method", values="cov95") if st != "events" else None
        lines += [f"### By {st}: median MASE", "", md_table(pv), ""]
        if cv95 is not None and not cv95.empty:
            cv80 = pcs[(pcs.segment_type == st) & pcs.method.isin(["hw_current", "new"])].pivot(index="segment", columns="method", values="cov80")
            cv = pd.concat([cv80.add_suffix("_cov80"), cv95.add_suffix("_cov95")], axis=1)
            lines += [f"### By {st}: pooled interval coverage", "", md_table(cv), ""]
    hh = cbh[cbh.method.isin(["hw_current", "new"])].pivot(index="h", columns="method", values=["cov80", "cov95", "MASE"])
    hh.columns = [f"{b}_{a_}" for a_, b in hh.columns]
    lines += ["### By horizon step", "", md_table(hh), ""]
    if "new" in omd.method.values:
        nm = omd[omd.method == "new"]
        lines += ["### New method: chosen model frequency", "", md_table(nm.cfg.value_counts().rename("count").to_frame()), ""]
        lines += ["### New method: confidence label vs realised error", ""]
        cf = nm[["sid", "origin", "conf"]].merge(
            r[r.method == "new"].groupby(["sid", "origin"]).agg(ase=("ase", "mean"), in80=("in80", "mean"), in95=("in95", "mean"), y=("y", "sum"), ae=("ae", "sum")).reset_index(),
            on=["sid", "origin"])
        cf["wape"] = cf.ae / cf.y.where(cf.y > 0)
        cft = cf.groupby("conf").agg(forecasts=("sid", "size"), MASE_median=("ase", "median"), WAPE_median=("wape", "median"), cov80=("in80", "mean"), cov95=("in95", "mean"))
        lines += [md_table(cft), ""]
        cft.to_csv(out_dir / "tables" / "confidence_vs_error.csv")
    (out_dir / "SUMMARY.md").write_text("\n".join(lines))
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
