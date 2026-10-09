import json, numpy as np, pandas as pd
rows = [json.loads(l) for l in open("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/bench.jsonl")]
rec = []
for r in rows:
    tr = np.array(r["truth"]); f = {k: np.array(v) for k, v in r["fc"].items()}
    cand = {
      "naive": f["naive"], "snaive": f["snaive"], "app_HW": f["app_HW"],
      "Comb3(ETS,Theta,sNaive)": np.mean([f["ETS(AICc)"], f["Theta"], f["snaive"]], axis=0),
      "FastComb(Theta,sNaive)": np.mean([f["Theta"], f["snaive"]], axis=0),
      "FastComb3(HW,Theta,sNaive)": np.mean([f["app_HW"], f["Theta"], f["snaive"]], axis=0),
      "Policy A: HW if n>=24 else Theta+sNaive": f["app_HW"] if r["L"] >= 24 else np.mean([f["Theta"], f["snaive"]], axis=0),
      "Policy B: HW if n>=24 else Comb3": f["app_HW"] if r["L"] >= 24 else np.mean([f["ETS(AICc)"], f["Theta"], f["snaive"]], axis=0),
      "Policy C: HW if n>=24 else snaive/naive": f["app_HW"] if r["L"] >= 24 else f["snaive"],
      "Policy D: Comb(HW,Theta,sNaive) if n>=24 else Theta+sNaive": np.mean([f["app_HW"], f["Theta"], f["snaive"]], axis=0) if r["L"] >= 24 else np.mean([f["Theta"], f["snaive"]], axis=0),
    }
    for k, v in cand.items():
        rec.append(dict(m=k, L=r["L"], mase=np.mean(np.abs(tr - v)) / r["hist_scale"], mae=np.mean(np.abs(tr - v))))
d = pd.DataFrame(rec)
pd.set_option("display.width", 200)
t = d.pivot_table(index="m", columns="L", values="mase", aggfunc="mean"); t["ALL"] = d.groupby("m")["mase"].mean()
print(t.round(3).sort_values("ALL").to_string())
