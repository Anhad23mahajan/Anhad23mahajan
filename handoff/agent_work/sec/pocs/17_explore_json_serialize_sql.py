import duckdb, json
con = duckdb.connect(":memory:")

def dump(sql):
    r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    d = json.loads(r)
    print(json.dumps(d, indent=1)[:4000])

print("### simple select ###")
dump("select * from data")
