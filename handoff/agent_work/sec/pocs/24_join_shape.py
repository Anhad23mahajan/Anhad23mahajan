import duckdb, json
con = duckdb.connect(":memory:")
r = con.execute("select json_serialize_sql(?)", ["select * from data a join data b on a.x=b.x"]).fetchone()[0]
d = json.loads(r)
ft = d["statements"][0]["node"]["from_table"]
print(json.dumps(ft, indent=1)[:1500])
