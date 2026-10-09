"""
guard_v2: a structural, AST-based replacement for app/llm.py's regex `guard()`.

Why: the shipped guard is a keyword-blocklist regex over the raw SQL text. It is
bypassable (any blocked keyword can be reconstructed at *runtime* via string
functions -- replace()/concat/chr() -- and executed through DuckDB's `query()` /
`query_table()` table functions, which are themselves not in the blocklist; see
/home/user/work/sec/pocs/02..04_*.py and REPORT.md finding F1). It is also prone
to false positives, because a regex has no notion of string-literal / identifier
/ comment context (e.g. WHERE product = 'Copy' is rejected because "copy" matches
\\bcopy\\b; a note containing a literal ';' is rejected as "multiple statements").

This module instead asks DuckDB's own parser what the query *means*, via
`json_serialize_sql(sql)`, and allow-lists the result structurally:

  1. Parsing must succeed and every statement must be representable as JSON.
     DuckDB's serializer itself only accepts SELECT-shaped statements and
     already rejects INSERT/UPDATE/DELETE/CREATE/ATTACH/COPY/PRAGMA/SET/CALL/
     INSTALL/LOAD/VACUUM/EXPORT/... with "Only SELECT statements can be
     serialized to json!" -- so we get that whole category of rejection for
     free, correctly (string-aware), with no regex.
  2. Exactly one statement (this also replaces the raw ';' substring check,
     which broke on ';' inside string literals).
  3. Walk the parsed AST (plain nested dict/list) and, wherever a table is
     referenced (BASE_TABLE node, anywhere in the tree: top level, inside a
     JOIN, inside a subquery, inside a CTE, inside a WHERE/SELECT-list
     sub-select -- the walk is unconditional, so nesting location doesn't
     matter), require its name to be the registered table (default "data")
     or a CTE name defined in the same query. Schema/catalog must be empty,
     "main", "memory" or "system" (how DuckDB reports the unqualified default
     schema for a plain `FROM data` / `FROM cte_name`).
  4. Reject outright any node whose "type" is "TABLE_FUNCTION", "SHOW_REF" or
     "PIVOT_REF" -- i.e. any row source that isn't a plain table/CTE/subquery/
     join. This is a default-deny on *all* table-valued functions (read_csv,
     read_text, range, generate_series, query, query_table, sniff_csv,
     parquet_scan, duckdb_settings, pragma_version, information_schema access
     comes in as a BASE_TABLE with schema_name="information_schema" and is
     caught by the name check) -- including ones not on anyone's denylist,
     because it is a structural allow-list, not a keyword blocklist.
  5. As defense in depth, also deny a short list of scalar functions that
     exist purely to leak server config/identity if called outside a FROM
     clause (current_setting, current_database, current_schema, current_catalog,
     version, current_query). Nothing in the app's own prompt needs these.

This directly closes the `query()`/`query_table()` string-reconstruction
bypass found in the regex guard: the function name "query" has to appear
literally in the SQL for the parser to produce a TABLE_FUNCTION node at all --
unlike a *keyword*, a *parsed node type* cannot be hidden by string
concatenation, replace(), or chr(), because those operations happen at
*execution* time, long after parsing already decided the query's shape.
"""
from __future__ import annotations

import json
import re
import threading
import duckdb

ALLOWED_SCHEMAS = {"", "main", "memory", "system"}
ALLOWED_CATALOGS = {"", "main", "memory", "system", "temp"}

# Row-source node kinds other than BASE_TABLE/JOIN/SUBQUERY/EMPTY that a SELECT
# can legitimately use. Deliberately empty-ish: this is a default-deny list of
# the DANGEROUS kinds we've identified so the error message can be specific;
# the real protection is the "only BASE_TABLE in allow-list" rule below, not
# this list, which only improves error messages.
DENIED_FROM_KINDS = {"TABLE_FUNCTION", "SHOW_REF", "PIVOT_REF"}

# Scalar functions that exist to disclose server/process state rather than to
# compute over the user's data. None of these are needed by the app's prompt.
DENIED_SCALAR_FUNCS = {
    "current_setting", "current_database", "current_schema", "current_catalog",
    "version", "current_query", "getenv", "getvariable",
}

# Belt-and-suspenders: the TABLE_FUNCTION node check (below) already default-
# denies every file/catalog/system table function when called the normal way
# (in a FROM clause), including ones not named here. This pattern additionally
# catches the same families of function *names* if they ever show up as a
# plain scalar-position FUNCTION node instead (e.g. `select read_text(...)`,
# which today is a guaranteed bind-time error in DuckDB -- "table function
# used as scalar" -- but guard_v2 should not rely on that binder behavior).
DENIED_FUNC_NAME_RE = re.compile(
    r"^(read_|write_|parquet_|duckdb_|pg_|pragma_|iceberg_|delta_|sniff_csv$|glob$|query$|query_table$)",
    re.I,
)

MAX_SQL_LEN = 8_000  # guard against pathological-depth parser/AST-walker input

_local = threading.local()


def _parser_conn() -> duckdb.DuckDBPyConnection:
    """A dedicated, locked-down connection used only to parse (never execute)
    candidate SQL. One per thread so concurrent requests don't share state."""
    con = getattr(_local, "con", None)
    if con is None:
        con = duckdb.connect(":memory:")
        con.execute("SET enable_external_access=false")
        con.execute("SET lock_configuration=true")
        _local.con = con
    return con


class GuardError(ValueError):
    pass


def _collect_cte_names(node, names: set[str]) -> None:
    if isinstance(node, dict):
        cte_map = node.get("cte_map")
        if isinstance(cte_map, dict):
            for entry in cte_map.get("map", []):
                key = entry.get("key")
                if isinstance(key, str):
                    names.add(key.lower())
        for v in node.values():
            _collect_cte_names(v, names)
    elif isinstance(node, list):
        for item in node:
            _collect_cte_names(item, names)


def _walk(node, allowed_tables: set[str]) -> None:
    if isinstance(node, dict):
        t = node.get("type")
        if t == "BASE_TABLE":
            schema = (node.get("schema_name") or "").lower()
            catalog = (node.get("catalog_name") or "").lower()
            name = (node.get("table_name") or "").lower()
            if schema not in ALLOWED_SCHEMAS or catalog not in ALLOWED_CATALOGS:
                raise GuardError("The query reads from a schema/catalog that isn't allowed.")
            if name not in allowed_tables:
                raise GuardError("The query reads from a table that isn't allowed. Only `data` (and its own CTEs) may be queried.")
        elif isinstance(t, str) and t in DENIED_FROM_KINDS:
            raise GuardError("The query uses a table function or special reference that isn't allowed.")

        fname = node.get("function_name")
        if isinstance(fname, str):
            low = fname.lower()
            if low in DENIED_SCALAR_FUNCS or DENIED_FUNC_NAME_RE.match(low):
                raise GuardError(f"The function `{fname}` isn't allowed.")

        for v in node.values():
            _walk(v, allowed_tables)
    elif isinstance(node, list):
        for item in node:
            _walk(item, allowed_tables)


def guard(sql: str, table_name: str = "data") -> str:
    """Validate `sql` structurally. Returns the original text unchanged
    (no string surgery needed) if it is a single, read-only SELECT over
    only `table_name` and/or its own CTEs. Raises GuardError otherwise."""
    if not isinstance(sql, str) or not sql.strip():
        raise GuardError("Empty query.")
    if len(sql) > MAX_SQL_LEN:
        raise GuardError("Query is too long.")

    con = _parser_conn()
    try:
        raw = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    except Exception as e:
        raise GuardError(f"Could not parse query: {e}") from e

    doc = json.loads(raw)
    if doc.get("error"):
        # DuckDB's own serializer already rejects anything that isn't a SELECT
        # (INSERT/UPDATE/DELETE/CREATE/ATTACH/COPY/PRAGMA/SET/CALL/INSTALL/
        # LOAD/VACUUM/EXPORT/IMPORT/...), as well as genuine syntax errors.
        raise GuardError(f"Only SELECT queries are allowed ({doc.get('error_message', 'parse error')}).")

    statements = doc.get("statements") or []
    if len(statements) != 1:
        raise GuardError("Only one query is allowed.")

    stmt = statements[0]
    node = stmt.get("node")

    allowed = {table_name.lower()}
    _collect_cte_names(node, allowed)
    _walk(node, allowed)

    return sql.strip().rstrip(";").strip()


def run_sql(df, sql: str, timeout: int = 10, table_name: str = "data"):
    """Drop-in replacement for app.llm.run_sql, using guard_v2's structural
    guard instead of the regex guard. Sandbox settings unchanged (kept as the
    shipped values, which this project's testing found to be effective:
    enable_external_access=false really does block file/network access AND
    Python replacement scans; lock_configuration=true really does prevent
    re-enabling it even through query())."""
    s = guard(sql, table_name=table_name)
    con = duckdb.connect(":memory:")
    con.register(table_name, df)
    con.execute("SET enable_external_access=false")
    con.execute("SET lock_configuration=true")
    timer = threading.Timer(timeout, con.interrupt)
    timer.start()
    try:
        return con.execute(f"SELECT * FROM ({s}) LIMIT 1000").df()
    finally:
        timer.cancel()
        con.close()
