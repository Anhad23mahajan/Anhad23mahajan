import json, sys
import numpy as np, pandas as pd
P = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/bench.jsonl"
rows = [json.loads(l) for l in open(P)]
print("windows:", len(rows))
def grp(s):
    return "aus_retail" if s.startswith("aus_retail") else "synthetic" if s.startswith("synthetic") else "classic"
recs = []
for r in rows:
    truth = np.array(r["truth"]); fcs = {k: (np.array(v) if v is not None else None) for k, v in r["fc"].items()}
    # derived combinations
    def comb(*names):
        if all(fcs.get(n) is not None for n in names): return np.mean([fcs[n] for n in names], axis=0)
    fcs["Comb(ETS,Theta)"] = comb("ETS(AICc)", "Theta")
    fcs["Comb(ETS,Theta,sNaive)"] = comb("ETS(AICc)", "Theta", "snaive")
    fcs["Comb(STL+ETS,Theta)"] = comb("STL+ETS(AICc)", "Theta")
    fcs["Comb(ETS,STL+ETS,Theta)"] = comb("ETS(AICc)", "STL+ETS(AICc)", "Theta")
    sc = r["hist_scale"] or np.nan
    key = f'{r["series"]}|{r["L"]}|{r["t"]}'
    for name, fc in fcs.items():
        if fc is None:
            recs.append(dict(series=r["series"], g=grp(r["series"]), L=r["L"], method=name, mae=np.nan, mase=np.nan, fail=1, cov=np.nan, width=np.nan, key=key)); continue
        mae = np.mean(np.abs(truth - fc))
        cov = width = np.nan
        if name in r["pi"]:
            lo, hi = np.array(r["pi"][name][0]), np.array(r["pi"][name][1])
            cov = np.mean((truth >= lo) & (truth <= hi)); width = np.mean(hi - lo) / np.mean(np.abs(truth))
        recs.append(dict(series=r["series"], g=grp(r["series"]), L=r["L"], method=name, mae=mae, mase=mae / sc if sc and sc > 0 else np.nan, fail=0, cov=cov, width=width, key=key))
    for name, tm in r["time"].items():
        recs.append(dict(series=r["series"], g=grp(r["series"]), L=r["L"], method="TIME:" + name, mae=tm, mase=np.nan, fail=0, cov=np.nan, width=np.nan, key=key))
d = pd.DataFrame(recs)
tm = d[d.method.str.startswith("TIME:")].copy(); d = d[~d.method.str.startswith("TIME:")].copy()
d["key"] = d["key"].fillna("")
# add window key to every record (needed for pairing)
order = ["naive", "snaive", "app_HW", "Theta", "ETS(AICc)", "STL+ETS(AICc)", "Comb(ETS,Theta)", "Comb(STL+ETS,Theta)", "Comb(ETS,Theta,sNaive)", "Comb(ETS,STL+ETS,Theta)"]
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)

def relmae(df, ref):
    """geometric mean of per-window MAE ratio vs reference method (lower is better, <1 beats ref)"""
    p = df.pivot_table(index="key", columns="method", values="mae")
    out = {}
    for m in order:
        if m in p and ref in p:
            ok = p[[m, ref]].dropna(); ok = ok[(ok[m] > 0) & (ok[ref] > 0)]
            out[m] = float(np.exp(np.mean(np.log(ok[m] / ok[ref])))) if len(ok) else np.nan
    return pd.Series(out)

print("\n=== Mean MASE (lower better) by group ===")
print(d.pivot_table(index="method", columns="g", values="mase", aggfunc="mean").reindex(order).round(3))
print("\n=== Median MASE by group ===")
print(d.pivot_table(index="method", columns="g", values="mase", aggfunc="median").reindex(order).round(3))
print("\n=== Relative MAE vs seasonal-naive (geo-mean ratio; <1 = better than snaive) ===")
tab = {}
for g, sub in d.groupby("g"): tab[g] = relmae(sub, "snaive")
tab["ALL"] = relmae(d, "snaive"); print(pd.DataFrame(tab).reindex(order).round(3))
print("\n=== Relative MAE vs NAIVE ===")
tab = {}
for g, sub in d.groupby("g"): tab[g] = relmae(sub, "naive")
tab["ALL"] = relmae(d, "naive"); print(pd.DataFrame(tab).reindex(order).round(3))
print("\n=== Mean MASE by history length L (all groups) ===")
print(d.pivot_table(index="method", columns="L", values="mase", aggfunc="mean").reindex(order).round(3))
print("\n=== Relative MAE vs naive by L (all groups) ===")
tab = {L: relmae(sub, "naive") for L, sub in d.groupby("L")}; print(pd.DataFrame(tab).reindex(order).round(3))
print("\n=== Win-rate vs app_HW (share of windows where method MAE < app_HW MAE) ===")
p = d.pivot_table(index="key", columns="method", values="mae")
print({m: round(float((p[m] < p["app_HW"]).mean()), 3) for m in order if m in p and m != "app_HW"})
print("\n=== 95% PI empirical coverage (nominal 0.95) & mean width/|actual| ===")
c = d[d.method.isin(["app_HW", "Theta", "ETS(AICc)", "STL+ETS(AICc)"])]
print(c.pivot_table(index="method", columns="g", values="cov", aggfunc="mean").round(3))
print(c.pivot_table(index="method", columns="L", values="cov", aggfunc="mean").round(3))
print("width/|actual| (median):"); print(c.pivot_table(index="method", columns="g", values="width", aggfunc="median").round(3))
print("\n=== failures ===")
print(d.groupby("method")["fail"].sum())
print("\n=== runtime seconds per forecast (median / p90), shared contended sandbox, OMP_NUM_THREADS=1 ===")
tm["method"] = tm["method"].str.replace("TIME:", "")
print(tm.groupby("method")["mae"].describe(percentiles=[.5, .9])[["50%", "90%", "max"]].round(2))
