"""drivers.py - anomalies, change points and "what drove the change" for small-business tables.

Everything here is deterministic arithmetic on the user's own data (pandas, numpy, scipy, statsmodels STL).
Each finding is a dict:  {kind, severity, title, detail, action, evidence}  where `evidence` holds the exact
numbers behind every figure quoted in `detail`.  No function raises on odd input: failures return [] / None.

Main entry points
-----------------
analyze(df, date_col, metric_col, dims, ...)            -> list[finding]   (everything below, ranked)
detect_anomalies(df, date_col, metric_col, dims, ...)   -> list[finding]   (STL / day-of-week-adjusted, with segment attribution)
variance_bridge(df, date_col, metric_col, dims, ...)    -> finding | None  (exact additive period-over-period bridge; price/volume/mix if qty*price)
decompose_change(df_a, df_b, metric_col, dim, ...)      -> dict            (the exact decomposition behind the bridge)
detect_change_points(series, ...)                       -> list[dict]      (guarded level-shift detection)
concentration(df, metric_col, dims)                     -> list[finding]   (HHI / top-N share)
entity_metrics(df, entity_col, date_col, metric_col)    -> list[finding]   (repeat rate, retention, churn proxy)
infer_roles(df)                                         -> dict            (quantity / price / entity column guesses)
"""
from __future__ import annotations

import math
import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats

__all__ = ["analyze", "detect_anomalies", "variance_bridge", "decompose_change", "detect_change_points",
           "concentration", "entity_metrics", "infer_roles", "false_positive_study"]

MEAN_HINT = re.compile(r"price|rate|score|age|temp|ratio|avg|average|pct|percent", re.I)   # same rule as analytics.agg_for
QTY_HINT = re.compile(r"(^|_)(qty|quantity|units?|items|count)(_|$)", re.I)
PRICE_HINT = re.compile(r"(^|_)(unit_?price|price|unit_?cost|rate)(_|$)", re.I)
ENTITY_HINT = re.compile(r"(donor|customer|client|member|supporter|buyer|patron|contact|account|volunteer|student|user)(_?(id|name|no|number|key))?$", re.I)

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ============================================================================ small helpers
def _agg_for(metric: str) -> str:
    return "mean" if MEAN_HINT.search(metric or "") else "sum"


def _f(x) -> float:
    return float(x) if x is not None and np.isfinite(x) else None


def _num(x) -> str:
    """Human number from a data value (no rounding of meaning, just display)."""
    if x is None or not np.isfinite(x):
        return "n/a"
    a = abs(x)
    if a >= 100:
        return f"{x:,.0f}"
    if a >= 10:
        return f"{x:,.1f}"
    return f"{x:,.2f}"


def _pct(x, digits=0) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{x:+.{digits}f}%"


def _d(ts) -> str:
    return pd.Timestamp(ts).strftime("%d %b %Y")


def _item(kind, severity, title, detail, action, evidence):
    return {"kind": kind, "severity": severity, "title": title, "detail": detail, "action": action, "evidence": evidence}


def _prep(df, date_col, metric_col):
    """Copy of the needed columns with parsed dates and numeric metric; NaN rows dropped. Returns None if unusable."""
    if df is None or date_col not in df.columns or metric_col not in df.columns:
        return None
    d = pd.DataFrame({"_t": pd.to_datetime(df[date_col], errors="coerce"), "_v": pd.to_numeric(df[metric_col], errors="coerce")}, index=df.index)
    if getattr(d["_t"].dt, "tz", None) is not None:
        d["_t"] = d["_t"].dt.tz_localize(None)
    d = d.replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < 5:
        return None
    return d


def _valid_dims(df, dims, max_unique=50):
    out = []
    for c in dims or []:
        if c in df.columns and 2 <= df[c].nunique(dropna=True) <= max_unique:
            out.append(c)
    return out


def _seg_series(df, c):
    return df[c].astype("string").fillna("(missing)").astype(str)


def _resolution(days: pd.DatetimeIndex) -> str:
    """'D', 'W' or 'M' from the typical gap between distinct dates."""
    u = pd.DatetimeIndex(sorted(set(days)))
    if len(u) < 3:
        return "D"
    gap = float(np.median(np.diff(u.values).astype("timedelta64[D]").astype(float)))
    return "D" if gap <= 3 else "W" if gap <= 10 else "M"


def infer_roles(df: pd.DataFrame) -> dict:
    """Best-guess quantity, unit-price and entity (donor/customer) columns. Any may be None."""
    cols = list(df.columns)
    num = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    qty = next((c for c in num if QTY_HINT.search(c)), None)
    price = next((c for c in num if PRICE_HINT.search(c) and c != qty), None)
    ent = None
    for c in cols:
        if ENTITY_HINT.search(c) and not pd.api.types.is_datetime64_any_dtype(df[c]):
            nu = df[c].nunique(dropna=True)
            if 2 <= nu < 0.95 * len(df):
                ent = c
                break
    return {"qty_col": qty, "price_col": price, "entity_col": ent}


# ============================================================================ STL / robust expectation
def _next_odd(x):
    x = int(math.ceil(x))
    return x if x % 2 == 1 else x + 1


def _expected(y: np.ndarray, period: int):
    """Robust 'what we would normally see': STL (robust) with weekly/annual cycle if the history supports it,
    otherwise a centred rolling median. Returns (expected, method_text)."""
    n = len(y)
    if period > 1 and n >= max(4 * period, 28):
        from statsmodels.tsa.seasonal import STL
        trend = _next_odd(max(2.5 * period, 15)) if period <= 12 else _next_odd(1.5 * period)
        res = STL(pd.Series(y), period=period, robust=True, seasonal=7, trend=trend).fit()
        return (np.asarray(res.trend) + np.asarray(res.seasonal)), f"robust STL (period {period})"
    w = _next_odd(min(max(5, n // 4), 15))
    base = pd.Series(y).rolling(w, center=True, min_periods=max(3, w // 2)).median().to_numpy()
    return base, f"rolling median ({w} periods), no seasonal cycle"


def _hetero_sigma(resid: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """Robust residual scale that may grow with the expected level (sigma ~ a * expected^g, g in [0,1])."""
    r = resid - np.nanmedian(resid)
    glob = 1.4826 * np.nanmedian(np.abs(r))
    if not np.isfinite(glob) or glob <= 0:
        glob = 1.4826 * np.nanmean(np.abs(r)) / 1.2533 if np.nanmean(np.abs(r)) > 0 else 1e-9
    e = np.maximum(expected, 1e-9)
    n = len(r)
    if n >= 60 and np.ptp(np.log(e)) > 0.3:
        qs = np.quantile(e, [0, .25, .5, .75, 1.0])
        xs, ys = [], []
        for i in range(4):
            m = (e >= qs[i]) & (e <= qs[i + 1]) if i == 3 else (e >= qs[i]) & (e < qs[i + 1])
            if m.sum() >= 12:
                mad = 1.4826 * np.median(np.abs(r[m] - np.median(r[m])))
                if mad > 0:
                    xs.append(np.log(np.median(e[m])))
                    ys.append(np.log(mad))
        if len(xs) >= 3:
            g, a = np.polyfit(xs, ys, 1)
            g = float(np.clip(g, 0.0, 1.0))
            a = float(np.mean(ys) - g * np.mean(xs))
            sig = np.exp(a) * e ** g
            return np.maximum(sig, 0.5 * glob)
    return np.full(n, glob)


def _anomaly_scan(y: np.ndarray, period: int, alpha: float, z_floor: float):
    """Return dict(expected, resid, sigma, z, zcrit, method)."""
    exp, how = _expected(y, period)
    ok = np.isfinite(exp)
    resid = np.where(ok, y - exp, 0.0)
    sig = _hetero_sigma(resid[ok], exp[ok]) if ok.sum() >= 8 else np.full(ok.sum(), 1e-9)
    sigma = np.full(len(y), np.nan)
    sigma[ok] = sig
    z = np.where(ok, resid / sigma, 0.0)
    n = int(ok.sum())
    zcrit = max(z_floor, float(stats.norm.isf(alpha / (2 * max(n, 1)))))
    # MAD scale is noisy in short series: widen a little
    zcrit *= 1.0 + 1.5 / math.sqrt(max(n, 1))
    return dict(expected=exp, resid=resid, sigma=sigma, z=z, zcrit=zcrit, method=how, n=n)


# ============================================================================ anomalies + attribution
def _share_baseline(piv: pd.DataFrame) -> pd.DataFrame:
    """Typical share of each segment per day (rolling median over ~8 weeks), rows renormalised to sum to 1."""
    tot = piv.sum(axis=1).replace(0, np.nan)
    share = piv.div(tot, axis=0)
    w = min(57, _next_odd(max(7, len(piv) // 2)))
    base = share.rolling(w, center=True, min_periods=5).median()
    base = base.fillna(share.median())
    s = base.sum(axis=1).replace(0, np.nan)
    return base.div(s, axis=0).fillna(1.0 / max(1, piv.shape[1]))


def _attribute(day, obs_total, exp_total, pivs):
    """Split (obs_total - exp_total) exactly across the segments of each dimension. Returns best-dimension dict + all."""
    dev_total = obs_total - exp_total
    per_dim = {}
    for dim, (piv, base, sig) in pivs.items():
        if day not in piv.index:
            continue
        obs = piv.loc[day]
        b = base.loc[day]
        exp_seg = exp_total * b
        dev = obs - exp_seg
        rows = []
        for seg in piv.columns:
            s = sig.get(seg, np.nan)
            rows.append({"segment": str(seg), "observed": float(obs[seg]), "expected": float(exp_seg[seg]), "deviation": float(dev[seg]),
                         "share_of_deviation": float(dev[seg] / dev_total) if dev_total != 0 else None,
                         "baseline_share": float(b[seg]), "z": float(dev[seg] / s) if np.isfinite(s) and s > 0 else None})
        sign = 1.0 if dev_total >= 0 else -1.0
        rows.sort(key=lambda r: -sign * r["deviation"])
        resid_prop = float(np.sum(np.abs(dev.to_numpy() - dev_total * b.to_numpy())))
        disproportion = resid_prop / (2 * abs(dev_total)) if dev_total != 0 else None
        top = rows[0]
        per_dim[dim] = {"dimension": dim, "top": rows[:3], "sum_of_segment_deviations": float(dev.sum()), "total_deviation": float(dev_total),
                        "disproportion": _f(disproportion),
                        "broad_based": bool(disproportion is not None and disproportion <= 0.2),
                        "top_share": top["share_of_deviation"], "top_z": top["z"]}
    if not per_dim:
        return None
    # best dimension: the one whose top segment explains the most of the deviation and stands out against its own history
    def score(v):
        t = v["top"][0]
        return (v["top_share"] or 0.0) * (1.0 if (t["z"] or 0) >= 3 else 0.5)
    best = max(per_dim.values(), key=score)
    return {"best": best, "all_dimensions": per_dim}


def _anomaly_item(day, unit_word, metric, obs, exp, z, zcrit, how, attr, scope="total", segment=None, agg="sum", dim=None):
    dev = obs - exp
    rel = dev / exp * 100 if exp else None
    up = dev > 0
    wd = DOW[pd.Timestamp(day).dayofweek] if unit_word == "day" else None
    where = f" for {segment}" if segment else ""
    when = f"{_d(day)}" + (f" ({wd})" if wd else "")
    exp_phrase = f"about {_num(exp)} expected" + (f" for a {wd}" if wd else "")
    detail = (f"{metric}{where} was {_num(obs)} on {when} against {exp_phrase}: {_pct(rel)} ({'+' if up else ''}{_num(dev)}). "
              f"That is {abs(z):.1f} typical deviations from normal, well past the {zcrit:.1f} needed to rule out chance.")
    cause = None
    if attr and scope == "total":
        b = attr["best"]
        t = b["top"][0]
        if b["broad_based"]:
            detail += (f" The change was spread across {b['dimension']} roughly in proportion to normal, so no single {b['dimension']} caused it "
                       f"(the largest, {t['segment']}, contributed {_pct((t['share_of_deviation'] or 0) * 100)} of the gap).")
            cause = {"type": "broad", "dimension": b["dimension"]}
        elif t["share_of_deviation"] is not None and t["share_of_deviation"] >= 0.5 and (t["z"] or 0) >= 3:
            detail += (f" {t['segment']} ({b['dimension']}) accounts for {t['share_of_deviation'] * 100:.0f}% of the gap: "
                       f"{_num(t['observed'])} vs {_num(t['expected'])} expected.")
            cause = {"type": "segment", "dimension": b["dimension"], "segment": t["segment"]}
        else:
            detail += f" No single {b['dimension']} clearly explains it (largest contributor: {t['segment']}, {_pct((t['share_of_deviation'] or 0) * 100)} of the gap)."
            cause = {"type": "unclear", "dimension": b["dimension"]}
    sev = "info" if up else "warn"
    title = f"Unusual {unit_word}{where}: {_d(day)} ({_pct(rel)} vs expected)"
    action = ("Check whether this was a real event (a campaign, a bulk order, a big donor) and whether it can be repeated, or a data-entry error."
              if up else "Check for an outage, stock-out, closure or missing data entry that day, and recover anything that was lost.")
    ev = {"date": pd.Timestamp(day).strftime("%Y-%m-%d"), "observed": float(obs), "expected": float(exp), "deviation": float(dev),
          "deviation_pct": _f(rel), "z": float(z), "z_threshold": float(zcrit), "method": how, "scope": scope, "segment": segment,
          "attribution": attr["best"] if attr else None, "attribution_all_dimensions": attr["all_dimensions"] if attr else None, "cause": cause}
    return _item("anomaly", sev, title, detail, action, ev)


def detect_anomalies(df, date_col, metric_col, dims=None, *, agg=None, freq="auto", alpha=0.02, min_rel=0.10,
                     max_items=5, segment_pass=True, max_segments=6):
    """Find unusual days (or weeks/months) after removing the weekly cycle and slow trend, and say which segment drove each.

    alpha     family-wise false-alarm budget across all points tested (Bonferroni on a robust z-score).
    min_rel   ignore statistically odd points that differ from normal by less than this fraction (not business-relevant).
    """
    try:
        return _detect_anomalies(df, date_col, metric_col, dims, agg, freq, alpha, min_rel, max_items, segment_pass, max_segments)
    except Exception:
        return []


def _detect_anomalies(df, date_col, metric_col, dims, agg, freq, alpha, min_rel, max_items, segment_pass, max_segments):
    d = _prep(df, date_col, metric_col)
    if d is None:
        return []
    agg = agg or _agg_for(metric_col)
    res = _resolution(d["_t"].dt.normalize()) if freq == "auto" else freq
    if res == "D":
        key, rule, period, unit = d["_t"].dt.normalize(), "D", 7, "day"
    elif res == "W":
        key, rule, period, unit = d["_t"].dt.to_period("W-SUN").dt.start_time, "W-MON", 52, "week"
    else:
        key, rule, period, unit = d["_t"].dt.to_period("M").dt.start_time, "MS", 12, "month"
    s = getattr(d.groupby(key)["_v"], agg)()
    full = pd.date_range(s.index.min(), s.index.max(), freq=rule)
    s = s.reindex(full)
    s = s.fillna(0.0) if agg == "sum" else s.interpolate(limit_area="inside")
    s = s.dropna()
    min_n = {"D": 21, "W": 12, "M": 12}[res]
    if len(s) < min_n:
        return []
    y = s.to_numpy(float)
    per = period if (res == "D" or len(y) >= 2 * period) else 1
    sc = _anomaly_scan(y, per, alpha, z_floor=3.5 if res == "D" else 4.0)
    flag = (np.abs(sc["z"]) > sc["zcrit"]) & (np.abs(sc["resid"]) >= min_rel * np.maximum(np.abs(sc["expected"]), 1e-9))
    idx = np.where(flag)[0]
    idx = idx[np.argsort(-np.abs(sc["z"][idx]))][:max_items]

    dimlist = _valid_dims(df, dims) if agg == "sum" else []
    pivs = {}
    if dimlist and idx.size or (dimlist and segment_pass):
        dd = pd.DataFrame({"_k": key, "_v": d["_v"]})
        for c in dimlist:
            seg = _seg_series(df, c).loc[d.index]
            piv = dd.assign(_s=seg.values).groupby(["_k", "_s"])["_v"].sum().unstack(fill_value=0.0).reindex(s.index, fill_value=0.0)
            base = _share_baseline(piv)
            dev = piv - sc["expected"][:, None] * base.to_numpy()
            sig = {k: (1.4826 * float(np.median(np.abs(dev[k] - np.median(dev[k]))))) for k in piv.columns}
            pivs[c] = (piv, base, sig)

    out = []
    flagged_days = set()
    for i in idx:
        day = s.index[i]
        attr = _attribute(day, float(y[i]), float(sc["expected"][i]), pivs) if pivs else None
        out.append(_anomaly_item(day, unit, metric_col, y[i], sc["expected"][i], sc["z"][i], sc["zcrit"], sc["method"], attr, agg=agg))
        flagged_days.add(day)

    # segment-level pass: a big move in one small segment can be invisible in the total
    if segment_pass and pivs and res == "D":
        tested = 0
        cand = []
        for dim, (piv, base, sig) in pivs.items():
            tot_by = piv.sum().sort_values(ascending=False)
            for seg in tot_by.index[:max_segments]:
                if tot_by[seg] <= 0 or tot_by[seg] / max(tot_by.sum(), 1e-9) < 0.03:
                    continue
                ys = piv[seg].to_numpy(float)
                sc2 = _anomaly_scan(ys, 7, alpha, z_floor=3.5)
                cand.append((dim, seg, ys, sc2))
                tested += sc2["n"]
        if cand:
            ntest = max(tested, 1)
            zc = max(4.0, float(stats.norm.isf(alpha / (2 * ntest)))) * (1.0 + 1.5 / math.sqrt(max(len(s), 1)))
            seg_items = []
            for dim, seg, ys, sc2 in cand:
                f2 = (np.abs(sc2["z"]) > zc) & (np.abs(sc2["resid"]) >= max(min_rel, 0.25) * np.maximum(np.abs(sc2["expected"]), 1e-9))
                for j in np.where(f2)[0]:
                    day = s.index[j]
                    if day in flagged_days:
                        continue
                    seg_items.append((abs(sc2["z"][j]), _anomaly_item(day, unit, metric_col, ys[j], sc2["expected"][j], sc2["z"][j], zc, sc2["method"],
                                                                        None, scope="segment", segment=f"{seg} ({dim})", dim=dim)))
            seg_items.sort(key=lambda t: -t[0])
            seen = set()
            for _, it in seg_items:
                k = (it["evidence"]["date"])
                if k in seen:
                    continue
                seen.add(k)
                out.append(it)
                if len(out) >= max_items:
                    break
    return out[:max_items]


# ============================================================================ variance bridge (exact)
def _period_bounds(d, mode, period_a, period_b):
    """Return ((a0,a1),(b0,b1),label_a,label_b,note). Bounds inclusive dates (Timestamps, normalised)."""
    t = d["_t"].dt.normalize()
    lo, hi = t.min(), t.max()
    span = (hi - lo).days
    if mode == "explicit" and period_a is not None and period_b is not None:
        a0, a1 = pd.Timestamp(period_a[0]).normalize(), pd.Timestamp(period_a[1]).normalize()
        b0, b1 = pd.Timestamp(period_b[0]).normalize(), pd.Timestamp(period_b[1]).normalize()
        return (a0, a1), (b0, b1), f"{_d(a0)}-{_d(a1)}", f"{_d(b0)}-{_d(b1)}", None
    if mode == "thirds":
        k = max(1, (span + 1) // 3)
        a0, a1 = lo, lo + pd.Timedelta(days=k - 1)
        b1 = hi
        b0 = hi - pd.Timedelta(days=k - 1)
        return (a0, a1), (b0, b1), "first third", "last third", None
    # last_vs_prev, resolution aware (same cut-offs as analytics.period_series)
    freq = "M" if span > 180 else "W" if span > 45 else "D"
    if freq == "M":
        last_end = (hi.to_period("M").end_time.normalize())
        note = None
        if (last_end - hi).days > 2:   # last month incomplete: step back one month
            last_end = (hi.to_period("M") - 1).end_time.normalize()
            note = f"The latest month ({hi.strftime('%b %Y')}) is incomplete and was skipped."
        pm = last_end.to_period("M")
        b0, b1 = pm.start_time.normalize(), last_end
        a0, a1 = (pm - 1).start_time.normalize(), (pm - 1).end_time.normalize()
        return (a0, a1), (b0, b1), a0.strftime("%b %Y"), b0.strftime("%b %Y"), note
    if freq == "W":
        pw = hi.to_period("W-SUN")
        note = None
        if (pw.end_time.normalize() - hi).days > 0:
            pw = pw - 1
            note = "The latest week is incomplete and was skipped."
        b0, b1 = pw.start_time.normalize(), pw.end_time.normalize()
        a0, a1 = (pw - 1).start_time.normalize(), (pw - 1).end_time.normalize()
        return (a0, a1), (b0, b1), f"week of {_d(a0)}", f"week of {_d(b0)}", note
    b1 = hi
    b0 = hi - pd.Timedelta(days=6)
    a1 = b0 - pd.Timedelta(days=1)
    a0 = a1 - pd.Timedelta(days=6)
    return (a0, a1), (b0, b1), f"{_d(a0)}-{_d(a1)}", f"{_d(b0)}-{_d(b1)}", None


def decompose_change(df_a, df_b, metric_col, dim, *, agg=None, qty_col=None, price_col=None):
    """Exact additive decomposition of total_B - total_A by segments of `dim`.

    sum metrics : contribution_s = B_s - A_s  (segments only in B are 'new', only in A are 'lost').
    mean metrics: contribution_s = w_B,s * r_B,s - w_A,s * r_A,s  with w = share of rows, r = segment mean.
    If qty_col and price_col are given and metric ~= qty*price (sum metrics), also returns the price/volume/mix split
    per segment:  volume_s = (Q_B - Q_A) * P_A ; price_s = Q_B * (P_B - P_A)  (P = realised average price = revenue / qty).
    """
    agg = agg or _agg_for(metric_col)
    sa = _seg_series(df_a, dim)
    sb = _seg_series(df_b, dim)
    if agg == "sum":
        A = df_a.groupby(sa.values)[metric_col].sum()
        B = df_b.groupby(sb.values)[metric_col].sum()
        segs = sorted(set(A.index) | set(B.index))
        A, B = A.reindex(segs).fillna(0.0), B.reindex(segs).fillna(0.0)
        total_a, total_b = float(A.sum()), float(B.sum())
        delta = total_b - total_a
        rows = []
        for sgm in segs:
            a, b = float(A[sgm]), float(B[sgm])
            status = "new" if (a == 0 and b != 0) else "lost" if (b == 0 and a != 0) else "continuing"
            rows.append({"segment": sgm, "a": a, "b": b, "contribution": b - a, "status": status,
                         "share_of_change": (b - a) / delta if delta != 0 else None})
    else:
        na, nb = len(df_a), len(df_b)
        ga = df_a.groupby(sa.values)[metric_col].agg(["mean", "size"])
        gb = df_b.groupby(sb.values)[metric_col].agg(["mean", "size"])
        segs = sorted(set(ga.index) | set(gb.index))
        total_a, total_b = float(df_a[metric_col].mean()), float(df_b[metric_col].mean())
        delta = total_b - total_a
        rows = []
        for sgm in segs:
            wa = ga["size"].get(sgm, 0) / na if na else 0.0
            wb = gb["size"].get(sgm, 0) / nb if nb else 0.0
            ra = float(ga["mean"].get(sgm, 0.0)) if sgm in ga.index else 0.0
            rb = float(gb["mean"].get(sgm, 0.0)) if sgm in gb.index else 0.0
            a, b = wa * ra, wb * rb
            status = "new" if wa == 0 else "lost" if wb == 0 else "continuing"
            rows.append({"segment": sgm, "a": a, "b": b, "contribution": b - a, "status": status, "weight_a": wa, "weight_b": wb,
                         "rate_a": ra, "rate_b": rb, "rate_effect": wb * (rb - ra) if status == "continuing" else 0.0,
                         "mix_effect": (b - a) - (wb * (rb - ra) if status == "continuing" else 0.0),
                         "share_of_change": (b - a) / delta if delta != 0 else None})
    rows.sort(key=lambda r: -abs(r["contribution"]))
    tot = float(math.fsum(r["contribution"] for r in rows))
    check = {"sum_of_contributions": tot, "total_change": float(delta), "abs_error": float(abs(tot - delta)),
             "exact": bool(abs(tot - delta) <= 1e-9 * max(1.0, abs(total_a), abs(total_b)))}
    out = {"dimension": dim, "agg": agg, "total_a": total_a, "total_b": total_b, "delta": float(delta),
           "delta_pct": _f(delta / abs(total_a) * 100) if total_a else None, "contributions": rows, "check": check, "pvm": None}

    if agg == "sum" and qty_col and price_col and qty_col in df_a.columns:
        out["pvm"] = _pvm(df_a, df_b, metric_col, dim, qty_col)
    return out


def _qp_consistent(df, metric_col, qty_col, price_col, tol=0.02):
    """True if metric ~= qty * price on (almost) all rows."""
    try:
        x = pd.DataFrame({"m": pd.to_numeric(df[metric_col], errors="coerce"), "q": pd.to_numeric(df[qty_col], errors="coerce"),
                          "p": pd.to_numeric(df[price_col], errors="coerce")}).dropna()
        x = x[x.m.abs() > 0]
        if len(x) < 10:
            return False
        rel = ((x.q * x.p - x.m).abs() / x.m.abs())
        return bool(rel.median() <= tol and (rel <= 0.05).mean() >= 0.9)
    except Exception:
        return False


def _pvm(df_a, df_b, metric_col, dim, qty_col):
    """Price / volume / mix / new / lost, exact. Segment price = revenue / quantity (realised average price)."""
    sa, sb = _seg_series(df_a, dim), _seg_series(df_b, dim)
    RA, RB = df_a.groupby(sa.values)[metric_col].sum(), df_b.groupby(sb.values)[metric_col].sum()
    QA, QB = df_a.groupby(sa.values)[qty_col].sum(), df_b.groupby(sb.values)[qty_col].sum()
    segs = sorted(set(RA.index) | set(RB.index))
    RA, RB, QA, QB = (x.reindex(segs).fillna(0.0) for x in (RA, RB, QA, QB))
    cont = [s for s in segs if QA[s] > 0 and QB[s] > 0]
    new = [s for s in segs if QA[s] <= 0 and (QB[s] > 0 or RB[s] != 0)]
    lost = [s for s in segs if QB[s] <= 0 and (QA[s] > 0 or RA[s] != 0) and s not in new]
    PA = {s: RA[s] / QA[s] for s in cont}
    PB = {s: RB[s] / QB[s] for s in cont}
    qa_c, qb_c = float(sum(QA[s] for s in cont)), float(sum(QB[s] for s in cont))
    ra_c = float(sum(RA[s] for s in cont))
    pbar_a = ra_c / qa_c if qa_c else 0.0
    volume = (qb_c - qa_c) * pbar_a                                   # more/fewer units at last period's average price
    mix = float(sum((QB[s] - QA[s]) * PA[s] for s in cont)) - volume    # shift between cheaper/dearer segments
    price = float(sum(QB[s] * (PB[s] - PA[s]) for s in cont))          # same segment, different realised price
    new_v = float(sum(RB[s] - RA[s] for s in new))
    lost_v = float(sum(RB[s] - RA[s] for s in lost))
    delta = float(RB.sum() - RA.sum())
    comp = {"volume": float(volume), "mix": float(mix), "price": float(price), "new_segments": new_v, "lost_segments": lost_v}
    tot = float(math.fsum(comp.values()))
    per_seg = []
    for s in cont:
        per_seg.append({"segment": s, "quantity_a": float(QA[s]), "quantity_b": float(QB[s]), "price_a": float(PA[s]), "price_b": float(PB[s]),
                        "volume_effect": float((QB[s] - QA[s]) * PA[s]), "price_effect": float(QB[s] * (PB[s] - PA[s])),
                        "total": float(RB[s] - RA[s])})
    per_seg.sort(key=lambda r: -abs(r["price_effect"]))
    return {"components": comp, "per_segment": per_seg, "new": new, "lost": lost, "total_change": delta,
            "check": {"sum_of_components": tot, "total_change": delta, "abs_error": abs(tot - delta),
                      "exact": bool(abs(tot - delta) <= 1e-9 * max(1.0, abs(RA.sum()), abs(RB.sum())))}}


def _daily_adjusted(d, a, b):
    """Daily totals for both windows with the day-of-week effect removed, for an honest noise test."""
    t = d["_t"].dt.normalize()
    daily = d.groupby(t)["_v"].sum()
    full = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full, fill_value=0.0)
    dow = daily.groupby(daily.index.dayofweek).transform("mean")
    adj = daily / (dow / dow.mean()).replace(0, np.nan)
    xa = adj[(adj.index >= a[0]) & (adj.index <= a[1])].dropna()
    xb = adj[(adj.index >= b[0]) & (adj.index <= b[1])].dropna()
    return xa.to_numpy(), xb.to_numpy()


def variance_bridge(df, date_col, metric_col, dims, period_a=None, period_b=None, *, mode="auto", agg=None, qty_col=None, price_col=None,
                    top_n=3, min_rel=0.05, p_value=0.05, force=False):
    """Explain why the total moved between two periods, as exact additive contributions by segment.

    mode: "auto"/"last_vs_prev" (last complete month/week vs the one before), "thirds" (last third vs first third of the
    date range), or "explicit" with period_a / period_b = (start, end). Returns one finding (or None if the change is
    within normal noise and `force` is False); evidence holds the full ranked contributions for every dimension and an
    exactness check (sum of contributions == total change).
    """
    try:
        return _variance_bridge(df, date_col, metric_col, dims, period_a, period_b, mode, agg, qty_col, price_col, top_n, min_rel, p_value, force)
    except Exception:
        return None


def _variance_bridge(df, date_col, metric_col, dims, period_a, period_b, mode, agg, qty_col, price_col, top_n, min_rel, p_value, force):
    d = _prep(df, date_col, metric_col)
    if d is None:
        return None
    agg = agg or _agg_for(metric_col)
    md = "explicit" if (period_a is not None and period_b is not None) else ("thirds" if mode == "thirds" else "last_vs_prev")
    (a0, a1), (b0, b1), la, lb, note = _period_bounds(d, md, period_a, period_b)
    t = d["_t"].dt.normalize()
    ma, mb = (t >= a0) & (t <= a1), (t >= b0) & (t <= b1)
    if ma.sum() < 3 or mb.sum() < 3:
        return None
    dfa, dfb = df.loc[d.index[ma.values]], df.loc[d.index[mb.values]]
    dfa = dfa.assign(**{metric_col: pd.to_numeric(dfa[metric_col], errors="coerce")}).dropna(subset=[metric_col])
    dfb = dfb.assign(**{metric_col: pd.to_numeric(dfb[metric_col], errors="coerce")}).dropna(subset=[metric_col])
    days_a, days_b = int((a1 - a0).days + 1), int((b1 - b0).days + 1)
    dimlist = _valid_dims(df, dims)
    use_pvm = bool(agg == "sum" and qty_col and price_col and qty_col in df.columns and price_col in df.columns
                   and _qp_consistent(df, metric_col, qty_col, price_col))

    results = {}
    for c in dimlist:
        results[c] = decompose_change(dfa, dfb, metric_col, c, agg=agg, qty_col=qty_col if use_pvm else None, price_col=price_col if use_pvm else None)
    # total-level result even without dims
    if not results:
        tot_a = float(dfa[metric_col].sum() if agg == "sum" else dfa[metric_col].mean())
        tot_b = float(dfb[metric_col].sum() if agg == "sum" else dfb[metric_col].mean())
        base = {"total_a": tot_a, "total_b": tot_b, "delta": tot_b - tot_a, "delta_pct": _f((tot_b - tot_a) / abs(tot_a) * 100) if tot_a else None}
    else:
        r0 = next(iter(results.values()))
        base = {k: r0[k] for k in ("total_a", "total_b", "delta", "delta_pct")}
    delta, tot_a = base["delta"], base["total_a"]
    rel = delta / abs(tot_a) if tot_a else None

    # is the change bigger than day-to-day noise?  (Welch t-test on day-of-week-adjusted daily totals; sum metrics only)
    pval = None
    if agg == "sum":
        try:
            xa, xb = _daily_adjusted(d, (a0, a1), (b0, b1))
            if len(xa) >= 5 and len(xb) >= 5:
                pval = float(stats.ttest_ind(xb, xa, equal_var=False).pvalue)
        except Exception:
            pval = None
    significant = (pval is None or pval < p_value) and rel is not None and abs(rel) >= min_rel
    if not significant and not force:
        return None

    # pick the dimension whose top segment explains the largest part of the movement
    best_dim = None
    if results:
        def conc(r):
            c = [abs(x["contribution"]) for x in r["contributions"]]
            return (c[0] / sum(c)) if c and sum(c) > 0 else 0.0
        best_dim = max(results, key=lambda k: conc(results[k]))
    word = "up" if delta > 0 else "down"
    sev = "good" if delta > 0 else "warn"
    title = f"{metric_col} is {word} {abs(rel) * 100:.0f}% ({lb} vs {la})" if rel is not None else f"{metric_col} changed between {la} and {lb}"
    detail = (f"{'Total' if agg == 'sum' else 'Average'} {metric_col} went from {_num(base['total_a'])} ({la}) to {_num(base['total_b'])} ({lb}): "
              f"{'+' if delta >= 0 else ''}{_num(delta)}.")
    if days_a != days_b:
        detail += f" Note the periods have different lengths ({days_a} vs {days_b} days)."
    if note:
        detail += " " + note
    if best_dim:
        r = results[best_dim]
        parts = []
        for x in r["contributions"][:top_n]:
            lab = {"new": " (new)", "lost": " (no longer present)"}.get(x["status"], "")
            sh = f", {abs(x['share_of_change']) * 100:.0f}% of the net change" if x["share_of_change"] is not None else ""
            parts.append(f"{x['segment']}{lab} {'+' if x['contribution'] >= 0 else ''}{_num(x['contribution'])}{sh}")
        detail += f" By {best_dim}: " + "; ".join(parts) + "."
        opp = [x for x in r["contributions"] if x["contribution"] * delta < 0]
        if opp:
            detail += f" Partly offset by {opp[0]['segment']} ({'+' if opp[0]['contribution'] >= 0 else ''}{_num(opp[0]['contribution'])})."
        if r["pvm"]:
            c = r["pvm"]["components"]
            detail += (f" Price vs volume: volume {'+' if c['volume'] >= 0 else ''}{_num(c['volume'])}, price {'+' if c['price'] >= 0 else ''}{_num(c['price'])}, "
                       f"mix {'+' if c['mix'] >= 0 else ''}{_num(c['mix'])}, new/lost products {'+' if c['new_segments'] + c['lost_segments'] >= 0 else ''}{_num(c['new_segments'] + c['lost_segments'])}.")
    top_seg = results[best_dim]["contributions"][0]["segment"] if best_dim else None
    action = (f"Start with {top_seg}: confirm whether the change is intended, and if it is a loss, fix that first." if delta < 0 and top_seg
              else f"Find out why {top_seg} moved and repeat or protect it." if top_seg else "Compare the two periods for what changed (price, volume, new items).")
    ev = {"metric": metric_col, "agg": agg, "mode": md, "period_a": {"label": la, "start": a0.strftime("%Y-%m-%d"), "end": a1.strftime("%Y-%m-%d"), "days": days_a, "rows": int(len(dfa))},
          "period_b": {"label": lb, "start": b0.strftime("%Y-%m-%d"), "end": b1.strftime("%Y-%m-%d"), "days": days_b, "rows": int(len(dfb))},
          **base, "p_value_vs_daily_noise": _f(pval), "best_dimension": best_dim, "by_dimension": results, "note": note,
          "price_volume_used": bool(use_pvm)}
    return _item("bridge", sev, title, detail, action, ev)


# ============================================================================ change points
_CRIT_CACHE: dict = {}


def _crit_value(n, min_seg, level=0.99, sims=400):
    """Monte-Carlo critical value for max|t| over split points under iid Gaussian noise (seeded, cached)."""
    bucket = int(round(2 ** (round(math.log2(max(n, 8)) * 4) / 4)))
    key = (bucket, min_seg, level)
    if key in _CRIT_CACHE:
        return _CRIT_CACHE[key]
    rng = np.random.default_rng(12345)
    n_ = bucket
    ks = np.arange(min_seg, n_ - min_seg + 1)
    if len(ks) == 0:
        _CRIT_CACHE[key] = np.inf
        return np.inf
    x = rng.standard_normal((sims, n_))
    cs = np.cumsum(x, axis=1)
    tot = cs[:, -1][:, None]
    left = cs[:, ks - 1] / ks
    right = (tot - cs[:, ks - 1]) / (n_ - ks)
    t = np.abs(left - right) / np.sqrt(1.0 / ks + 1.0 / (n_ - ks))
    v = float(np.quantile(t.max(axis=1), level))
    _CRIT_CACHE[key] = v
    return v


def _scan_split(x, min_seg):
    n = len(x)
    ks = np.arange(min_seg, n - min_seg + 1)
    if len(ks) == 0:
        return None
    cs = np.cumsum(x)
    tot = cs[-1]
    left = cs[ks - 1] / ks
    right = (tot - cs[ks - 1]) / (n - ks)
    stat = np.abs(left - right) / np.sqrt(1.0 / ks + 1.0 / (n - ks))
    j = int(np.argmax(stat))
    return int(ks[j]), float(stat[j]), float(left[j]), float(right[j])


def _noise_sigma(x, k):
    """Long-run noise sd of x around a two-level mean split at k: diff-based sd, corrected for lag-1 autocorrelation."""
    r = np.concatenate([x[:k] - x[:k].mean(), x[k:] - x[k:].mean()])
    dx = np.diff(r)
    sd_d = 1.4826 * np.median(np.abs(dx - np.median(dx))) / math.sqrt(2) if len(dx) > 3 else 0.0
    if sd_d <= 0:
        sd_d = float(np.std(dx)) / math.sqrt(2) if len(dx) > 1 else 0.0
    if len(r) > 5 and np.std(r) > 0:
        rho = float(np.corrcoef(r[:-1], r[1:])[0, 1])
        rho = 0.0 if not np.isfinite(rho) else float(np.clip(rho, 0.0, 0.7))
    else:
        rho = 0.0
    return sd_d * math.sqrt(1 + rho) / (1 - rho), rho


def detect_change_points(y, *, min_seg=None, min_rel=0.10, level=0.99, max_cp=3, season=None):
    """Binary-segmentation level-shift detector with guards against false alarms.

    y: pd.Series (DatetimeIndex) or array. season: seasonal period removed first (e.g. 7 for daily); None = none.
    A split is reported only if (1) its t-statistic beats a Monte-Carlo critical value for the max over all split points,
    computed with a long-run (autocorrelation-aware) noise estimate; (2) the level changes by >= min_rel (relative);
    (3) a two-level step explains the data clearly better than a straight trend line (BIC gap); (4) both sides have >= min_seg points.
    Returns list of {index, date, before_mean, after_mean, change_pct, t_stat, critical_value, n_before, n_after}, in time order.
    """
    try:
        return _change_points(y, min_seg, min_rel, level, max_cp, season)
    except Exception:
        return []


def _change_points(y, min_seg, min_rel, level, max_cp, season):
    idx = y.index if isinstance(y, pd.Series) else None
    x = np.asarray(y, dtype=float)
    ok = np.isfinite(x)
    if ok.sum() < 12:
        return []
    x = np.where(ok, x, np.nanmedian(x))
    n = len(x)
    xs = x.copy()
    if season and season > 1 and n >= 4 * season:
        from statsmodels.tsa.seasonal import STL
        res = STL(pd.Series(x), period=season, robust=True, seasonal=7).fit()
        xs = x - np.asarray(res.seasonal)
    min_seg = min_seg or max(5, min(14, n // 8))
    found = []

    def rec(lo, hi, depth):
        seg = xs[lo:hi]
        m = len(seg)
        if depth >= max_cp or m < 2 * min_seg:
            return
        sp = _scan_split(seg, min_seg)
        if sp is None:
            return
        k, stat, ml, mr = sp
        sig, rho = _noise_sigma(seg, k)
        if sig <= 0:
            return
        tstat = stat / sig
        crit = _crit_value(m, min_seg, level)
        base = abs(ml) if abs(ml) > 1e-9 else 1e-9
        rel = (mr - ml) / base
        if tstat < crit or abs(rel) < min_rel:
            return
        # step vs straight-line trend (BIC)
        t_ = np.arange(m, dtype=float)
        coef = np.polyfit(t_, seg, 1)
        sse_lin = float(np.sum((seg - np.polyval(coef, t_)) ** 2))
        sse_step = float(np.sum((seg[:k] - seg[:k].mean()) ** 2) + np.sum((seg[k:] - seg[k:].mean()) ** 2))
        if sse_step <= 0 or sse_lin <= 0:
            pass
        else:
            bic_gain = m * math.log(sse_lin / sse_step) - 2 * math.log(m)   # step has one more free parameter
            if bic_gain < 10:
                return
        found.append({"index": lo + k, "before_mean": float(ml), "after_mean": float(mr), "change_pct": float(rel * 100), "t_stat": float(tstat),
                      "critical_value": float(crit), "rho": float(rho), "lo": lo, "hi": hi})
        rec(lo, lo + k, depth + 1)
        rec(lo + k, hi, depth + 1)

    rec(0, n, 0)
    found.sort(key=lambda r: r["index"])
    out = []
    bounds = [0] + [f["index"] for f in found] + [n]
    for i, f in enumerate(found):
        left = xs[bounds[i]:f["index"]]
        right = xs[f["index"]:bounds[i + 2]]
        f = dict(f)
        f["before_mean"], f["after_mean"] = float(left.mean()), float(right.mean())
        f["change_pct"] = float((f["after_mean"] - f["before_mean"]) / abs(f["before_mean"]) * 100) if f["before_mean"] else None
        f["n_before"], f["n_after"] = int(len(left)), int(len(right))
        f["date"] = pd.Timestamp(idx[f["index"]]).strftime("%Y-%m-%d") if idx is not None else None
        f.pop("lo", None)
        f.pop("hi", None)
        out.append(f)
    return out


def _changepoint_items(df, date_col, metric_col, dims, agg, qty_col, price_col, max_items=2):
    d = _prep(df, date_col, metric_col)
    if d is None:
        return []
    agg = agg or _agg_for(metric_col)
    res = _resolution(d["_t"].dt.normalize())
    if res == "D":
        key, rule, season, unit = d["_t"].dt.normalize(), "D", 7, "day"
    elif res == "W":
        key, rule, season, unit = d["_t"].dt.to_period("W-SUN").dt.start_time, "W-MON", None, "week"
    else:
        key, rule, season, unit = d["_t"].dt.to_period("M").dt.start_time, "MS", None, "month"
    s = getattr(d.groupby(key)["_v"], agg)()
    s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq=rule))
    s = s.fillna(0.0) if agg == "sum" else s.interpolate(limit_area="inside").dropna()
    cps = detect_change_points(s, season=season, min_seg={"D": 14, "W": 5, "M": 4}[res])
    cps = sorted(cps, key=lambda c: -abs(c["t_stat"] / max(c["critical_value"], 1e-9)))[:max_items]
    out = []
    for c in cps:
        up = c["after_mean"] > c["before_mean"]
        when = _d(c["date"])
        detail = (f"Average {unit}ly {metric_col} was {_num(c['before_mean'])} for the {c['n_before']} {unit}s before {when} and {_num(c['after_mean'])} "
                  f"for the {c['n_after']} {unit}s since: {_pct(c['change_pct'])}. This is a sustained step, not a one-off spike "
                  f"(test statistic {c['t_stat']:.1f} vs {c['critical_value']:.1f} needed to rule out chance).")
        ev = dict(c)
        # name the segment behind it using equal windows either side
        try:
            w = min(c["n_before"], c["n_after"])
            i = c["index"]
            t0 = s.index[max(0, i - w)]
            t1 = s.index[i]
            t2 = s.index[min(len(s) - 1, i + w - 1)]
            b = _variance_bridge(df, date_col, metric_col, dims, (t0, t1 - pd.Timedelta(days=1)), (t1, t2), "explicit", agg, qty_col, price_col, 3, 0.0, 1.0, True)
            if b and b["evidence"]["best_dimension"]:
                bd = b["evidence"]["best_dimension"]
                top = b["evidence"]["by_dimension"][bd]["contributions"][0]
                detail += f" Over equal windows either side, the biggest mover was {top['segment']} ({bd}): {'+' if top['contribution'] >= 0 else ''}{_num(top['contribution'])}."
                ev["top_segment"] = {"dimension": bd, **top}
        except Exception:
            pass
        out.append(_item("changepoint", "good" if up else "warn",
                         f"{metric_col} stepped {'up' if up else 'down'} {abs(c['change_pct']):.0f}% around {when}", detail,
                         "Find what changed around that date (price, campaign, channel, staffing, stock) and decide whether to keep or reverse it.", ev))
    return out


# ============================================================================ concentration / dependency
def concentration(df, metric_col, dims, *, min_segments=3, top1_flag=0.40, top3_flag=0.80, entity_col=None):
    """HHI and top-N share per dimension (sum metrics, non-negative totals). Flags heavy dependence on one segment."""
    try:
        agg = _agg_for(metric_col)
        if agg != "sum" or metric_col not in df.columns:
            return []
        out = []
        v = pd.to_numeric(df[metric_col], errors="coerce")
        for c in _valid_dims(df, dims, max_unique=10 ** 6) + ([entity_col] if entity_col and entity_col in df.columns else []):
            g = v.groupby(_seg_series(df, c).values).sum()
            g = g[g > 0].sort_values(ascending=False)
            tot = float(g.sum())
            if len(g) < min_segments or tot <= 0:
                continue
            sh = (g / tot).to_numpy()
            hhi = float(np.sum(sh ** 2))
            top1, top3 = float(sh[0]), float(sh[:3].sum())
            ent = c == entity_col
            ev = {"dimension": c, "segments": int(len(g)), "hhi": hhi, "effective_segments": 1 / hhi, "top1": str(g.index[0]), "top1_share": top1,
                  "top3_share": top3, "top3": [str(i) for i in g.index[:3]], "total": tot}
            if ent:
                k = max(1, int(math.ceil(0.1 * len(g))))
                ev["top_decile_share"] = float(sh[:k].sum())
                ev["top_decile_n"] = k
            if top1 >= top1_flag or (top3 >= top3_flag and len(g) >= 6) or (ent and ev["top_decile_share"] >= 0.7):
                if ent:
                    title = f"Top {ev['top_decile_n']} {c} values bring {ev['top_decile_share'] * 100:.0f}% of {metric_col}"
                    detail = (f"The top 10% of {c} ({ev['top_decile_n']} of {len(g)}) account for {ev['top_decile_share'] * 100:.0f}% of {metric_col}; "
                              f"the single largest is {ev['top1']} at {top1 * 100:.0f}%. Losing a few of them would be felt immediately.")
                    action = f"Know your top {c} values personally and track whether each is still active."
                else:
                    title = f"{g.index[0]} brings {top1 * 100:.0f}% of {metric_col} (by {c})"
                    detail = (f"Across {len(g)} {c} values, {g.index[0]} is {top1 * 100:.0f}% of total {metric_col} and the top 3 are {top3 * 100:.0f}% "
                              f"(concentration index HHI = {hhi:.2f}; equivalent to {1 / hhi:.1f} equally sized {c} values).")
                    action = f"Protect what makes {g.index[0]} work, and test whether other {c} values can grow so one is not carrying the business."
                out.append(_item("concentration", "warn" if top1 >= 0.6 else "info", title, detail, action, ev))
        return out
    except Exception:
        return []


# ============================================================================ entity (donor / customer) metrics
def entity_metrics(df, entity_col, date_col, metric_col=None, *, min_entities=10):
    """Repeat rate, month-to-month retention and a churn proxy for a donor/customer column. Modest by design."""
    try:
        return _entity_metrics(df, entity_col, date_col, metric_col, min_entities)
    except Exception:
        return []


def _entity_metrics(df, entity_col, date_col, metric_col, min_entities):
    if entity_col not in df.columns or date_col not in df.columns:
        return []
    t = pd.to_datetime(df[date_col], errors="coerce")
    e = df[entity_col].astype("string")
    v = pd.to_numeric(df[metric_col], errors="coerce") if metric_col and metric_col in df.columns else pd.Series(1.0, index=df.index)
    x = pd.DataFrame({"e": e, "t": t.dt.normalize(), "v": v}).dropna(subset=["e", "t"])
    n_ent = x["e"].nunique()
    if n_ent < min_entities or len(x) < 2 * min_entities:
        return []
    span = (x["t"].max() - x["t"].min()).days
    if span < 60:
        return []
    out = []
    days_per = x.groupby("e")["t"].nunique()
    repeat = float((days_per >= 2).mean())
    ev = {"entity_col": entity_col, "entities": int(n_ent), "repeat_rate": repeat, "single_visit_entities": int((days_per == 1).sum()),
          "median_active_days": float(days_per.median())}
    # monthly retention over the last up-to-3 complete transitions
    x["m"] = x["t"].dt.to_period("M")
    last_full = x["t"].max().to_period("M") if (x["t"].max().to_period("M").end_time.normalize() - x["t"].max()).days <= 2 else x["t"].max().to_period("M") - 1
    months = [last_full - i for i in range(4)][::-1]
    act = {m: set(x.loc[x.m == m, "e"]) for m in months}
    rets = []
    for m0, m1 in zip(months[:-1], months[1:]):
        if len(act[m0]) >= 5:
            rets.append({"from": str(m0), "to": str(m1), "active_prev": len(act[m0]), "retained": len(act[m0] & act[m1]),
                         "retention": len(act[m0] & act[m1]) / len(act[m0])})
    ev["monthly_retention"] = rets
    # churn proxy: active in the earlier window but silent in the recent one
    gaps = x.sort_values("t").groupby("e")["t"].apply(lambda s: s.diff().dt.days.dropna().median() if s.nunique() > 1 else np.nan).dropna()
    R = int(np.clip(2 * float(gaps.median()) if len(gaps) else 90, 30, 180))
    end = x["t"].max()
    recent = x[x["t"] > end - pd.Timedelta(days=R)]
    prior = x[(x["t"] <= end - pd.Timedelta(days=R)) & (x["t"] > end - pd.Timedelta(days=2 * R))]
    if prior["e"].nunique() >= 5:
        pr_set, rc_set = set(prior["e"]), set(recent["e"])
        lapsed = pr_set - rc_set
        churn = len(lapsed) / len(pr_set)
        lost_value = float(prior.loc[prior["e"].isin(lapsed), "v"].sum())
        tot_prior = float(prior["v"].sum())
        ev.update({"window_days": R, "prior_active": len(pr_set), "lapsed": len(lapsed), "churn_proxy": churn,
                   "value_of_lapsed_in_prior_window": lost_value, "prior_window_total": tot_prior})
        detail = (f"{repeat * 100:.0f}% of {n_ent} {entity_col} values appear on 2+ different days. Of the {len(pr_set)} active in the {R} days before "
                  f"{_d(end - pd.Timedelta(days=R))}, {len(lapsed)} ({churn * 100:.0f}%) did not appear in the last {R} days"
                  + (f", taking {lost_value / tot_prior * 100:.0f}% of that earlier window's {metric_col}" if tot_prior > 0 and metric_col else "") + ".")
        if rets:
            r = rets[-1]
            detail += f" Month-to-month retention {r['from']} to {r['to']}: {r['retention'] * 100:.0f}% ({r['retained']} of {r['active_prev']})."
        sev = "warn" if churn >= 0.5 else "info"
        out.append(_item("retention", sev, f"{churn * 100:.0f}% of recently active {entity_col} values have gone quiet", detail,
                         f"Reach out personally to the lapsed {entity_col} values, starting with the highest value ones.", ev))
    else:
        out.append(_item("retention", "info", f"{repeat * 100:.0f}% of {entity_col} values come back",
                         f"{repeat * 100:.0f}% of {n_ent} {entity_col} values appear on 2 or more different days; {ev['single_visit_entities']} appear once.",
                         "Follow up with one-time contacts while they still remember you.", ev))
    return out


# ============================================================================ orchestrator
def analyze(df, date_col=None, metric_col=None, dims=None, *, profile=None, qty_col="auto", price_col="auto", entity_col="auto", max_items=8):
    """Run every check and return findings ranked warn > good > info.  `profile` may be analytics.profile(df) output."""
    try:
        if profile:
            date_col = date_col or profile.get("date")
            metric_col = metric_col or profile.get("metric")
            dims = dims if dims is not None else profile.get("cat_cols")
        if not date_col or not metric_col:
            return []
        roles = infer_roles(df)
        qty = roles["qty_col"] if qty_col == "auto" else qty_col
        price = roles["price_col"] if price_col == "auto" else price_col
        ent = roles["entity_col"] if entity_col == "auto" else entity_col
        dims = [c for c in (dims or []) if c not in (ent,)]
        items = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            b = variance_bridge(df, date_col, metric_col, dims, qty_col=qty, price_col=price)
            if b:
                items.append(b)
            items += _changepoint_items(df, date_col, metric_col, dims, None, qty, price)
            items += detect_anomalies(df, date_col, metric_col, dims)
            items += concentration(df, metric_col, dims, entity_col=ent)
            if ent:
                items += entity_metrics(df, ent, date_col, metric_col)
        order = {"warn": 0, "good": 1, "info": 2}
        items.sort(key=lambda i: order.get(i["severity"], 3))
        return items[:max_items]
    except Exception:
        return []


# ============================================================================ false-positive study (used by tests / docs)
def false_positive_study(runs=500, days=365, seed=0, kinds=("gauss_dow", "poisson_orders", "trend_season")):
    """Count how often pure-noise data triggers each detector. Returns {kind: {anomaly_runs, changepoint_runs, bridge_runs, runs}}."""
    res = {}
    for kind in kinds:
        a = c = br = 0
        for r in range(runs):
            rng = np.random.default_rng([seed, r, sum(map(ord, kind))])
            df = _noise_frame(kind, days, rng)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                if detect_anomalies(df, "date", "amount", ["product", "region"], max_items=5):
                    a += 1
                if _changepoint_items(df, "date", "amount", ["product", "region"], None, None, None):
                    c += 1
                if variance_bridge(df, "date", "amount", ["product", "region"]) is not None:
                    br += 1
        res[kind] = {"runs": runs, "anomaly_runs": a, "changepoint_runs": c, "bridge_runs": br}
    return res


def _noise_frame(kind, days, rng):
    """Synthetic daily sales table with NO planted effect. Rows = day x product x region (aggregated)."""
    dates = pd.date_range("2024-01-01", periods=days, freq="D")
    prods = {"A": 0.40, "B": 0.25, "C": 0.20, "D": 0.10, "E": 0.05}
    regs = {"North": 0.5, "South": 0.3, "Online": 0.2}
    t = np.arange(days)
    dow = np.array([1.0, 0.95, 0.9, 1.0, 1.1, 1.4, 1.3])[dates.dayofweek]
    rows = []
    if kind == "gauss_dow":
        level = 1000 * dow
        for p, sp in prods.items():
            for g, sg in regs.items():
                mu = level * sp * sg
                v = np.maximum(mu * (1 + 0.15 * rng.standard_normal(days)), 0)
                rows.append(pd.DataFrame({"date": dates, "product": p, "region": g, "amount": v}))
    elif kind == "poisson_orders":
        lam = 12 * dow
        for p, sp in prods.items():
            for g, sg in regs.items():
                n = rng.poisson(lam * sp * sg)
                price = {"A": 900, "B": 250, "C": 120, "D": 300, "E": 60}[p]
                rows.append(pd.DataFrame({"date": dates, "product": p, "region": g, "amount": n * price * (1 + 0.1 * rng.standard_normal(days)).clip(0.3)}))
    else:  # trend_season
        level = 1000 * dow * (1 + 0.0015 * t) * (1 + 0.3 * np.sin(2 * np.pi * t / 365.25))
        for p, sp in prods.items():
            for g, sg in regs.items():
                mu = level * sp * sg
                v = np.maximum(mu * (1 + 0.12 * rng.standard_normal(days)), 0)
                rows.append(pd.DataFrame({"date": dates, "product": p, "region": g, "amount": v}))
    return pd.concat(rows, ignore_index=True)
