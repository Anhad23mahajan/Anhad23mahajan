import sys, time, json, warnings, os
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from multiprocessing import Pool
from fc_lib import *

DATA = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/bench.jsonl"
M = 12; H = 6
LENS = [8, 12, 24, 36, 48]
RUN = {"naive": f_naive, "snaive": f_snaive, "app_HW": f_app, "Theta": f_theta, "ETS(AICc)": f_ets, "STL+ETS(AICc)": f_stl_ets}

def build_tasks():
    rng = np.random.default_rng(2026)
    tasks = []
    # --- real: Australian retail turnover (tsibbledata::aus_retail), monthly, 441 obs per series
    d = pd.read_csv(f"{DATA}/aus_retail.csv")
    groups = [(k, g.sort_values("rownames")["Turnover"].values) for k, g in d.groupby("Series ID") if len(g) == 441]
    pick = rng.choice(len(groups), size=50, replace=False)
    for gi in pick:
        sid, y = groups[gi]
        for L in LENS:
            for t in rng.choice(np.arange(441 - 180, 441 - H), size=2, replace=False):
                tasks.append(("aus_retail:" + sid, L, int(t), y[t - L:t].tolist(), y[t:t + H].tolist()))
    # --- real: other classic monthly series
    for name, col in [("AirPassengers", "value"), ("USAccDeaths", "value"), ("wineind", "value"), ("a10", "value"), ("debitcards", "value"), ("auscafe", "value")]:
        df = pd.read_csv(f"{DATA}/{name}.csv"); y = df[col].values.astype(float)
        for L in LENS:
            for t in rng.choice(np.arange(max(L, len(y) // 3), len(y) - H), size=3, replace=False):
                tasks.append((name, L, int(t), y[t - L:t].tolist(), y[t:t + H].tolist()))
    # --- synthetic "small business" series with known noise (for interval calibration)
    for i in range(100):
        L = int(rng.choice(LENS)); n = L + H
        trend = rng.normal(0.005, 0.01); amp = rng.uniform(0, 0.3); ph = rng.uniform(0, 2 * np.pi); base = rng.uniform(50, 5000); sig = rng.uniform(0.05, 0.25)
        tt = np.arange(n)
        mu = base * np.exp(trend * tt) * (1 + amp * np.sin(2 * np.pi * tt / M + ph))
        y = mu * np.exp(rng.normal(0, sig, n))
        if rng.random() < 0.3: y[rng.integers(0, L)] *= rng.uniform(1.8, 3.0)   # one-off spike in history
        tasks.append((f"synthetic{i}", L, 0, y[:L].tolist(), y[L:].tolist()))
    rng2 = np.random.default_rng(7); order = rng2.permutation(len(tasks)); return [tasks[i] for i in order]

def work(task):
    sid, L, t, hist, truth = task
    y = mk(hist); res = {"series": sid, "L": L, "t": t, "truth": truth, "hist_scale": None, "fc": {}, "pi": {}, "time": {}}
    k = M if len(y) > M else 1
    res["hist_scale"] = float(np.mean(np.abs(y.values[k:] - y.values[:-k])))
    for name, f in RUN.items():
        t0 = time.time()
        try:
            out = f(y, H, M)
            fc = np.asarray(out[0], float)
            res["fc"][name] = fc.tolist()
            if out[1] is not None and out[1][0] is not None:
                res["pi"][name] = [np.asarray(out[1][0]).tolist(), np.asarray(out[1][1]).tolist()]
        except Exception as e:
            res["fc"][name] = None; res.setdefault("err", {})[name] = f"{type(e).__name__}: {str(e)[:80]}"
        res["time"][name] = time.time() - t0
    return res

if __name__ == "__main__":
    tasks = build_tasks(); print("tasks:", len(tasks), flush=True)
    t0 = time.time()
    with open(OUT, "w") as fh, Pool(3) as pool:
        for i, r in enumerate(pool.imap_unordered(work, tasks, chunksize=2)):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            if i % 25 == 0: print(f"{i}/{len(tasks)} done, {time.time()-t0:.0f}s", flush=True)
    print("DONE", time.time() - t0, flush=True)
