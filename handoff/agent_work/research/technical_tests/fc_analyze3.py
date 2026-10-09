import json, numpy as np
rows = [json.loads(l) for l in open("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/bench.jsonl")]
def cov(name, k=1.0, cond=lambda r: True):
    out = []
    for r in rows:
        if not cond(r) or name not in r["pi"]: continue
        tr = np.array(r["truth"]); fc = np.array(r["fc"][name]); lo, hi = map(np.array, r["pi"][name])
        out.append(np.mean((tr >= fc - k * (fc - lo)) & (tr <= fc + k * (hi - fc))))
    return np.mean(out), len(out)
for name in ["app_HW", "ETS(AICc)", "Theta"]:
    for k in (1.0, 1.5):
        a = cov(name, k); lt = cov(name, k, lambda r: r["L"] < 24); ge = cov(name, k, lambda r: r["L"] >= 24)
        print(f"{name:10s} k={k}: overall {a[0]:.3f} (n={a[1]}) | L<24 {lt[0]:.3f} | L>=24 {ge[0]:.3f}")
