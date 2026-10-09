import duckdb, json
con = duckdb.connect(":memory:")
try: con.execute("SELECT st_astext(st_point(1,2))")
except Exception as e: print("default st_point msg:\n", str(e)[:600], "\n")
print("=== json_serialize_sql (needs bundled json ext) ===")
def js(sql):
    return json.loads(con.execute("SELECT json_serialize_sql(?)", [sql]).fetchone()[0])
for sql in ["SELECT a, sum(b) FROM data GROUP BY a", "SELECT * FROM read_csv('/etc/passwd')", "SELECT * FROM data d JOIN (SELECT 1) s ON true",
            "PRAGMA database_list", "COPY (SELECT 1) TO 'x'", "SELECT 1; SELECT 2", "WITH c AS (SELECT * FROM data) SELECT * FROM c", "this is not sql", "FROM data SELECT x",
            "SELECT * FROM glob('*')", "SELECT (SELECT max(x) FROM other) FROM data", "SELECT * FROM 'file.csv'"]:
    try:
        j = js(sql)
        if j.get("error"):
            print(f" {sql[:45]!r:50s} -> ERROR {j.get('error_type')}: {str(j.get('error_message'))[:70]}")
        else:
            st = j["statements"]; node = st[0]["node"]
            ft = node.get("from_table", {})
            def tables(n, out):
                if isinstance(n, dict):
                    if n.get("type") in ("BASE_TABLE","TABLE_FUNCTION","SUBQUERY","JOIN","EXPRESSION_LIST","PIVOT","SHOWREF","COLUMN_DATA","CTE"): out.append((n["type"], n.get("table_name") or (n.get("function",{}) or {}).get("function_name")))
                    for v in n.values(): tables(v, out)
                elif isinstance(n, list):
                    for v in n: tables(v, out)
            out=[]; tables(j, out)
            print(f" {sql[:45]!r:50s} -> ok nstmts={len(st)} node.type={node.get('type')} refs={out}")
    except Exception as e:
        print(f" {sql[:45]!r:50s} -> EXC {type(e).__name__}: {str(e).splitlines()[0][:80]}")
print("json_deserialize_sql roundtrip:", con.execute("SELECT json_deserialize_sql(json_serialize_sql('SELECT 1 AS a'))").fetchone())
# with ext=false still works?
c2 = duckdb.connect(":memory:"); c2.execute("SET enable_external_access=false"); c2.execute("SET lock_configuration=true")
print("json_serialize_sql under ext=false+lock:", c2.execute("SELECT json_serialize_sql('SELECT 1')").fetchone()[0][:60])
print("extract_statements under ext=false+lock:", [s.type.name for s in c2.extract_statements("select 1")])
