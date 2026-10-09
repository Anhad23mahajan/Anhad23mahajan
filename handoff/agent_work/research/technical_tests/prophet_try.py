import time, warnings, logging, sys
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
import pandas as pd, numpy as np
t0 = time.time()
from prophet import Prophet
print("import %.1fs" % (time.time() - t0))
d = pd.read_csv("/tmp/claude-0/-home-user-Anhad23mahajan/be613ad6-240e-52cd-ac9f-915e88d6d3d2/scratchpad/data/AirPassengers.csv")
y = d["value"].values[:36]
df = pd.DataFrame({"ds": pd.date_range("2000-01-01", periods=36, freq="MS"), "y": y})
t0 = time.time()
m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
m.fit(df)
print("fit %.1fs" % (time.time() - t0))
fut = m.make_future_dataframe(periods=6, freq="MS")
t0 = time.time(); fc = m.predict(fut); print("predict %.1fs" % (time.time() - t0))
print(fc[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(6).round(0).to_string())
print("truth", d["value"].values[36:42])
tr = d["value"].values[36:42]; f = fc.tail(6)
inside = ((tr >= f["yhat_lower"].values) & (tr <= f["yhat_upper"].values))
print("inside default interval (80%):", inside.tolist(), "-> %d of 6" % inside.sum(), "| MAE %.1f" % np.mean(np.abs(tr - f["yhat"].values)))
