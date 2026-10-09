import sys, time, warnings
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
import pandas as pd, numpy as np
from fc_lib import *
d = pd.read_csv("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/AirPassengers.csv")
y = mk(d["value"].values[:36])
for name, f in METHODS.items():
    t = time.time(); out = f(y, 6, 12); dt = time.time() - t
    fc, pi = out[0], out[1]
    print(f"{name:26s} {dt:5.2f}s fc={np.round(fc,0)} PI={'yes' if pi is not None else 'no'}")
fc, pi, info = f_ets(y, 6, 12, return_info=True); print("ETS chosen:", info); print("PI lo/hi:", np.round(pi[0],0), np.round(pi[1],0))
print("truth:", d["value"].values[36:42])
