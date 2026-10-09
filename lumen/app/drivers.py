"""'What changed and why': exact contribution analysis and conservative daily anomaly detection. Pure pandas/numpy, no LLM.

Everything here is arithmetic that can be checked by hand:
  * bridge(): the change in a total between two equal windows is split into per-segment contributions that add up
    exactly to the change (checked and reported). With a quantity column it is also split into volume vs price effects.
  * daily_anomalies(): days far outside what the recent level and day-of-week pattern predict, with the segment that
    contributed most. The threshold is deliberately high; the false-positive rate on pure noise is measured in tests.
"""
import numpy as np, pandas as pd

QTY_HINT = ("qty", "quantity", "units", "unit_count", "count", "pieces", "items")
WINDOW = {"D": 7, "W": 4, "MS": 1, "YS": 1}
UNIT = {"D": "day", "W": "week", "MS": "month", "YS": "year"}
LABEL_FMT = {"D": "%d %b %Y", "W": "week ending %d %b %Y", "MS": "%b %Y", "YS": "%Y"}


def _fmt(x) -> str:
    x = float(x); a = abs(x)
    if a >= 1e7: return f"{x/1e6:,.1f}M"
    if a >= 1e5: return f"{x/1e3:,.0f}k"
    if a >= 1000: return f"{x:,.0f}"
    return f"{x:,.1f}" if a >= 1 else f"{x:.2g}"


def _windows(s: pd.Series, freq: str):
    """Last two equal windows of the (already partial-period-trimmed) series: (prev_idx, cur_idx)."""
    w = WINDOW[freq]
    if len(s) < 2 * w: return None
    return s.index[-2 * w:-w], s.index[-w:]


def _span(idx, freq):
    """Half-open [start, end) date range covered by a block of period labels."""
    off = {"D": pd.Timedelta(days=1), "W": pd.Timedelta(days=7), "MS": pd.offsets.MonthBegin(1), "YS": pd.offsets.YearBegin(1)}[freq]
    # weekly labels are week-ENDING Sundays (pandas default): the period covers the 7 days up to and including the label
    if freq == "W": return idx[0] - pd.Timedelta(days=6), idx[-1] + pd.Timedelta(days=1)
    return idx[0], idx[-1] + off


def bridge(df: pd.DataFrame, date: str, metric: str, dims: list, freq: str, series: pd.Series, qty: str | None = None, min_change: float = 0.03):
    """Explain the change in `metric` (a summable measure) between the last two equal windows. Returns a finding dict or None."""
    win = _windows(series, freq)
    if win is None or not dims: return None
    (p0, p1), (c0, c1) = _span(win[0], freq), _span(win[1], freq)
    d = df[[date, metric, *dims] + ([qty] if qty else [])].dropna(subset=[date, metric])
    prev, cur = d[(d[date] >= p0) & (d[date] < p1)], d[(d[date] >= c0) & (d[date] < c1)]
    pt, ct = float(prev[metric].sum()), float(cur[metric].sum())
    if pt == 0 or abs(ct - pt) / abs(pt) < min_change: return None
    delta = ct - pt
    best = None
    for dim in dims:
        a, b = prev.groupby(dim, observed=True)[metric].sum(), cur.groupby(dim, observed=True)[metric].sum()
        contrib = b.sub(a, fill_value=0.0)
        if len(contrib) < 2: continue
        assert abs(contrib.sum() - delta) <= 1e-6 * max(1.0, abs(delta)), "contributions must add up to the change"
        top = contrib.reindex(contrib.abs().sort_values(ascending=False).index)
        focus = abs(top.iloc[0]) / max(abs(contrib).sum(), 1e-12)      # how concentrated the movement is in one segment
        if best is None or focus > best[0]: best = (focus, dim, a, b, top)
    if best is None: return None
    _, dim, a, b, top = best
    rows = [{"segment": str(k), "previous": float(a.get(k, 0.0)), "current": float(b.get(k, 0.0)), "change": float(v),
             "share_of_change": float(v / delta)} for k, v in top.head(4).items()]
    unit = UNIT[freq]; w = WINDOW[freq]
    span = f"the last {w} {unit}s" if w > 1 else f"the latest {unit}"
    prior = f"the {w} {unit}s before" if w > 1 else f"the previous {unit}"
    up = delta > 0
    lead = rows[0]
    lead_txt = (f"{lead['segment']} ({'+' if lead['change'] >= 0 else '-'}{_fmt(abs(lead['change']))}, {abs(lead['share_of_change']) * 100:.0f}% of the change)"
                if abs(lead["share_of_change"]) >= 0.25 else "no single value dominates")
    out = {"kind": "change", "severity": "info",
           "title": f"{metric} {'rose' if up else 'fell'} {abs(delta / pt) * 100:.0f}% in {span}",
           "detail": f"{span.capitalize()} totalled {_fmt(ct)} against {_fmt(pt)} in {prior}, a change of {'+' if up else '-'}{_fmt(abs(delta))}. "
                     f"Split by {dim}, the biggest mover is {lead_txt}.",
           "action": f"Look at {lead['segment']} first: " + ("find out what worked and repeat it." if up else "find out what went wrong and fix it.") if abs(lead["share_of_change"]) >= 0.25
                     else f"Check several {dim} values, since the change is spread out.",
           "evidence": {"dimension": dim, "window": f"{span} vs {prior}", "previous_total": pt, "current_total": ct, "change": delta,
                        "contributions": rows, "contributions_sum_to_change": True, "rows_current": int(len(cur)), "rows_previous": int(len(prev))}}
    if qty and qty in d.columns:
        pv = _price_volume(prev, cur, dim, metric, qty)
        if pv:
            out["evidence"]["price_volume"] = pv
            v, pr, tot = pv["volume_effect"], pv["price_effect"], abs(delta)
            if abs(pr) < 0.02 * tot: out["detail"] += f" Almost all of it came from selling {'more' if v >= 0 else 'fewer'} units; the average price per unit barely moved."
            elif abs(v) < 0.02 * tot: out["detail"] += f" Almost all of it came from the average price per unit being {'higher' if pr >= 0 else 'lower'}; units sold barely moved."
            else: out["detail"] += (f" {'+' if v >= 0 else '-'}{_fmt(abs(v))} came from selling {'more' if v >= 0 else 'fewer'} units and "
                                    f"{'+' if pr >= 0 else '-'}{_fmt(abs(pr))} from a {'higher' if pr >= 0 else 'lower'} average price per unit.")
    return out


def _price_volume(prev, cur, dim, metric, qty):
    """Volume/price split per segment; adds up exactly: sum(Q1*P1 - Q0*P0) = sum((Q1-Q0)*P0) + sum(Q1*(P1-P0))."""
    q0, q1 = prev.groupby(dim, observed=True)[qty].sum(), cur.groupby(dim, observed=True)[qty].sum()
    r0, r1 = prev.groupby(dim, observed=True)[metric].sum(), cur.groupby(dim, observed=True)[metric].sum()
    segs = q0.index.union(q1.index)
    q0, q1, r0, r1 = (x.reindex(segs, fill_value=0.0) for x in (q0, q1, r0, r1))
    if (q1 <= 0).all() or (q0 <= 0).all(): return None
    p0 = (r0 / q0.where(q0 > 0)).fillna(0.0); p1 = (r1 / q1.where(q1 > 0)).fillna(0.0)
    vol = ((q1 - q0) * p0).where(q0 > 0, r1)           # a brand-new segment is all volume
    price = (q1 * (p1 - p0)).where(q0 > 0, 0.0)
    total = float(r1.sum() - r0.sum())
    if abs(float(vol.sum() + price.sum()) - total) > 1e-6 * max(1.0, abs(total)): return None
    return {"volume_effect": float(vol.sum()), "price_effect": float(price.sum())}


def daily_anomalies(df: pd.DataFrame, date: str, metric: str, dims: list, mean_metric: bool = False, z: float = 6.0, max_n: int = 2):
    """Days far outside the recent level x day-of-week pattern. Returns finding dicts, strongest first."""
    d = df[[date, metric] + dims].dropna(subset=[date, metric])
    if d.empty: return []
    day = d.set_index(date)[metric].resample("D")
    y = (day.mean() if mean_metric else day.sum()).astype(float)
    if mean_metric: y = y.dropna()
    if len(y.dropna()) < 28 or (y.index.max() - y.index.min()).days < 27: return []
    base = y.rolling(29, center=True, min_periods=15).median()
    ratio = (y + 1e-9) / (base + 1e-9)
    ok = np.isfinite(ratio) & (base > 0)
    if ok.sum() < 28: return []
    dow = ratio[ok].groupby(ratio[ok].index.dayofweek).median(); dow = dow / dow.mean()
    exp = base * y.index.dayofweek.map(dow).values
    # Revenue/count style totals have variance that grows with the level (more orders -> bigger swings), so residuals are
    # scaled by sqrt(expected) (Pearson); averages have roughly constant variance, so they are left unscaled.
    scale = np.ones(len(y)) if mean_metric else np.sqrt(np.clip(exp.values, 1e-9, None))
    r = pd.Series((y.values - exp.values) / scale, index=y.index).where(ok)
    med = r.median(); sig = 1.4826 * (r - med).abs().median()
    if not np.isfinite(sig) or sig <= 0: return []
    score = (r - med) / sig
    # a flagged day must be both statistically extreme and practically large (>=40% off what was expected)
    flag = score[(score.abs() > z) & ((y - exp).abs() >= 0.4 * exp.abs())].abs().sort_values(ascending=False).head(max_n)
    out = []
    for t in flag.index:
        obs, e = float(y[t]), float(exp[t]); up = obs > e
        who = _attribute(d, date, metric, dims, t)
        out.append({"kind": "anomaly", "severity": "warn", "title": f"{'Spike' if up else 'Drop'} on {t.strftime('%d %b %Y')}",
                    "detail": f"{metric} was {_fmt(obs)} that day, about {abs(obs - e) / abs(e) * 100:.0f}% {'above' if up else 'below'} the {_fmt(e)} expected for a {t.strftime('%A')} at that time of year."
                              + (f" Most of the difference came from {who[0]} ({'+' if who[1] >= 0 else '-'}{_fmt(abs(who[1]))})." if who else ""),
                    "action": "Check whether this was a real event (a campaign, a big order or donor) or a data-entry mistake.",
                    "evidence": {"date": t.strftime("%Y-%m-%d"), "observed": obs, "expected": e, "robust_score": float(score[t]),
                                 "segment": None if not who else {"dimension": who[2], "value": who[0], "change": who[1]}}})
    return out


def _attribute(d, date, metric, dims, t):
    """Segment whose value that day differs most from its typical daily value in the surrounding +-14 days."""
    best = None
    near = d[(d[date] >= t - pd.Timedelta(days=14)) & (d[date] <= t + pd.Timedelta(days=14))]
    today = near[near[date].dt.normalize() == t.normalize()]
    others = near[near[date].dt.normalize() != t.normalize()]
    n_other = max(others[date].dt.normalize().nunique(), 1)
    for dim in dims:
        a = today.groupby(dim, observed=True)[metric].sum(); b = others.groupby(dim, observed=True)[metric].sum() / n_other
        diff = a.sub(b, fill_value=0.0)
        if diff.empty: continue
        k = diff.abs().idxmax()
        if best is None or abs(diff[k]) > abs(best[1]): best = (str(k), float(diff[k]), dim)
    return best


def find_quantity_column(df: pd.DataFrame, metric: str, metric_cols: list):
    """A numeric column that looks like units sold (never the metric itself)."""
    for c in metric_cols:
        if c != metric and any(h in c.lower().split("_") or c.lower() == h for h in QTY_HINT): return c
    return None
