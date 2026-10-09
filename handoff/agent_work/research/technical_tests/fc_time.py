import sys, time
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
import pandas as pd, numpy as np, warnings
warnings.simplefilter("ignore")
from fc_lib import *
d = pd.read_csv("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/AirPassengers.csv")
for n in (24, 36, 60):
    y = mk(d["value"].values[:n]); print("n =", n)
    tot = 0
    for c in ets_candidates(n, 12, True):
        t = time.time()
        try:
            res = ETSModel(y, seasonal_periods=12 if c["seasonal"] else None, initialization_method="estimated", **c).fit(disp=False, maxiter=200); aicc = res.aicc
        except Exception as e: aicc = float("nan")
        dt = time.time() - t; tot += dt
        print(f"   {str(c):90s} {dt:5.2f}s aicc={aicc:8.1f}")
    print("   total %.1fs" % tot)
t = time.time(); ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal="add", seasonal_periods=12).fit(); print("HW damped seasonal n=60: %.2fs" % (time.time()-t))
t = time.time(); ThetaModel(y, period=12).fit().forecast(6); print("Theta n=60: %.2fs" % (time.time()-t))
