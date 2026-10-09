import sys, threading, gc
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as llm
import pandas as pd

df = pd.DataFrame({"a": list(range(1000))})
start_threads = threading.active_count()
print("threads before:", start_threads)

# normal fast queries (timer cancelled before firing)
for i in range(20):
    llm.run_sql(df, "select count(*) from data", timeout=5)
print("threads after 20 fast queries:", threading.active_count())

# queries that actually time out (timer DOES fire)
for i in range(5):
    try:
        llm.run_sql(df, "select count(*) from range(1000000000000)", timeout=1)
    except Exception as e:
        pass
import time; time.sleep(0.5)
print("threads after 5 timed-out queries:", threading.active_count())
gc.collect()
print("threads after gc.collect():", threading.active_count())
