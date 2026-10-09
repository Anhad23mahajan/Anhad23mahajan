import sys, time, resource, os
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.analytics as A

path = "/home/user/work/sec/pocs/bomb.xlsx"
compressed_mb = os.path.getsize(path) / 1e6
with open(path, "rb") as f:
    raw = f.read()

t0 = time.time()
df = A.read_raw_df(raw, "bomb.xlsx")
t1 = time.time()
peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
mem_mb = df.memory_usage(deep=True).sum() / 1e6

print(f"compressed upload size: {compressed_mb:.1f} MB")
print(f"rows x cols: {df.shape}")
print(f"decompress+parse time: {t1-t0:.1f}s")
print(f"DataFrame .memory_usage(deep=True): {mem_mb:.1f} MB")
print(f"process peak RSS: {peak_mb:.1f} MB")
print(f"amplification ratio (peak_rss / compressed_upload): {peak_mb/compressed_mb:.1f}x")
print(f"extrapolated peak RSS for an exactly-25MB upload of this shape: {peak_mb/compressed_mb*25:.0f} MB")
