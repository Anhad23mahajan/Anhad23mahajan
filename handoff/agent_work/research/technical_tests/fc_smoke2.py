import sys, time, warnings
sys.path.insert(0, "/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/tests")
import pandas as pd, numpy as np
warnings.simplefilter("ignore")
from fc_lib import *
d = pd.read_csv("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/AirPassengers.csv")
for n in (8, 12, 24, 36, 48):
    y = mk(d["value"].values[:n]); print("n=", n, "truth", d["value"].values[n:n+6])
    for name, f in METHODS_FAST.items():
        t = time.time(); out = f(y, 6, 12); dt = time.time() - t
        print(f"   {name:22s} {dt:5.2f}s fc={np.round(out[0],0)} PI={'yes' if out[1] is not None else 'no'}")
