import sys, time
sys.path.insert(0, "/home/user/work/sec")
sys.path.insert(0, "/home/user/Anhad23mahajan/lumen")
import app.llm as old_llm
import guard_v2

sql = "select product, sum(amount) as total from data group by product order by total desc limit 30"
N = 2000

t0=time.time()
for _ in range(N): old_llm.guard(sql)
t1=time.time()
print(f"regex guard: {(t1-t0)/N*1e6:.1f} us/call")

t0=time.time()
for _ in range(N): guard_v2.guard(sql)
t1=time.time()
print(f"guard_v2 (AST): {(t1-t0)/N*1e6:.1f} us/call")
