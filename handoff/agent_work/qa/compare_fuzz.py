import json, sys, collections
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
print("ok pd3:", sum(r["ok"] for r in a.values()), "/", len(a), "| ok pd2:", sum(r["ok"] for r in b.values()), "/", len(b))
diff = [k for k in a if a[k] != b[k]]
print("seeds with any difference:", len(diff))
cat = collections.Counter()
for k in diff:
    x, y = a[k], b[k]
    if x["ok"] != y["ok"]: cat["ok-status differs"] += 1
    elif not x["ok"]: cat["both fail, message differs"] += 1
    else:
        for f in ("metric", "date", "kinds", "rows", "kpis", "fc", "fc_null", "fc_neg"):
            if x.get(f) != y.get(f): cat[f] += 1
        if all(x.get(f) == y.get(f) for f in ("metric", "date", "kinds", "rows", "kpis", "fc", "fc_null", "fc_neg")): cat["only payload hash differs"] += 1
print(dict(cat))
for k in diff[:25]:
    x, y = a[k], b[k]; print("seed", k, "\n   pd3:", {f: x.get(f) for f in x if f not in ("hash",)}, "\n   pd2:", {f: y.get(f) for f in y if f not in ("hash",)})
print("\nfailure types (pd3):")
for e, n in collections.Counter((r.get("err") or "")[:100] + " @" + r.get("at", "") for r in a.values() if not r["ok"]).most_common(20): print(f"  {n:3d} {e}")
print("\nforecast outcomes (pd3):", collections.Counter((r.get("fc") or "-")[:60] for r in a.values() if r["ok"]).most_common(12))
print("forecast with null/NaN in output:", sum(1 for r in a.values() if r.get("fc_null")), "| forecast negative for non-negative history:", sum(1 for r in a.values() if r.get("fc_neg")))
