"""BUG-10/11/12/13  non-ASCII header mangling, cp1252 euro sign, UTF-16 'Unicode text', duplicate-name collision crash.
run: /home/user/work/venv/bin/python -I r05_headers_encoding.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import *
hdr("A) Hindi / NFD-accent headers: re.sub(r'\\W+','_') treats combining marks (matras, U+0301) as non-word and replaces them")
for f in ("hindi_headers.csv", "accents_nfd.csv", "accents_nfc.csv"):
    raw = A.read_raw_df((DATA / f).read_bytes(), f); df = A.preprocess_df(raw.copy()); print(f"{f:20s} raw={list(raw.columns)} -> {list(df.columns)}")
hdr("B) cp1252 file (Excel on Windows 'CSV (Comma delimited)') with a euro sign: decoded as latin-1 so EUR becomes control char U+0080")
raw = (DATA / "cp1252_euro.csv").read_bytes(); print("bytes:", raw[:60]); df = load("cp1252_euro.csv"); print("amount dtype:", df.amount.dtype, "sample:", repr(df.amount.iloc[0]), "-> column left as text, metric =", A.profile(df)["metric"])
hdr("C) UTF-16 tab-separated 'Unicode Text' export from Excel")
try: load("utf16_tab.txt.csv"); print("loaded OK")
except Exception as e: print("REJECTED:", type(e).__name__, e)
hdr("D) duplicate header names that collide after cleaning: 'amount,amount,Amount ,AMOUNT!'")
try: load("edge_dup_cols.csv"); print("loaded OK")
except Exception as e: print("CRASH:", type(e).__name__, e)
hdr("E) mixed UTC offsets inside one column (DST change, e.g. -0500 then -0400) rejects the whole file")
try: load("tz_mixed_offsets.csv"); print("loaded OK")
except Exception as e: print("REJECTED:", type(e).__name__, e)
