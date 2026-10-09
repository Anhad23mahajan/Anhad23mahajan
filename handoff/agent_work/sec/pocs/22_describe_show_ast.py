import duckdb, json
con = duckdb.connect(":memory:")
for sql in ["DESCRIBE data", "SHOW TABLES"]:
    r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    print(sql, "->", r[:600])
    print()
