import json, sys
r = json.load(open(sys.argv[1])); pats = sys.argv[2:]
for f, x in r.items():
    if pats and not any(p in f for p in pats): continue
    print("=" * 110); print(f, "| status", x.get("status"), "| t=", x.get("upload_secs"), "| size", x["size"])
    if "summary" not in x:
        print("   ", x.get("detail") or x.get("json_error") or x.get("upload")); continue
    s = x["summary"]
    print(f"  rows={s['rows']} (raw {s['raw_total_rows']}) ncols={s['ncols']} metric={s['metric']} date={s['date']} date_cols={s['date_cols']}")
    print(f"  metric_cols={s['metric_cols'][:8]} cat_cols={s['cat_cols']} id_like={s['id_like']}")
    print(f"  kinds={s['kinds'] if s['ncols']<=12 else '(many)'}")
    for k in s["kpis"]: print("  KPI", {a: (round(b, 2) if isinstance(b, float) else b) for a, b in k.items()})
    for i in s["insights"]: print("  INS", i[0], "|", i[1], "|", i[2][:170])
    print("  SUM:", s["narrative"]["summary"][:250])
    for c in s["charts"]: print("  CHART", c)
    if x.get("bad_text"): print("  !!BAD_TEXT", x["bad_text"])
    if x.get("bad_preview_cells"): print("  !!bad preview cells", x["bad_preview_cells"])
    print("  proc_rows", s["proc_rows"][:1])
    if "fc" in x:
        c = x["fc"]; print(f"  FC {c['freq']} n={c['hist_n']} last={c['hist_last']} y={c['fc_y']} lo={c['lo'][:2]} hi={c['hi'][:2]} ok={c['interval_ok']} neg={c['neg_forecast']} | {c['note'][:120]}")
    elif "fc_status" in x: print("  FC FAIL", x["fc_status"], x.get("fc_detail"), x.get("fc_json_error"))
