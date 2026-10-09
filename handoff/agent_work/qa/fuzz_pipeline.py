"""Differential fuzz: random messy CSVs through the whole non-LLM pipeline. Deterministic by seed.
usage: <venv>/bin/python -I fuzz_pipeline.py OUT.json [N]
Then:  compare_fuzz.py a.json b.json"""
import sys, json, io, random, warnings, traceback, hashlib
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import numpy as np, pandas as pd
from app import analytics as A, llm
warnings.simplefilter("ignore")
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300

def gen_csv(seed):
    rng = random.Random(seed); nr = rng.choice([1, 2, 5, 12, 40, 200, 700]); cols = {}
    for i in range(rng.randint(1, 7)):
        kind = rng.choice(["int", "float", "money", "pct", "date_iso", "date_dmy", "date_mdy", "date_txt", "yyyymmdd", "text", "cat", "bool", "yesno", "id", "mixed", "empty", "ts_tz"])
        name = rng.choice(["amount", "date", "Date Created", "qty", "region", "Revenue ($)", "donor", "id", "notes", "flag", "month", "total", "x", "Amount", "price", "category", "set", "order", "वर्ष"])
        name = name if name not in cols else f"{name}{i}"
        base = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.randint(0, 300), unit="D")
        vals = []
        for r in range(nr):
            miss = rng.random() < rng.choice([0, 0, 0.05, 0.4])
            if miss: vals.append(rng.choice(["", "N/A", "-", "null", " "])); continue
            d = base + pd.Timedelta(days=rng.randint(0, 700) if kind.startswith("date") or kind in ("yyyymmdd", "ts_tz") else 0)
            vals.append({"int": lambda: rng.randint(-50, 5000), "float": lambda: round(rng.uniform(-100, 9999), 2), "money": lambda: rng.choice(["$", "€", "£", ""]) + f"{rng.uniform(0, 99999):,.2f}" if rng.random() > .1 else f"({rng.uniform(0, 500):.2f})",
                         "pct": lambda: f"{rng.uniform(0, 100):.1f}%", "date_iso": lambda: d.strftime("%Y-%m-%d"), "date_dmy": lambda: d.strftime("%d/%m/%Y"), "date_mdy": lambda: d.strftime("%m/%d/%Y"),
                         "date_txt": lambda: d.strftime("%d %b %Y"), "yyyymmdd": lambda: d.strftime("%Y%m%d"), "text": lambda: "".join(rng.choice("abcdefgh ") for _ in range(rng.randint(3, 30))),
                         "cat": lambda: rng.choice(["North", "South", "East", "West"]), "bool": lambda: rng.choice(["True", "False"]), "yesno": lambda: rng.choice(["Yes", "No", "Y", "N"]),
                         "id": lambda: 1000 + r if rng.random() > .02 else 5, "mixed": lambda: rng.choice([str(rng.randint(1, 99)), "abc", "n/a", "12.5"]), "empty": lambda: "",
                         "ts_tz": lambda: d.strftime("%Y-%m-%dT%H:%M:%S") + rng.choice(["+00:00", "+05:30", "Z"])}[kind]())
        cols[name] = vals
    sep = rng.choice([",", ",", ";", "\t"]); df = pd.DataFrame(cols)
    if sep != ",": df = df.astype(str).replace({"nan": ""})
    txt = df.to_csv(index=False, sep=sep)
    if rng.random() < .15: txt += ",,\n\n"
    return txt.encode(rng.choice(["utf-8", "utf-8", "utf-8-sig", "latin-1" if txt.isascii() else "utf-8"]))

out = {}
for seed in range(N):
    raw = gen_csv(seed); rec = {}
    try:
        rawdf = A.read_raw_df(raw, f"f{seed}.csv"); df = A.preprocess_df(rawdf); p = A.profile(df); ins = A.insights(df, p); ch = A.starter_charts(df, p)
        n = llm.narrate(ins, {}); pv = A.df_to_preview(df); sq = A.suggested_questions(p); sch = llm.schema_text(df)
        resp = A.clean({"profile": p, "insights": ins, "charts": ch, "narr": n, "q": sq, "pv": {k: v for k, v in pv.items() if k != "dtypes"}})
        s = json.dumps(resp, allow_nan=False, sort_keys=True)
        rec.update(ok=True, hash=hashlib.md5(s.encode()).hexdigest(), metric=p["metric"], date=p["date"], kinds={c["name"]: c["kind"] for c in p["columns"]}, rows=p["rows"], kpis=p["kpis"][:4])
        if p["date"] and p["metric"]:
            try:
                f = A.clean(A.forecast(df, p["date"], p["metric"], 6)); json.dumps(f, allow_nan=False); fy = f["forecast"]["y"]
                rec["fc"] = "ok"; rec["fc_null"] = any(v is None for v in fy + f["forecast"]["lower"] + f["forecast"]["upper"]); rec["fc_neg"] = (min(f["history"]["y"]) >= 0 and min(fy) < 0)
            except ValueError as e: rec["fc"] = "ValueError:" + str(e)[:60]
            except Exception as e: rec["fc"] = f"{type(e).__name__}:{str(e)[:80]}"
    except ValueError as e: rec.update(ok=False, err="ValueError:" + str(e)[:80])
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]; rec.update(ok=False, err=f"{type(e).__name__}:{str(e)[:90]}", at=f"{tb.filename.split('/')[-1]}:{tb.lineno}")
    out[seed] = rec
json.dump(out, open(sys.argv[1], "w"), indent=0, default=str)
print("done", len(out), "ok:", sum(1 for r in out.values() if r["ok"]))
