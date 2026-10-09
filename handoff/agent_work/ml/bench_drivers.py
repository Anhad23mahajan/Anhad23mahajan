"""bench_drivers.py - false-positive rate and detection power of drivers.py on synthetic data with KNOWN ground truth.

    python bench_drivers.py --runs 500            # writes results/drivers/{fp_study.json,power_study.json,SUMMARY.md}

False-positive study: pure-noise sales tables (no planted effect). A run is a false positive if the detector reports anything.
Power study: plant a known effect, count how often it is found at the right place (and nothing else).
"""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
import argparse
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drivers as D                      # noqa: E402
from test_drivers import make_sales, level_series   # noqa: E402

warnings.simplefilter("ignore")
KINDS = ["gauss_dow", "poisson_orders", "trend_season", "heavy_tail_t4"]


def noise_frame(kind, days, rng):
    if kind == "heavy_tail_t4":
        dates = pd.date_range("2024-01-01", periods=days, freq="D")
        dow = np.array([1.0, 0.95, 0.9, 1.0, 1.1, 1.4, 1.3])[dates.dayofweek]
        rows = []
        for p, sp in {"A": 0.4, "B": 0.25, "C": 0.2, "D": 0.1, "E": 0.05}.items():
            for g, sg in {"North": 0.5, "South": 0.3, "Online": 0.2}.items():
                v = np.maximum(1000 * dow * sp * sg * (1 + 0.15 * rng.standard_t(4, days) / np.sqrt(2)), 0)
                rows.append(pd.DataFrame({"date": dates, "product": p, "region": g, "amount": v}))
        return pd.concat(rows, ignore_index=True)
    return D._noise_frame(kind, days, rng)


def fp_one(args):
    kind, r, days = args
    warnings.simplefilter("ignore")
    rng = np.random.default_rng([2026, r, sum(map(ord, kind))])
    df = noise_frame(kind, days, rng)
    an = D.detect_anomalies(df, "date", "amount", ["product", "region"], max_items=50)
    cp = D._changepoint_items(df, "date", "amount", ["product", "region"], None, None, None)
    br = D.variance_bridge(df, "date", "amount", ["product", "region"])
    return kind, len(an), len(cp), br is not None


def power_one(args):
    kind, seed, size, noise, where = args
    warnings.simplefilter("ignore")
    day = "2024-09-12"
    if kind == "spike":
        prod = "Hoodie" if where == "big" else "Mug"
        df = make_sales(seed, noise=noise, spike=(day, prod, size))
        out = D.detect_anomalies(df, "order_date", "amount", ["product", "region"], max_items=50)
        dates = [a["evidence"]["date"] for a in out]
        found = day in dates
        only = dates == [day]
        attributed = False
        if found:
            a = out[dates.index(day)]
            cause = a["evidence"].get("cause") or {}
            attributed = (cause.get("segment") == prod) or (prod in (a["evidence"].get("segment") or ""))
        return kind, size, noise, where, found, only, attributed, None
    # level shift
    s = level_series(seed, shift=size, noise=noise)
    cps = D.detect_change_points(s, season=7, min_seg=14)
    found = len(cps) >= 1 and min(abs(c["index"] - 200) for c in cps) <= 3
    only = len(cps) == 1 and found
    err = None if not found else float(min(cps, key=lambda c: abs(c["index"] - 200))["change_pct"] - size * 100)
    return kind, size, noise, where, found, only, found, err


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=500)
    ap.add_argument("--power-runs", type=int, default=100)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    out = HERE / "results" / "drivers"
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        fp = list(ex.map(fp_one, [(k, r, a.days) for k in KINDS for r in range(a.runs)], chunksize=5))
    df = pd.DataFrame(fp, columns=["kind", "anomalies", "changepoints", "bridge"])
    res = {}
    for k, g in df.groupby("kind"):
        res[k] = {"runs": int(len(g)), "days_per_run": a.days,
                  "anomaly_false_positive_runs": int((g.anomalies > 0).sum()), "anomaly_fp_rate": float((g.anomalies > 0).mean()),
                  "anomalies_flagged_total": int(g.anomalies.sum()), "anomaly_fp_per_1000_days": float(g.anomalies.sum() / (len(g) * a.days) * 1000),
                  "changepoint_false_positive_runs": int((g.changepoints > 0).sum()), "changepoint_fp_rate": float((g.changepoints > 0).mean()),
                  "bridge_false_alarm_runs": int(g.bridge.sum()), "bridge_fp_rate": float(g.bridge.mean()),
                  "any_finding_fp_rate": float(((g.anomalies > 0) | (g.changepoints > 0) | g.bridge).mean())}
    (out / "fp_study.json").write_text(json.dumps(res, indent=1))
    print(f"fp study done in {time.time() - t0:.0f}s")

    tasks = []
    for size in (0.10, 0.20, 0.40, 0.80):
        for noise in (0.03, 0.10):
            for where in ("big", "small"):
                tasks += [("spike", s, size, noise, where) for s in range(a.power_runs)]
    for size in (0.10, -0.10, 0.20, -0.20, 0.30, -0.30):
        for noise in (0.05, 0.10):
            tasks += [("shift", s, size, noise, "-") for s in range(a.power_runs)]
    with ProcessPoolExecutor(a.workers) as ex:
        pw = list(ex.map(power_one, tasks, chunksize=4))
    p = pd.DataFrame(pw, columns=["kind", "size", "noise", "where", "found", "only_planted", "attributed", "err_pct_points"])
    tab = p.groupby(["kind", "where", "size", "noise"]).agg(runs=("found", "size"), found=("found", "mean"), only_planted=("only_planted", "mean"),
                                                            attributed=("attributed", "mean"), loc_err_pct_points=("err_pct_points", "median")).reset_index()
    tab.to_csv(out / "power_study.csv", index=False)

    def md(d):
        cols = list(d.columns)
        lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for _, r in d.iterrows():
            lines.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r) + " |")
        return "\n".join(lines)

    fpt = pd.DataFrame(res).T.reset_index().rename(columns={"index": "noise type"})
    summary = ["# drivers.py false-positive and power study", "",
               f"Pure-noise tables ({a.days} days x 5 products x 3 regions, no planted effect), {a.runs} runs per noise type. "
               "A run counts as a false positive if the detector reports at least one finding of that kind.", "",
               md(fpt[["noise type", "runs", "anomaly_false_positive_runs", "anomaly_fp_rate", "anomaly_fp_per_1000_days", "changepoint_false_positive_runs",
                       "changepoint_fp_rate", "bridge_false_alarm_runs", "bridge_fp_rate", "any_finding_fp_rate"]]), "",
               f"## Power: planted effects found ({a.power_runs} runs per cell)", "",
               "spike = +X% units for one product on one day (big = Hoodie, ~64% of revenue; small = Mug, ~9% of revenue); noise = per-row multiplicative sd. "
               "shift = permanent level change at day 200 of 365 (weekly cycle present). `only_planted` = the planted effect was the ONLY thing reported.", "",
               md(tab)]
    (out / "SUMMARY.md").write_text("\n".join(summary))
    (out / "power_raw.csv").write_text(p.to_csv(index=False))
    print("\n".join(summary))


if __name__ == "__main__":
    main()
