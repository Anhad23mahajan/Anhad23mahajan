import json, numpy as np, pandas as pd
P = "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/bench.jsonl"
rows = [json.loads(l) for l in open(P)]
def grp(s): return "aus_retail" if s.startswith("aus_retail") else "synthetic" if s.startswith("synthetic") else "classic"
rec = []
for r in rows:
    tr = np.array(r["truth"]); f = {k: np.array(v) for k, v in r["fc"].items()}
    f["Comb3"] = np.mean([f["ETS(AICc)"], f["Theta"], f["snaive"]], axis=0)
    f["policy_app24"] = f["app_HW"] if r["L"] >= 24 else f["Comb3"]          # keep app HW only when >=2 seasons
    f["policy_ets36"] = f["ETS(AICc)"] if r["L"] >= 36 else f["Comb3"]
    sid = r["series"]
    rec.append(dict(series=sid, g=grp(sid), L=r["L"], key=f'{sid}|{r["L"]}|{r["t"]}', **{m: np.mean(np.abs(tr - v)) for m, v in f.items()},
                    sc=r["hist_scale"], **{"mase_" + m: np.mean(np.abs(tr - v)) / r["hist_scale"] for m, v in f.items()}))
d = pd.DataFrame(rec)
print("=== mean MASE by L: app_HW vs Comb3 (ETS+Theta+sNaive) vs policies ===")
cols = ["mase_naive", "mase_snaive", "mase_app_HW", "mase_ETS(AICc)", "mase_Comb3", "mase_policy_app24", "mase_policy_ets36"]
print(d.groupby("L")[cols].mean().round(3).T)
print("overall:", d[cols].mean().round(3).to_dict())
# cluster bootstrap by series: rel MAE (geo-mean ratio) of A vs B
rng = np.random.default_rng(0)
ser = d["series"].unique()
def geo(df, a, b):
    ok = df[(df[a] > 0) & (df[b] > 0)]; return float(np.exp(np.mean(np.log(ok[a] / ok[b]))))
def boot(a, b, mask=None, n=500):
    sub = d if mask is None else d[mask]
    ss = sub["series"].unique(); idx = {s: sub.index[sub.series == s].values for s in ss}
    vals = []
    for _ in range(n):
        pick = rng.choice(ss, size=len(ss), replace=True)
        ii = np.concatenate([idx[s] for s in pick]); vals.append(geo(sub.loc[ii], a, b))
    return geo(sub, a, b), np.percentile(vals, [2.5, 97.5])
for label, a, b, mask in [("Comb3 vs app_HW (all L)", "Comb3", "app_HW", None), ("Comb3 vs app_HW (L<24)", "Comb3", "app_HW", d.L < 24), ("Comb3 vs app_HW (L>=24)", "Comb3", "app_HW", d.L >= 24),
                          ("app_HW vs naive (L<24)", "app_HW", "naive", d.L < 24), ("app_HW vs naive (L>=24)", "app_HW", "naive", d.L >= 24),
                          ("Comb3 vs snaive (L>=12)", "Comb3", "snaive", d.L >= 12), ("ETS vs app_HW (L>=36)", "ETS(AICc)", "app_HW", d.L >= 36),
                          ("policy_app24 vs app_HW (all)", "policy_app24", "app_HW", None)]:
    est, ci = boot(a, b, mask); print(f"{label:34s} ratio={est:.3f}  95% CI [{ci[0]:.3f}, {ci[1]:.3f}]  (cluster bootstrap by series)")

print("\n=== interval calibration: scale ETS PI half-widths by k ===")
for k in (1.0, 1.25, 1.5, 2.0):
    cov = {}
    for r in rows:
        if "ETS(AICc)" not in r["pi"]: continue
        tr = np.array(r["truth"]); fc = np.array(r["fc"]["ETS(AICc)"]); lo, hi = np.array(r["pi"]["ETS(AICc)"][0]), np.array(r["pi"]["ETS(AICc)"][1])
        lo2, hi2 = fc - k * (fc - lo), fc + k * (hi - fc)
        cov.setdefault(grp(r["series"]), []).append(np.mean((tr >= lo2) & (tr <= hi2)))
    print(f"k={k}: " + ", ".join(f"{g}={np.mean(v):.3f}" for g, v in cov.items()) + f" | all={np.mean(sum(cov.values(), [])):.3f}")
print("\n=== negative forecasts produced (positive-only series) ===")
neg = {m: 0 for m in ["app_HW", "ETS(AICc)", "Theta", "STL+ETS(AICc)"]}
for r in rows:
    for m in neg:
        if (np.array(r["fc"][m]) < 0).any() and min(r["truth"]) >= 0: neg[m] += 1
print(neg, "of", len(rows))
