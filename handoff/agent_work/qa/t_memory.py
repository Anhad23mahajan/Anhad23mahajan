import sys, os, resource
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
from app import analytics as A
import pandas as pd
print("pandas", pd.__version__)
raw = open("/home/user/work/qa/fixtures/data/big_200k.csv", "rb").read()
df = A.preprocess_df(A.read_raw_df(raw, "x.csv"))
mb = df.memory_usage(deep=True).sum() / 2**20
print(f"processed df (200k rows x 5 cols): {mb:.0f} MB deep; x51 sessions = {51*mb:.0f} MB (processed only; raw frame is garbage collected)")
print(df.dtypes.to_dict())
