import duckdb, json
con = duckdb.connect(":memory:")
def dump(sql, n=1500):
    r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    d = json.loads(r)
    print(json.dumps(d)[:n]); print()

print("aggregate+window:"); dump("select sum(x) over (partition by y order by z) from data")
print("case + date_trunc:"); dump("select date_trunc('month', d), case when a>1 then 'x' else 'y' end from data")
print("scalar current_setting in select list:"); dump("select current_setting('memory_limit') as x")
print("read_text as scalar (not FROM)?:")
try:
    dump("select read_text('/etc/hostname') as x")
except Exception as e:
    print("ERR", e)
print("invalid syntax:")
r = con.execute("select json_serialize_sql(?)", ["select * from where"]).fetchone()[0]
print(r[:300])
print("explain stmt:")
r = con.execute("select json_serialize_sql(?)", ["explain select 1"]).fetchone()[0]
print(r[:300])
