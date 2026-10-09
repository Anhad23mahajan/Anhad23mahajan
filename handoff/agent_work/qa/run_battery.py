"""Upload every fixture to a running Lumen server, record results.
usage: run_battery.py BASE_URL OUT.json [glob]
Strict JSON parsing (NaN/Infinity rejected), text sanity flags, forecast call, timings."""
import sys, json, re, time, pathlib, httpx, fnmatch

BASE, OUT = sys.argv[1], sys.argv[2]
PAT = sys.argv[3] if len(sys.argv) > 3 else "*"
DATA = pathlib.Path(__file__).parent / "fixtures" / "data"
BAD = re.compile(r"(?i)(?<![\w])(nan|inf|infinity|nat|none|null|undefined)(?![\w])")

def strict(body: bytes):
    def boom(c): raise ValueError(f"non-finite constant {c} in JSON body")
    return json.loads(body, parse_constant=boom)

def texts(d):
    out = []
    for i in d.get("insights", []): out += [("insight.title", i["title"]), ("insight.detail", i["detail"]), ("insight.action", i.get("action", ""))]
    n = d.get("narrative", {}); out.append(("narrative.summary", n.get("summary", "")))
    out += [("narrative.rec", r) for r in n.get("recommendations", [])]
    for k in d.get("profile", {}).get("kpis", []): out += [("kpi.label", k["label"]), ("kpi.note", str(k.get("note", "")))]
    for c in d.get("charts", []): out.append(("chart.title", c["title"]))
    out += [("question", q) for q in d.get("suggested_questions", [])]
    out += [("colname", c["name"]) for c in d.get("profile", {}).get("columns", [])]
    return out

def summarize(d):
    p = d["profile"]
    return {"rows": p["rows"], "metric": p["metric"], "date": p["date"], "date_cols": p["date_cols"], "metric_cols": p["metric_cols"], "cat_cols": p["cat_cols"],
            "kinds": {c["name"]: c["kind"] for c in p["columns"]}, "ncols": len(p["columns"]),
            "missing": {c["name"]: c["missing_pct"] for c in p["columns"] if c["missing_pct"]},
            "id_like": [c["name"] for c in p["columns"] if c.get("id_like")],
            "kpis": p["kpis"], "insights": [(i["severity"], i["title"], i["detail"]) for i in d["insights"]],
            "narrative": d["narrative"], "charts": [{"title": c["title"], "type": c["type"], "freq": c.get("freq"), "n": len(c["x"]), "x0": c["x"][:2], "xN": c["x"][-1:], "y0": c["y"][:2], "yN": c["y"][-2:]} for c in d["charts"]],
            "questions": d["suggested_questions"],
            "raw_cols": d["raw_preview"]["columns"], "raw_rows": d["raw_preview"]["rows"][:2], "raw_total_rows": d["raw_preview"]["total_rows"],
            "proc_dtypes": dict(zip(d["processed_preview"]["columns"], d["processed_preview"]["dtypes"])), "proc_rows": d["processed_preview"]["rows"][:2]}

res = {}
cli = httpx.Client(base_url=BASE, timeout=600)
for f in sorted(DATA.iterdir()):
    if not fnmatch.fnmatch(f.name, PAT): continue
    if f.name.startswith("big_") and not PAT.startswith("big_"): continue
    rec = {"file": f.name, "size": f.stat().st_size}
    t = time.time()
    try:
        r = cli.post("/api/upload", files={"file": (f.name, f.read_bytes(), "application/octet-stream")})
    except Exception as e:
        rec["upload"] = {"exc": repr(e)}; res[f.name] = rec; continue
    rec["upload_secs"] = round(time.time() - t, 2); rec["status"] = r.status_code; rec["body_bytes"] = len(r.content)
    try:
        d = strict(r.content)
    except Exception as e:
        rec["json_error"] = repr(e)[:200]; rec["body_head"] = r.text[:300]; res[f.name] = rec; print(f"{f.name:34s} {rec['status']} NON-JSON/STRICT-JSON FAIL {rec['json_error']} {rec['body_head'][:100]!r}", flush=True); continue
    if r.status_code != 200:
        rec["detail"] = d.get("detail"); res[f.name] = rec; print(f"{f.name:34s} {rec['status']} {rec['upload_secs']:6.2f}s DETAIL={rec['detail']}", flush=True); continue
    rec["summary"] = summarize(d)
    rec["bad_text"] = [(w, s[:160]) for w, s in texts(d) if BAD.search(s or "")]
    # preview cells containing nan-ish strings
    rec["bad_preview_cells"] = sum(1 for pv in ("raw_preview", "processed_preview") for row in d[pv]["rows"] for v in row if isinstance(v, str) and BAD.fullmatch(v.strip()))
    p = d["profile"]
    if p["date"] and p["metric"]:
        t = time.time()
        fr = cli.post("/api/forecast", json={"session_id": d["session_id"], "date_col": p["date"], "value_col": p["metric"], "periods": 6})
        rec["fc_secs"] = round(time.time() - t, 2); rec["fc_status"] = fr.status_code
        try:
            fd = strict(fr.content)
            if fr.status_code == 200:
                f_, h = fd["forecast"], fd["history"]
                rec["fc"] = {"freq": fd["freq"], "hist_n": len(h["x"]), "hist_last": [h["x"][-1], h["y"][-1]], "fc_x": f_["x"][:1] + f_["x"][-1:], "fc_y": f_["y"], "lo": f_["lower"], "hi": f_["upper"], "note": fd["note"],
                             "has_null": any(v is None for v in f_["y"] + f_["lower"] + f_["upper"]),
                             "interval_ok": all(l is not None and y is not None and u is not None and l <= y <= u for l, y, u in zip(f_["lower"], f_["y"], f_["upper"])),
                             "neg_forecast": any(y is not None and y < 0 for y in f_["y"]), "hist_min": min(v for v in h["y"] if v is not None)}
            else: rec["fc_detail"] = fd.get("detail")
        except Exception as e:
            rec["fc_json_error"] = repr(e)[:200]; rec["fc_head"] = fr.text[:200]
    res[f.name] = rec
    print(f"{f.name:34s} {rec['status']} {rec['upload_secs']:6.2f}s metric={p['metric']} date={p['date']}", flush=True)
json.dump(res, open(OUT, "w"), indent=1, default=str)
