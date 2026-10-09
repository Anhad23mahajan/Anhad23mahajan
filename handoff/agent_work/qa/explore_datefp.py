import sys, warnings
sys.dont_write_bytecode = True
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import pandas as pd, random
from app import analytics as A
warnings.simplefilter("ignore")
random.seed(1)
cases = {
 "version 1.2.3": lambda i: f"{1+i%3}.{i%10}.{i%7}",
 "version v2.10.1": lambda i: f"v{1+i%3}.{i%10}.{i%7}",
 "ratio 3/4": lambda i: f"{1+i%9}/{2+i%9}",
 "score 10-12": lambda i: f"{1+i%9}-{2+i%9}",
 "range 5-10": lambda i: f"{5+i%5}-{10+i%5}",
 "time 10:30": lambda i: f"{i%24}:{(i*7)%60:02d}",
 "quarter Q1-2025": lambda i: f"Q{1+i%4}-2025",
 "FY2025": lambda i: f"FY{2020+i%6}",
 "quarter 2025Q1": lambda i: f"{2020+i%6}Q{1+i%4}",
 "month-year Jan-25": lambda i: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i%12] + "-25",
 "month name only": lambda i: ["January","February","March","April","May","June","July","August","September","October","November","December"][i%12],
 "month abbr only": lambda i: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i%12],
 "weekday": lambda i: ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][i%7],
 "weekday abbr": lambda i: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i%7],
 "year-month 2025-03": lambda i: f"{2020+i%6}-{1+i%12:02d}",
 "week 2025-W03": lambda i: f"2025-W{1+i%52:02d}",
 "sku A-12": lambda i: f"A-{10+i%80}",
 "phone 555-1234": lambda i: f"555-{1000+i*7%9000}",
 "zip+4": lambda i: f"{10000+i}-{1000+i%9000}",
 "decimal text 12.5": lambda i: f"{i%90}.{i%10}",
 "short code 12.03": lambda i: f"{1+i%12}.{1+i%28:02d}",
 "ip": lambda i: f"192.168.{i%255}.{i%200}",
 "name with 3 letters+digits": lambda i: f"Donor {i}",
 "name Mar/May/Jun-like": lambda i: random.choice(["May","June","March","Mark","Mary","Jan","Jun","Dec"]),
 "hyphen id 2024-001": lambda i: f"2024-{i+1:03d}",
 "invoice INV-2024-0012": lambda i: f"INV-2024-{i:04d}",
}
print("pandas", pd.__version__)
for name, f in cases.items():
    df = pd.DataFrame({"label": [f(i) for i in range(60)], "amount": range(60)})
    out = A.preprocess_df(df)
    k = A.kind(out["label"]); ex = str(out["label"].iloc[1])[:19]
    flag = "  <-- FALSE DATE" if k == "date" else ""
    print(f"{name:28s} -> {k:9s} e.g. {ex}{flag}")
