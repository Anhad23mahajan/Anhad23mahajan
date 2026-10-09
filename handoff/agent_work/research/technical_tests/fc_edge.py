import sys, time, warnings
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from fc_lib import *
rng = np.random.default_rng(1)
cases = {
 "constant n=12": np.full(12, 100.0),
 "zeros+spikes n=24 (intermittent)": np.where(rng.random(24) < 0.6, 0, rng.integers(1, 20, 24)).astype(float),
 "negatives n=24 (profit)": rng.normal(0, 50, 24).cumsum(),
 "n=8 trend": np.arange(8) * 5 + 100 + rng.normal(0, 2, 8),
 "n=30 with one huge outlier": np.r_[rng.normal(100, 5, 14), 900, rng.normal(100, 5, 15)],
 "short + all positive noisy n=14": 200 + rng.normal(0, 40, 14),
}
for name, v in cases.items():
    y = mk(v); print("\n", name)
    for mname, f in [("app_HW", f_app), ("ETS(AICc)", f_ets), ("STL+ETS", f_stl_ets), ("Theta", f_theta)]:
        t = time.time()
        try:
            out = f(y, 6, 12); fc = out[0]; pi = out[1]
            lo, hi = (np.round(pi[0][[0, -1]], 0), np.round(pi[1][[0, -1]], 0)) if pi is not None and pi[0] is not None else (None, None)
            print(f"   {mname:10s} OK {time.time()-t:4.1f}s fc[0],fc[-1]={np.round(fc[[0,-1]],1)} PI h1/h6 lo={lo} hi={hi}")
        except Exception as e:
            print(f"   {mname:10s} FAIL {type(e).__name__}: {str(e)[:90]}")

print("\n--- weekly (m=52) and daily (m=7) as in the app ---")
w = mk(100 + 20*np.sin(2*np.pi*np.arange(120)/52) + rng.normal(0, 5, 120)); w.index = pd.date_range("2022-01-02", periods=120, freq="W")
t = time.time(); fit = ExponentialSmoothing(w, trend="add", damped_trend=True, seasonal="add", seasonal_periods=52).fit(); print("weekly n=120 HW seasonal m=52: %.1fs" % (time.time()-t), "(n>=2m? no, 120 < 104? ->", 120 >= 104, ")")
t = time.time()
try:
    r = ETSModel(w, error="add", trend="add", damped_trend=True, seasonal="add", seasonal_periods=52).fit(disp=False, maxiter=100); print("weekly ETS m=52 fit: %.1fs aicc=%.0f" % (time.time()-t, r.aicc))
except Exception as e: print("weekly ETS m=52 FAIL", type(e).__name__, str(e)[:100])
