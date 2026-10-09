import duckdb
con = duckdb.connect(":memory:")
def check(sql):
    try:
        r = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
        import json; d = json.loads(r)
        print(sql, "->", "error" if d.get("error") else f"OK ({len(d['statements'])} stmt)", d.get("error_message",""))
    except Exception as e:
        print(sql, "-> EXC", type(e).__name__, e)

for s in ["ATTACH ':memory:' as x", "COPY data TO '/tmp/x.csv'", "CREATE TABLE t AS SELECT 1",
          "INSERT INTO data VALUES (1)", "DELETE FROM data", "UPDATE data SET a=1",
          "EXPORT DATABASE '/tmp/x'", "CALL pragma_version()", "DESCRIBE data", "SHOW TABLES",
          "select 1;", "select 1;;", "select 1 -- trailing comment",
          "select * from data where note = 'a;b'",  # semicolon inside string literal -> must be ONE statement
          "VACUUM", "LOAD 'httpfs'", "INSTALL httpfs", "SET GLOBAL threads=1",
          "select 1; select 2 --real second stmt should be 2 statements"]:
    check(s)
