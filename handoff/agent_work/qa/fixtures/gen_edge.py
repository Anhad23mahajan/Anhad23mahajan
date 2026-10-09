"""Structural edge cases. Output: data/edge_*.csv"""
import numpy as np, pandas as pd, pathlib
OUT = pathlib.Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(3)
n = 120
dates = pd.date_range("2024-01-01", periods=n, freq="3D")
def w(name, text, enc="utf-8"): (OUT / name).write_bytes(text.encode(enc) if isinstance(text, str) else text)

# trailing blank rows (empty commas AND whitespace-only rows) + all-NaN column + all 'N/A' column
base = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "sales": rng.integers(100, 999, n), "empty": np.nan, "na_text": "N/A", "region": rng.choice(["N", "S"], n)})
txt = base.to_csv(index=False) + ",,,,\n,,,,\n   ,   ,   ,   ,   \n\n\n"
w("edge_trailing_blank.csv", txt)

# single column / single row / header only / one-cell
w("edge_single_col.csv", "amount\n" + "\n".join(str(int(x)) for x in rng.integers(1, 100, 50)) + "\n")
w("edge_single_col_text.csv", "name\nalice\nbob\ncarol\n")
w("edge_single_row.csv", "date,amount,region\n2025-01-31,1200,North\n")
w("edge_two_rows.csv", "date,amount,region\n2025-01-31,1200,North\n2025-02-28,900,South\n")
w("edge_header_only.csv", "date,amount,region\n")
w("edge_empty.csv", "")
w("edge_newlines_only.csv", "\n\n\n")
w("edge_binary_garbage.csv", bytes(rng.integers(0, 256, 5000, dtype=np.uint8)))
w("edge_html_page.csv", "<html><body><h1>Login</h1></body></html>")

# no numeric columns / no date column / date but no metric
pd.DataFrame({"name": [f"p{i}" for i in range(50)], "city": rng.choice(["A", "B", "C"], 50), "note": [f"free text number {i} here" for i in range(50)]}).to_csv(OUT / "edge_no_numeric.csv", index=False)
pd.DataFrame({"sku": [f"S{i}" for i in range(50)], "qty": rng.integers(1, 99, 50), "price": np.round(rng.uniform(1, 9, 50), 2)}).to_csv(OUT / "edge_no_date.csv", index=False)
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "region": rng.choice(["N", "S", "E"], n), "note": "x"}).to_csv(OUT / "edge_date_no_metric.csv", index=False)

# duplicated column names (3x) and names that differ only by case/space/punctuation
w("edge_dup_cols.csv", "date,amount,amount,Amount ,AMOUNT!\n" + "\n".join(f"2025-01-{i+1:02d},{i},{i*2},{i*3},{i*4}" for i in range(28)) + "\n")
# SQL-reserved / blocklisted column names
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "set": rng.integers(1, 9, n), "load": rng.integers(10, 99, n), "order": rng.integers(1, 5, n),
              "group": rng.choice(["a", "b", "c"], n), "update": rng.choice(["x", "y"], n), "export": rng.integers(1, 99, n), "call": rng.integers(1, 99, n)}).to_csv(OUT / "edge_reserved_cols.csv", index=False)

# 300 columns wide
wide = pd.DataFrame(rng.integers(0, 1000, (80, 300)), columns=[f"metric_{i}" for i in range(300)]); wide.insert(0, "date", pd.date_range("2024-01-01", periods=80).strftime("%Y-%m-%d"))
wide.to_csv(OUT / "edge_wide_300.csv", index=False)

# sequential id column + monotone integer id mixed with amount; negative amounts; all-zero; constant
pd.DataFrame({"id": np.arange(1, 101), "amount": rng.integers(1, 99, 100)}).to_csv(OUT / "edge_seq_id.csv", index=False)
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "profit": rng.integers(-500, 100, n)}).to_csv(OUT / "edge_negative_metric.csv", index=False)
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "amount": 0}).to_csv(OUT / "edge_all_zero.csv", index=False)
pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "amount": 5}).to_csv(OUT / "edge_constant.csv", index=False)
# huge / tiny magnitudes and inf in the data
w("edge_inf_values.csv", "date,amount\n" + "\n".join(f"2025-01-{i+1:02d},{'inf' if i==3 else '-inf' if i==5 else 'NaN' if i==7 else i*10}" for i in range(28)) + "\n")
w("edge_huge_values.csv", "date,amount\n" + "\n".join(f"2024-{(i%12)+1:02d}-{(i//12)+1:02d},{1e300 if i%7==0 else i}" for i in range(36)) + "\n")
# duplicate dates / unsorted / big gaps in months
d = pd.to_datetime(["2024-01-15", "2024-01-20", "2024-06-01", "2024-06-02", "2025-03-01", "2025-03-05", "2024-09-09", "2024-10-10", "2024-11-11", "2024-12-12", "2025-01-13", "2025-02-14"])
pd.DataFrame({"date": d.strftime("%Y-%m-%d"), "amount": rng.integers(100, 500, len(d))}).to_csv(OUT / "edge_gappy_unsorted.csv", index=False)
# quoted fields with commas/newlines, ragged rows
w("edge_ragged.csv", 'date,amount,note\n2025-01-01,10,"hello, world"\n2025-01-02,20,"multi\nline"\n2025-01-03,30\n2025-01-04,40,x,extra,more\n')
# date column with year-only values, 4 digit years
pd.DataFrame({"year": np.repeat([2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026], 3), "amount": rng.integers(100, 500, 24)}).to_csv(OUT / "edge_year_only.csv", index=False)
# non-date text with separators that look date-ish: phone/sku/version/ratio
pd.DataFrame({"sku": [f"A-{i%90+10}" for i in range(60)], "version": ["1.2.3"] * 60, "ratio": ["3/4"] * 60, "amount": rng.integers(1, 99, 60)}).to_csv(OUT / "edge_datelike_text.csv", index=False)
print("edge ok")
