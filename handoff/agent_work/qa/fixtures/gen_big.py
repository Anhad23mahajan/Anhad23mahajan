"""Large-file fixtures. Output: data/big_*"""
import numpy as np, pandas as pd, pathlib
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
MAX = 25 * 1024 * 1024
rng = np.random.default_rng(99)

def frame(n, note_len=0):
    d = pd.Timestamp("2023-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D")
    df = pd.DataFrame({"date": d.strftime("%Y-%m-%d"), "donor": [f"Donor {i}" for i in rng.integers(1, 50000, n)],
                       "amount": np.round(rng.lognormal(3.5, 1.0, n), 2), "campaign": rng.choice(["A", "B", "C", "D"], n),
                       "channel": rng.choice(["Online", "Cheque", "Cash"], n)})
    if note_len: df["note"] = "x" * note_len
    return df.sort_values("date")

frame(200_000).to_csv(OUT / "big_200k.csv", index=False)
frame(250_000).to_csv(OUT / "big_250k_truncation.csv", index=False)

# exact-size files: build rows, then pad the final 'note' to hit target bytes exactly
def exact(name, target, note_len=100):
    df = frame(int(target / (45 + note_len)), note_len)
    txt = df.to_csv(index=False)
    b = txt.encode()
    while len(b) > target - 200:           # trim rows until just under
        df = df.iloc[:-1000]; b = df.to_csv(index=False).encode()
    pad = target - len(b) - len(b"2024-01-01,Donor 1,1.0,A,Online,") - 1
    b += b"2024-01-01,Donor 1,1.0,A,Online," + b"y" * pad + b"\n"
    assert len(b) == target, (len(b), target)
    (OUT / name).write_bytes(b)
exact("big_under_25mb_wide.csv", MAX)          # exactly 25 MiB: allowed (check is  >)
exact("big_over_25mb.csv", MAX + 1)            # 1 byte over
print({p.name: p.stat().st_size for p in OUT.glob("big_*")})

# xlsx 100k rows
from openpyxl import Workbook
wb = Workbook(write_only=True); ws = wb.create_sheet("data"); df = frame(100_000)
ws.append(list(df.columns))
for r in df.itertuples(index=False): ws.append([pd.Timestamp(r[0]).to_pydatetime(), r[1], r[2], r[3], r[4]])
wb.save(OUT / "big_100k.xlsx")
print((OUT / "big_100k.xlsx").stat().st_size)
