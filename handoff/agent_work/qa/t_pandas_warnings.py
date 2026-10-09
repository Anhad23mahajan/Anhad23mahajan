"""Collect every warning raised (with lumen file:line) while running the whole non-LLM pipeline on every fixture.
Run in each venv: <venv>/bin/python -I t_pandas_warnings.py"""
import sys, warnings, collections, pathlib
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import pandas as pd, numpy as np
from app import analytics as A
D = pathlib.Path("/home/user/work/qa/fixtures/data")
seen = collections.OrderedDict(); errs = collections.OrderedDict()
for f in sorted(D.iterdir()):
    if f.name.startswith("big_"): continue
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            raw = A.read_raw_df(f.read_bytes(), f.name); A.df_to_preview(raw)
            df = A.preprocess_df(raw); p = A.profile(df); A.insights(df, p); A.starter_charts(df, p); A.df_to_preview(df)
            if p["date"] and p["metric"]:
                try: A.forecast(df, p["date"], p["metric"], 6)
                except ValueError: pass
        except Exception as e:
            errs[f.name] = f"{type(e).__name__}: {str(e)[:100]}"
    for x in w:
        loc = x.filename.replace("/home/user/Anhad23mahajan/lumen/", "")
        if "site-packages" in loc: loc = "site-packages/" + loc.split("site-packages/")[1].split("/")[0] + ":" + str(x.lineno)
        else: loc = f"{loc}:{x.lineno}"
        k = (x.category.__name__, str(x.message)[:140], loc)
        seen.setdefault(k, []).append(f.name)
print("pandas", pd.__version__, "numpy", np.__version__)
for (cat, msg, loc), files in seen.items(): print(f"{cat:22s} {loc:34s} x{len(files):<3d} {msg}\n      e.g. {files[:3]}")
print("--- exceptions (pipeline level)")
for k, v in errs.items(): print(" ", k, "->", v)
