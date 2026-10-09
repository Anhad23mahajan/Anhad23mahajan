import duckdb, json
con = duckdb.connect(":memory:")
print("extensions loaded:", [r[0] for r in con.execute("select extension_name from duckdb_extensions() where loaded").fetchall()])
print("installed(not loaded):", [r[0] for r in con.execute("select extension_name from duckdb_extensions() where installed and not loaded").fetchall()])
print("all known:", [r[0] for r in con.execute("select extension_name from duckdb_extensions()").fetchall()])

print("\n=== autoload/autoinstall ===")
for presets in ([], ["SET autoinstall_known_extensions=false"], ["SET autoinstall_known_extensions=false","SET autoload_known_extensions=false"], ["SET enable_external_access=false"]):
    c = duckdb.connect(":memory:")
    for p in presets: c.execute(p)
    for q in ["SELECT st_astext(st_point(1,2))", "SELECT * FROM read_parquet('/nonexistent.parquet')", "SELECT sqlite_version()"]:
        try: c.execute(q).fetchall(); r="ok"
        except Exception as e: r = type(e).__name__ + ": " + str(e).splitlines()[0][:110] + (" | " + str(e).splitlines()[1][:90] if len(str(e).splitlines())>1 else "")
        print(f" {str(presets)[:75]:78s} {q[:45]:46s} -> {r}")

print("\n=== extract_statements (parse-only, no execution) ===")
import duckdb as d
for sql in ["SELECT 1", "SELECT 1; DROP TABLE x", "WITH a AS (SELECT 1) SELECT * FROM a", "COPY (SELECT 1) TO 'x.csv'", "PRAGMA database_list", "SET threads=1", "INSTALL httpfs", "ATTACH 'x.db'", "EXPLAIN SELECT 1", "CALL pragma_version()", "SELECT * FROM read_csv('x')", "this is not sql", "-- c\nSELECT 1 /* x */", "VALUES (1)", "FROM data SELECT x", "SUMMARIZE SELECT 1", "DESCRIBE data", "SHOW TABLES", "PIVOT data ON x USING sum(y)"]:
    try:
        st = con.extract_statements(sql)
        print(f" {sql[:42]!r:46s} -> n={len(st)} types={[ (s.type.name) for s in st]}")
    except Exception as e:
        print(f" {sql[:42]!r:46s} -> {type(e).__name__}: {str(e).splitlines()[0][:70]}")
print("Statement attrs:", [a for a in dir(con.extract_statements('select 1')[0]) if not a.startswith('_')])
print("StatementType values:", [x for x in dir(d.StatementType) if x.isupper()])
print("module-level duckdb.extract_statements exists:", hasattr(d, "extract_statements"))
print(" module-level:", [s.type.name for s in d.extract_statements("select 1; select 2")])
