"""
hardened_llm_snippet.py -- drop-in replacement for the `guard()` / `run_sql()`
pair in /home/user/Anhad23mahajan/lumen/app/llm.py.

Everything else in llm.py (MODELS, _json, answer, narrate, schema_text) is
untouched and still imports/calls `guard` and `run_sql` by the same names and
signatures, so this is a true drop-in: copy the two functions below (plus the
small amount of supporting code) over the existing ones in app/llm.py.

WHAT CHANGED AND WHY (full detail + PoCs in REPORT.md):

1. guard() is now AST-based (DuckDB's own `json_serialize_sql`), not a
   keyword-blocklist regex. The regex was bypassed (verified): any blocked
   keyword can be rebuilt at *runtime* with replace()/concat/chr() and run
   through DuckDB's `query()` / `query_table()` table functions, which are
   themselves not in the blocklist:

     select * from query(replace('select * from duck#db_settings()', '#', ''))

   ^ this one line, sent through the SHIPPED guard()+run_sql(), executes and
   returns the full DuckDB configuration (memory_limit, temp_directory,
   secret_directory, server filesystem paths, ...). See pocs/02-04_*.py.
   A keyword blocklist can never close this class of bug, because the
   attacker only needs ONE escape hatch (query/query_table) that isn't on the
   list, and can hide any other keyword from the regex that way. The fix asks
   DuckDB's parser what the query *structurally is*, instead of pattern-
   matching the characters of the request: it allow-lists "a single SELECT
   whose only table sources are `data` and its own CTEs, with no table-valued
   function anywhere in the tree" -- which query()/query_table()/read_csv/...
   all fail by construction, regardless of how their string arguments were
   built, because the AST node type ("TABLE_FUNCTION") is fixed at parse
   time, before any runtime string-building happens.

2. The regex also had real false positives (verified): a column value of
   'Copy' or 'Drop shipping', or a note containing a literal ';', is rejected
   by the shipped guard even though it is completely safe. guard_v2 has none
   of these false positives (string literals/identifiers are parsed as what
   they are, not pattern-matched) -- see test_guard_v2.py's BENIGN cases.

3. run_sql()'s DuckDB sandbox settings are KEPT AS-IS. Testing found them to
   be the one layer that holds up even under direct, deliberate misuse:
     - enable_external_access=false blocks read_csv/read_text/parquet_scan/
       httpfs-autoinstall/etc. at the engine level (independent of guard()),
       AND (not documented, verified by testing) it also disables DuckDB's
       Python "replacement scan" feature -- so even if some future SQL made
       it past guard() and referenced a bare Python variable name, it could
       not be resolved. This is why goal 2 (reading app.main.SESSIONS or
       another tenant's DataFrame through replacement scans) came back
       negative: python_scan_all_frames defaults to false in duckdb 1.5.6
       (scans only the frame that calls .execute(), which is run_sql's own
       frame in app.llm, not app.main), AND even with BOTH settings
       deliberately misconfigured back to their enable-everything defaults,
       SESSIONS is a plain dict, which DuckDB explicitly refuses as a
       replacement-scan source (only DataFrame/Arrow/numpy are accepted).
     - lock_configuration=true really does prevent re-enabling
       enable_external_access afterwards, verified directly and via query().
   Recommendation: keep both settings, and additionally set
   python_enable_replacements=false explicitly (belt-and-suspenders -- do not
   rely on the undocumented side effect of enable_external_access alone,
   in case a future DuckDB version decouples them). Memory/thread settings
   are added below for goal 3's findings (memory_limit does NOT bound a
   single `repeat()` call's allocation -- verified, see pocs/08_*.py -- so a
   lower memory_limit does not fully substitute for the timeout; threads=1
   plus a modest memory_limit meaningfully shrinks the blast radius of a
   single request without breaking the app's own workload).
"""
from __future__ import annotations

import json
import re
import threading

import duckdb
import pandas as pd

ALLOWED_SCHEMAS = {"", "main", "memory", "system"}
ALLOWED_CATALOGS = {"", "main", "memory", "system", "temp"}
DENIED_FROM_KINDS = {"TABLE_FUNCTION", "SHOW_REF", "PIVOT_REF"}
DENIED_SCALAR_FUNCS = {
    "current_setting", "current_database", "current_schema", "current_catalog",
    "version", "current_query", "getenv", "getvariable",
}
DENIED_FUNC_NAME_RE = re.compile(
    r"^(read_|write_|parquet_|duckdb_|pg_|pragma_|iceberg_|delta_|sniff_csv$|glob$|query$|query_table$)",
    re.I,
)
MAX_SQL_LEN = 8_000

_local = threading.local()


def _parser_conn() -> duckdb.DuckDBPyConnection:
    con = getattr(_local, "con", None)
    if con is None:
        con = duckdb.connect(":memory:")
        con.execute("SET enable_external_access=false")
        con.execute("SET lock_configuration=true")
        _local.con = con
    return con


def _collect_cte_names(node, names: set) -> None:
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


def _walk(node, allowed_tables: set) -> None:
    if isinstance(node, dict):
        t = node.get("type")
        if t == "BASE_TABLE":
            schema = (node.get("schema_name") or "").lower()
            catalog = (node.get("catalog_name") or "").lower()
            name = (node.get("table_name") or "").lower()
            if schema not in ALLOWED_SCHEMAS or catalog not in ALLOWED_CATALOGS:
                raise ValueError("The query reads from a schema/catalog that isn't allowed.")
            if name not in allowed_tables:
                raise ValueError("The query reads from a table that isn't allowed. Only `data` (and its own CTEs) may be queried.")
        elif isinstance(t, str) and t in DENIED_FROM_KINDS:
            raise ValueError("The query uses a table function or special reference that isn't allowed.")

        fname = node.get("function_name")
        if isinstance(fname, str):
            low = fname.lower()
            if low in DENIED_SCALAR_FUNCS or DENIED_FUNC_NAME_RE.match(low):
                raise ValueError(f"The function `{fname}` isn't allowed.")

        for v in node.values():
            _walk(v, allowed_tables)
    elif isinstance(node, list):
        for item in node:
            _walk(item, allowed_tables)


def guard(sql: str) -> str:
    """Allow exactly one read-only SELECT over table `data` (and its own
    CTEs). Validated structurally via DuckDB's own parser, not by pattern-
    matching keywords in the SQL text -- see module docstring for why."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Empty query.")
    if len(sql) > MAX_SQL_LEN:
        raise ValueError("Query is too long.")

    con = _parser_conn()
    try:
        raw = con.execute("select json_serialize_sql(?)", [sql]).fetchone()[0]
    except Exception as e:
        raise ValueError(f"Could not parse query: {e}") from e

    doc = json.loads(raw)
    if doc.get("error"):
        # DuckDB's serializer itself rejects anything that isn't a SELECT:
        # INSERT/UPDATE/DELETE/CREATE/ATTACH/COPY/PRAGMA/SET/CALL/INSTALL/
        # LOAD/VACUUM/EXPORT/IMPORT/... all land here, string-aware (no
        # regex false positives on ';' or keywords inside string literals).
        raise ValueError(f"Only SELECT queries are allowed ({doc.get('error_message', 'parse error')}).")

    statements = doc.get("statements") or []
    if len(statements) != 1:
        raise ValueError("Only one query is allowed.")

    node = statements[0].get("node")
    allowed = {"data"}
    _collect_cte_names(node, allowed)
    _walk(node, allowed)

    return sql.strip().rstrip(";").strip()


def run_sql(df: pd.DataFrame, sql: str, timeout: int = 10) -> pd.DataFrame:
    s = guard(sql)
    con = duckdb.connect(":memory:")
    con.register("data", df)
    con.execute("SET enable_external_access=false")
    con.execute("SET lock_configuration=false")   # must set BEFORE the options below; locked last
    # Defense in depth beyond the shipped settings (kept, see module docstring):
    con.execute("SET python_enable_replacements=false")  # don't rely on the undocumented
                                                          # external_access side effect alone
    con.execute("SET threads=2")                  # shrink one request's parallel CPU footprint
    con.execute("SET memory_limit='512MB'")       # bounds the DuckDB buffer manager; NOTE this
                                                   # does NOT bound a single huge scalar allocation
                                                   # like repeat('a', 1e9) -- verified, see
                                                   # pocs/08_memlimit_worker.py -- the interrupt
                                                   # timer below is still the real backstop for that.
    con.execute("SET lock_configuration=true")    # lock last, after all SETs above are applied
    timer = threading.Timer(timeout, con.interrupt)
    timer.start()
    try:
        return con.execute(f"SELECT * FROM ({s}) LIMIT 1000").df()
    finally:
        timer.cancel()
        con.close()
