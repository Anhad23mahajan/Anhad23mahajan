"""Where does the time go for a 200k-row upload? usage: profile_upload.py <venv-python> file"""
import sys, time, cProfile, pstats, io
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
sys.dont_write_bytecode = True
from app import analytics as A
raw = open(sys.argv[1], "rb").read()
t = time.time(); df = A.read_raw_df(raw, "x.csv"); print("read_raw_df", round(time.time() - t, 2))
t = time.time(); pdf = A.preprocess_df(df); print("preprocess_df", round(time.time() - t, 2))
pr = cProfile.Profile(); pr.enable(); A.preprocess_df(df); pr.disable()
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(14); print(s.getvalue()[:3500])
t = time.time(); p = A.profile(pdf); print("profile", round(time.time() - t, 2))
t = time.time(); f = A.insights(pdf, p); print("insights", round(time.time() - t, 2))
t = time.time(); A.starter_charts(pdf, p); print("charts", round(time.time() - t, 2))
t = time.time(); A.df_to_preview(pdf); A.df_to_preview(df); print("previews", round(time.time() - t, 2))
