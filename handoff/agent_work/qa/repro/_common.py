import sys, os, warnings, io, pathlib
sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get("LUMEN_DIR", "/home/user/Anhad23mahajan/lumen"))
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
from app import analytics as A, llm
DATA = pathlib.Path("/home/user/work/qa/fixtures/data")
def load(name): return A.load_df((DATA / name).read_bytes(), name)
def analyse(df):
    p = A.profile(df); return p, A.insights(df, p), A.starter_charts(df, p)
def csv_df(text, name="x.csv"): return A.load_df(text.encode() if isinstance(text, str) else text, name)
def hdr(t): print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)
print("pandas", pd.__version__, "numpy", np.__version__)
