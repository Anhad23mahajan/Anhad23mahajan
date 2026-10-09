import duckdb, json
con = duckdb.connect(":memory:")
def dump(sql, n=3000):
    r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    d = json.loads(r)
    print(json.dumps(d)[:n])
    print()

print("CTE:"); dump("with t as (select 1 as x) select * from t")
print("UNION:"); dump("select 1 union all select 2")
print("table function range:"); dump("select * from range(10)")
print("query():"); dump("select * from query('select 1')")
print("info schema:"); dump("select * from information_schema.tables")
print("multi-stmt:"); dump("select 1; select 2")
print("non-select (set):"); dump("SET memory_limit='1GB'")
print("pragma stmt:"); dump("PRAGMA version")
