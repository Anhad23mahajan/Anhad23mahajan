import subprocess, time, os, sys, json, io, random, datetime, urllib.request, psutil
env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PORT="8123", MALLOC_ARENA_MAX="2")
env.pop("GEMINI_API_KEY",None)
p=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8123"],cwd="lumen_copy",env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def rss():
    pr=psutil.Process(p.pid); return pr.memory_info().rss/1e6
def call(path,data=None,ctype="application/json",method="POST"):
    req=urllib.request.Request("http://127.0.0.1:8123"+path,data=data,method=method,headers={"Content-Type":ctype} if data is not None else {})
    try:
        with urllib.request.urlopen(req,timeout=120) as r: return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
for _ in range(60):
    try:
        if call("/api/health",method="GET")[0]==200: break
    except Exception: time.sleep(0.5)
print("after start RSS MB", round(rss()))
s,b=call("/api/demo",data=b"{}"); print("demo",s,len(b),"RSS",round(rss()))
sid=json.loads(b)["session_id"]; prof=json.loads(b)["profile"]
print("date col",prof.get("date"),"metric",prof.get("metric"))
s,b=call("/api/forecast",data=json.dumps({"session_id":sid,"date_col":prof["date"],"value_col":prof["metric"],"periods":6}).encode()); print("forecast",s,"RSS",round(rss()))
# multipart upload helper
def upload(csv_bytes,name="data.csv"):
    bd="----x"
    body=(f"--{bd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\nContent-Type: text/csv\r\n\r\n").encode()+csv_bytes+f"\r\n--{bd}--\r\n".encode()
    return call("/api/upload",data=body,ctype=f"multipart/form-data; boundary={bd}")
def mkcsv(n):
    random.seed(1); d0=datetime.date(2020,1,1); out=io.StringIO(); out.write("date,region,product,units,revenue,cost\n")
    for i in range(n):
        d=d0+datetime.timedelta(days=i%1500); out.write(f"{d},R{random.randint(1,8)},P{random.randint(1,40)},{random.randint(1,50)},{random.random()*500:.2f},{random.random()*300:.2f}\n")
    return out.getvalue().encode()
for n in (400000,690000):
    c=mkcsv(n); s,b=upload(c); print("upload rows",n,"size MB",round(len(c)/1e6,1),"status",s,"RSS",round(rss()), "peak?")
    if s==200:
        sid=json.loads(b)["session_id"]; pr=json.loads(b)["profile"]
        s2,_=call("/api/forecast",data=json.dumps({"session_id":sid,"date_col":pr["date"],"value_col":pr["metric"],"periods":6}).encode()); print("  forecast",s2,"RSS",round(rss()))
    else: print(b[:200])
hw=[l for l in open(f"/proc/{p.pid}/status") if l.startswith(("VmHWM","VmRSS"))]
print("".join(hw))
p.terminate()
