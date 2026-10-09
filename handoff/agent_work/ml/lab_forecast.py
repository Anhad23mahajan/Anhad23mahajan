"""lab_forecast.py - design tooling (not shipped): cache component backtests so selection / interval rules can be
replayed offline in seconds.  Usage: python lab_forecast.py collect --seed 1 --n 120 --out results/lab/dev1.pkl"""
import os
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
import sys, pickle, argparse, warnings, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import bench_forecast as B
import forecasting as FC

LAB_CFG = dict(seasonal_damped=True, extra_components=["drift"])


def work(task):
    y, idx, meta, H, k, cfgover = task
    warnings.simplefilter("ignore")
    cfg = {**FC.CFG, **LAB_CFG, **cfgover}
    out = []
    for t in B.pick_origins(len(y), H, k):
        ytr = y[:t]
        col = FC._collect(ytr, meta["m"], H, cfg, all_final=True)
        out.append(dict(sid=meta["sid"], origin=t, col=col, yte=y[t:t + H], scale=float(np.mean(np.abs(np.diff(ytr)))), meta=meta))
    return out


def collect(seed, n, H, k, out, cfgover, demo=False):
    series = [B.gen_series(seed, i) for i in range(n)]
    if demo:
        series += B.demo_series()
    tasks = [(y, idx, mt, H, k, cfgover) for y, idx, mt in series]
    res = []
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        for r in ex.map(work, tasks, chunksize=2):
            res += r
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    pickle.dump(res, open(out, "wb"))
    print(f"collected {len(res)} (series,origin) in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--H", type=int, default=6)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--out", default="results/lab/dev1.pkl")
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    import json
    collect(a.seed, a.n, a.H, a.k, a.out, json.loads(a.cfg), a.demo)
