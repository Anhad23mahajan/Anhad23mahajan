import duckdb, json
con = duckdb.connect(":memory:")
def show_from(sql):
    r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    d = json.loads(r)
    ft = d["statements"][0]["node"].get("from_table")
    print(sql, "-> from_table.type =", ft.get("type") if ft else None)

show_from("select * from data a join data b on a.x=b.x")
show_from("select * from (select * from data) t")
show_from("select * from data cross join data")
show_from("select unnest([1,2,3])")
show_from("select * from (values (1),(2)) as t(x)")
show_from("pivot data on product using sum(amount)")
