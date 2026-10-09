import sys, time, resource, io
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.analytics as A

ncols = int(sys.argv[1]) if len(sys.argv) > 1 else 50_000
nrows = int(sys.argv[2]) if len(sys.argv) > 2 else 5

header = ",".join(f"c{i}" for i in range(ncols))
row = ",".join(str(i % 10) for i in range(ncols))
csv_text = header + "\n" + ("\n".join([row] * nrows)) + "\n"
raw = csv_text.encode()
print(f"synthetic CSV: {ncols} cols x {nrows} rows, raw size = {len(raw)/1e6:.2f} MB (cap is 25MB)")

t0 = time.time()
df = A.load_df(raw, "wide.csv")
t1 = time.time()
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
mem = df.memory_usage(deep=True).sum() / 1e6
print(f"load_df (read+preprocess) time: {t1-t0:.2f}s")
print(f"resulting shape: {df.shape}")
print(f"DataFrame memory_usage(deep=True): {mem:.1f} MB")
print(f"process peak RSS: {peak:.1f} MB")
print(f"amplification vs raw upload: {peak/(len(raw)/1e6):.1f}x")
