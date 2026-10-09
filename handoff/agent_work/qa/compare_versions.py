"""Diff results_pd3.json vs results_pd2.json (ignore timings). usage: compare_versions.py [a.json b.json]"""
import json, sys
a = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results_pd3.json")); b = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "results_pd2.json"))
def norm(r):
    r = json.loads(json.dumps(r)); 
    for k in ("upload_secs", "fc_secs", "body_bytes"): r.pop(k, None)
    r.get("summary", {}).pop("proc_dtypes", None)
    return r
n = 0
for f in sorted(set(a) | set(b)):
    ra, rb = norm(a.get(f, {})), norm(b.get(f, {}))
    if ra == rb: continue
    n += 1
    print("=" * 100); print("DIFF", f)
    def walk(x, y, path=""):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)): walk(x.get(k, "<missing>"), y.get(k, "<missing>"), f"{path}.{k}")
        elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
            for i, (p, q) in enumerate(zip(x, y)): walk(p, q, f"{path}[{i}]")
        elif x != y: print(f"  {path}\n     pd3: {str(x)[:300]}\n     pd2: {str(y)[:300]}")
    walk(ra, rb)
print("files differing:", n, "of", len(set(a) | set(b)))
