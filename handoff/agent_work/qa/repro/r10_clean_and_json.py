"""BUG-30/31  clean() turns Python bool into int (ai:true -> 1, boolean cells -> 0/1) and passes timedelta through; plus 'inf' text leaking into insights.
run: /home/user/work/venv/bin/python -I r10_clean_and_json.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
import json, datetime, decimal
print("clean(True) =", repr(A.clean(True)), "| clean(np.bool_(True)) =", repr(A.clean(np.bool_(True))), "| clean({'ai': True}) =", A.clean({"ai": True}))
print("clean(pd.Timedelta('1D')) =", repr(A.clean(pd.Timedelta("1D"))), "(left as-is; only FastAPI's encoder turns it into seconds)", "| clean(Decimal('1.5')) =", repr(A.clean(decimal.Decimal("1.5"))))
hdr("Preview of boolean columns (Raw Input / Cleaned Output tab)")
df = load("pct_bool_thousands.csv"); pv = A.df_to_preview(df, 3); print("columns:", pv["columns"], "\ndtypes :", pv["dtypes"], "\nrows   :", pv["rows"], "<- 'paid' and 'repeat_customer' show 0/1, dtype labels say 'str'/'datetime64[us]' on pandas 3")
hdr("what the live server returns for the 'ai' flag (see t_api_edges / curl):")
import urllib.request
try:
    r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:18711/api/demo", method="POST")); d = json.loads(r.read()); print("/api/demo -> \"ai\":", json.dumps(d["ai"]), "  (health endpoint returns:", json.loads(urllib.request.urlopen("http://127.0.0.1:18711/api/health").read()), ")")
except Exception as e: print("server not running on :18711 ->", e)
hdr("inf in the data: KPI total is null, insight text says 'inf'")
p, ins, ch = analyse(load("edge_inf_values.csv")); print("KPIs:", [(k["label"], k["value"]) for k in p["kpis"]]); print("insights:", [i["detail"] for i in ins])
