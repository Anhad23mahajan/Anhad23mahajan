# Lumen technical fact-check: Gemini API, DuckDB sandbox, forecasting, competitive claims

Researched 2026-10-09 (UTC afternoon). Scripts and raw results are in `/home/user/work/research/technical_tests/` (every `[T]` below can be re-run from there). I did not edit `/home/user/Anhad23mahajan` (I imported its modules with `-B`; `git status` stayed clean).

## Source tags

- **[T]** I ran it myself in `/home/user/work/venv` (google-genai 2.29.0, duckdb 1.5.6, pandas 3.0.6, statsmodels 0.15.0, Python 3.13.16). Script named in the text.
- **[P]** Primary source I actually read (raw files in Google/DuckDB/statsmodels GitHub repos, PyPI).
- **[S]** Only a web-search excerpt or third-party page; I could not open the page. Secondary: treat as "probably true".
- **[U]** Unverified or sources conflict.

## What I could not reach (be aware when you cite this)

`ai.google.dev`, `duckdb.org`, `arxiv.org`, `learn.microsoft.com`, `otexts.com`, `tableau.com`, `metabase.com` are blocked by this sandbox's proxy or DNS (curl 403 / WebFetch ENOTFOUND). `raw.githubusercontent.com`, `github.com`, `pypi.org` and `generativelanguage.googleapis.com` work. So every statement about what an `ai.google.dev` page says comes from a search-engine excerpt of that page [S], except where I could read the same fact in a Google GitHub repo [P]. There is **no Gemini key in the sandbox, so no live generation call was made**; anything about live model behaviour is [S]/[U], not [T].

---

## 0. Corrections to make before submission (priority order)

1. **Free-tier capacity is unknown and may be tiny.** Google no longer publishes a per-model free-tier table; its rate-limits page says limits "can be viewed in Google AI Studio" and "are not guaranteed" [S]. Numbers floating around range from ~20 requests/day for a Flash-class model (one forum-derived report, plus reports of a ~90% cut in Dec 2025) to ~1,000/day for Flash-Lite [S/U]. One judge asking 5 questions makes ~11-21 Gemini calls (see 1.2). **Do not make the live demo depend on the free tier**: enable billing on the demo project with a hard budget cap (about $5 per 1,000 questions by my arithmetic: 2 calls x (1,000 input + 500 output tokens) at the 3.8 Flash introductory price of $0.75 / $3.75 per million tokens [S], ignoring thinking-token overhead), and/or add a bring-your-own-key box, a cache for the sample dataset and per-IP throttling.
2. **The privacy sentence in the README is wrong in two ways.** (a) Gemini also receives the user's question, the generated SQL and any DuckDB error text, and, on every upload (not only on questions), the column names, row count and the computed findings text (which contains category names, dates and totals). (b) "Self-host to keep data fully on your machine" is false whenever a key is configured. On the free tier Google may use prompts to improve products and human reviewers may read them. Honest wording is in section 1.6.
3. **"Files never written to disk" is false for uploads over 1 MiB.** Starlette's multipart parser spools anything above 1,048,576 bytes to a temp file [T `mini FastAPI test`: 900,000 B -> in memory, 1,100,000 B -> `_rolled=True`]. DuckDB can also spill query intermediates to `./.tmp` when a memory limit is hit [T duck4]. Either say "held in memory; large uploads may touch a temporary file that is deleted after the request" or fix both (see 2.5).
4. **The forecast band is not a 95% range.** In my backtest of 690 windows the app's band (`±1.96·sd(resid)·√h`) contained 81% of actual values [T fc_analyze3]. Either call it "likely range" or widen it (×1.5 gave 91%) or use ETS intervals (84%, 94% at ×1.5).
5. **The forecaster is worse than "repeat last value" when there are fewer than 24 periods** (32% worse, 95% CI 1.24-1.43x error) and about twice as good as naive from 24 periods up [T fc_analyze2]. The app accepts 8+. Gate it (section 3.4).
6. **Model IDs.** `gemini-3.8-flash` (what `.env.example` says) is real and GA. The code comment "3.5 Flash is the GA replacement" is stale: Google now tells people to move from 3.5 Flash to 3.8 Flash, and from 3.1 Flash-Lite to `gemini-3.5-flash-lite` [P gemini-skills migration.md]. `gemini-flash-latest` is a real alias but I cannot verify where it points today [U].
7. **Error handling has four real holes** (reproduced with stubs, [T] robust_llm.py and the stub run in section 1.5): a blocked/empty response crashes with `AttributeError: 'NoneType' ... 'strip'` and never fails over; a 429 in `llm._json` is raised instead of trying the next model (quotas are per model); an error body that merely contains the digits `404` (e.g. a project number) is misread as "model missing"; truncated JSON (`MAX_TOKENS`) raises `JSONDecodeError`.
8. **`temperature` advice has flipped.** Gemini 3.5 Flash-Lite and 3.8 Flash ignore `temperature/top_p/top_k` (Google says future models will return HTTP 400 if you send them) and Google tells Gemini 3 users to keep temperature at the default 1.0 [S + P]. Do not add `temperature=0`.
9. **Unpinned dependencies are a live risk.** `requirements.txt` has `duckdb>=1.1`, `google-genai`, `statsmodels>=0.14`, `pandas>=2.2`. DuckDB 1.5.6 was released 2026-09-28 and its post says v2.0.0 is due in October [S]; google-genai 2.29.0 came out 2026-10-07 and 2.0.0 (2026-05-07) already contained Interactions-API breaking changes [P CHANGELOG]. Pin to the versions I tested (list in section 5).
10. **Competitive claims to soften** (section 4): Power BI Copilot is not "enterprise licence" but "paid capacity, F2 or higher, about $260 a month"; free AI analysis of uploaded CSVs exists in ChatGPT Free, Claude Free and the Gemini app; "zero-config forecasts" exist in Excel, Power BI and Tableau; Vanna's repo was archived 2026-03-29; Rows shut down.

---

## 1. Gemini API

### 1.1 Which model IDs exist today (as of 2026-10-09)

| Model ID | Exists? | Status and dates | Evidence |
|---|---|---|---|
| `gemini-3.8-flash` | Yes | GA since 2026-09-02. Google's "latest Flash" and the default model in Google's own skill. No shutdown date announced. Default thinking level `medium`; `minimal` is **not** supported (returns an error). Ignores temperature/top_p/top_k. Supports structured output. Intro price $0.75 in / $3.75 out per 1M tokens through end of 2026, then $1.50 / $7.50. | [P] googleapis/python-genai CHANGELOG 2.22.0 (2026-09-02) "Added the Gemini 3.8 Flash model"; [P] gemini-cli `models.ts` `LATEST_GEMINI_FLASH_MODEL='gemini-3.8-flash'`; [P] gemini-skills `SKILL.md` "Current Models"; [S] model page + latest-model page excerpts; [S] price (third-party blogs quoting Google) |
| `gemini-3.5-flash-lite` | Yes | GA since 2026-07-21. Google: "fastest, lowest-cost 3.5 model". Default thinking `minimal`. No shutdown date announced. Google's migration target for 3.1 Flash-Lite. | [P] gemini-skills `SKILL.md` + `references/migration.md`; [P] gemini-cli `LATEST_GEMINI_FLASH_LITE_MODEL`; [S] deprecations table excerpt |
| `gemini-3.5-flash` | Yes | GA since 2026-05-19. Now an "active legacy model, migration recommended" to 3.8 Flash. No shutdown date announced; table dates are "earliest possible". | [P] migration.md; [S] deprecations excerpt |
| `gemini-3.1-flash-lite` | Yes | GA since 2026-05-07 (preview ID `-preview` already shut down). Deprecations table lists an earliest shutdown of 2027-05-07; Google recommends moving to 3.5 Flash-Lite. | [P] migration.md; [S] deprecations excerpt (row layout ambiguous: verify the 2027 date) |
| `gemini-flash-latest` | Alias exists (used in the python-genai README examples) | Where it points now is unknown. A May 2026 source said 3.5 Flash. An alias can change behaviour (thinking defaults, price) under you the night before judging. | [P] python-genai README; target [U] |
| `gemini-3.6-flash`, `gemini-3.7-flash` | Yes | GA 2026-07-21 and ~2026-08-13; both on Google's "migrate to 3.8" list. | [P] migration.md; dates [S] |
| `gemini-2.5-flash` (the comment in `llm.py`) | Yes, but dying | Gemini API earliest shutdown reported as **2026-10-16**, Vertex AI **2026-10-20**; Google's own 2026-09-18 release note says 2.5 access is limited to previous users and "not deprecated"; Google's skill file says "legacy and deprecated, never use". Sources conflict, so assume it can vanish any day. | [S] several; [P] gemini-skills |
| `gemma-4-31b-it`, `gemma-4-26b-a4b-it` | Yes, served via the Gemini API | Open-weights models. Reported free quota 1,500 req/day (single Korean note) [U]. JSON-mode/schema support unknown [U]. | [P] gemini-skills, gemini-cli constants |

Recommended list for `llm.py`: `[env GEMINI_MODEL, "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]`. Drop `gemini-flash-latest` and `gemini-3.5-flash`. Flash first (quality), Flash-Lite as the cheap, separately-metered fallback. I could not run a quality comparison without a key: do a 20-question A/B on your own key before locking the order.

### 1.2 Free tier: what is actually known

- **Which models have a free tier.** Third parties (Sept 2026) list Flash and Flash-Lite as free and Pro as paid-only since about April 2026; Google's own pricing page was not reachable [S]. Batch/Flex/Search-grounding are not free [S].
- **Per-model numbers: not published by Google any more.** The rate-limits page says limits "depend on usage tier and can be viewed in Google AI Studio", "specified rate limits are not guaranteed", limits apply **per project, not per API key**, and daily quotas reset at midnight Pacific time [S, quoted from the page by two searches].
- **What third parties claim (all [U], they disagree):** 3.1 Flash-Lite 15 RPM / 250k TPM / 1,000 RPD (Sept 2026 table); Flash-class 10-15 RPM and 250-1,500 RPD; reports that Flash-class free RPD fell from ~250 to ~20 in Dec 2025; one note that "Gemini 3.5 Flash shows 20 per day" while Gemma 4 26B/31B show 1,500 per day on the same AI Studio screen. New projects without billing can show "limit: 0".
- **Capacity arithmetic for the demo.** One upload = 1 call (`narrate`). One question = 2 calls (SQL plan + verification), up to 4 with the one allowed SQL retry. A judge who uploads and asks 5 questions makes 11-21 calls. At 20 RPD that is one judge; at 250 RPD roughly 12-22 judges a day; at 15 RPM only about 4-7 questions per minute across **everyone**, because all judges share one project key. Fallback models multiply capacity (separate per-model buckets, "limits vary by model" [S]) only if the code actually falls through on 429, which today it does not (1.5).
- **Cheaper/higher-quota option for short NL-to-SQL:** `gemini-3.5-flash-lite` (or 3.1 Flash-Lite) is the natural first choice for quota and latency; a one-table schema question is easy. Whether it matches Flash quality on your questions is untested [U].
- **How to see your real limits in two minutes:** open `aistudio.google.com/rate-limit` with the key you will use.

### 1.3 The current SDK idiom

`response_mime_type='application/json'` alone only asks for JSON text; it does **not** enforce a schema. Google's python-genai README now shows the pattern below ("pass a standard JSON schema through `response_json_schema`, with `response_mime_type` set to `application/json`") and says not to repeat the schema or an example JSON in the prompt because quality can drop [P README]. Google's Nov 2025 post says JSON-Schema support was added to all actively supported Gemini models and works with Pydantic; `response_schema=` is the older OpenAPI-subset path [S]. Pydantic's `model_json_schema()` output goes straight in.

```python
from typing import Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types, errors

class Chart(BaseModel):
    type: Literal["bar", "line", "pie", "number", "table"]
    x: str | None = None
    y: str | None = None

class SqlPlan(BaseModel):
    sql: str = Field(description="One DuckDB SELECT on table data")
    chart: Chart

client = genai.Client(api_key=KEY, http_options=types.HttpOptions(timeout=30_000))   # ms
cfg = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_json_schema=SqlPlan.model_json_schema(),
    thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
    max_output_tokens=2048,          # thinking tokens count against this; do not set it small
)
resp = client.models.generate_content(model="gemini-3.8-flash", contents=prompt, config=cfg)
plan = SqlPlan.model_validate_json(resp.text)   # validates the values (enum, required) not just JSON syntax
```

[T sdk_test.py] All of these construct without error in google-genai 2.29.0: `GenerateContentConfig` with `response_schema=<pydantic class>`, with `response_json_schema=<dict>`, with `ThinkingConfig(thinking_level=LOW)`, with `safety_settings`, with `HttpOptions(timeout=..., retry_options=HttpRetryOptions(...))`; `genai.Client(...)` has both `.models.generate_content` and `.interactions`. **Not tested live** (no key): that the 3.x models accept exactly this config. Also note `GenerateContentConfig` in 2.29.0 has no `response_format` field (Google's migration doc mentions one only for the Interactions API).

- **Interactions API.** Google now calls `client.interactions.create` its "primary interface" and its docs default to it, but states that `generateContent` "remains fully supported" and will keep getting new mainline models [S, Google launch post + docs]. Do not migrate the week of the deadline.
- If you prefer `response_schema=SqlPlan` you can read `resp.parsed`, but it is `None` when output is truncated or blocked [S, GitHub issue]. `response_json_schema` + `model_validate_json` is the more transparent path.
- Do **not** send `thinking_budget` on Gemini 3 models (replaced by `thinking_level`; sending both is a 400 per a third-party migration guide [S]); `ThinkingLevel.MINIMAL` errors on 3.8 Flash [S]; `LOW` is the safe common choice for both Flash and Flash-Lite and is what Google suggests for latency/cost-sensitive extraction [S].
- **Temperature for SQL: leave it unset.** See correction 8. Determinism now comes from the schema, the validation, and execution feedback (the retry-on-DuckDB-error loop is genuine external feedback, which is what makes self-repair work).

### 1.4 Thinking, safety, blocked responses

- **Thinking matters for latency/cost.** 3.8 Flash defaults to `medium`, 3.5 Flash-Lite to `minimal` [S]. Thinking tokens are billed as output and consume `max_output_tokens`. For one-table NL-to-SQL, `LOW` is a sensible default; raise to `MEDIUM` only for the SQL-retry call. Latency effect not measured (no key) [U].
- **Safety defaults.** Per the safety-settings page, the default threshold is OFF for Gemini 2.5 and 3 models [S], so category blocks are rarer than in 2024, but empty responses still happen: `prompt_feedback.block_reason` (SAFETY, PROHIBITED_CONTENT, BLOCKLIST, JAILBREAK...), a candidate with `finish_reason` SAFETY/SPII/PROHIBITED_CONTENT/RECITATION and no content, or a thought-only candidate. NGO data (health, minors) is the likeliest to trip SPII/PROHIBITED_CONTENT.
- **`.text` is `None` in all those cases** [T sdk_test.py: empty candidates -> None; SAFETY finish with no content -> None]. The app's `.text.strip()` then raises `AttributeError` and, because that matches neither regex, `_json` re-raises it as a user-visible 502 "The AI service failed: 'NoneType' object has no attribute 'strip'" [T, stub run, section 1.5]. Check `resp.text`, and when empty report `prompt_feedback.block_reason` / `candidates[0].finish_reason`.
- `finish_reason == MAX_TOKENS` yields truncated JSON: `resp.text` is a cut-off string [T sdk_test.py]. Retry with a higher cap.

### 1.5 Error handling in google-genai 2.x

[T] Classes: `errors.APIError` -> `ClientError` (4xx) and `ServerError` (5xx). Attributes: `.code` (int), `.status` (e.g. "RESOURCE_EXHAUSTED"), `.message`, `.details` (the full parsed JSON body as a dict), `.response`. `str(e)` is `"429 RESOURCE_EXHAUSTED. {the whole body}"`.
[T live_err.py] With a deliberately invalid key against the real endpoint: **HTTP 400, `status=INVALID_ARGUMENT`**, message "API key not valid...", `details['error']['details'][0]['reason'] == 'API_KEY_INVALID'`. A bad key is a 400, not 401/403, so `main.py`'s `401|403|PERMISSION_DENIED` branch will not fire for it (the separate `API key` branch does, by luck of the message text). I could not trigger a real 429/503/404 without a valid key; the shape of their bodies follows the standard `google.rpc` error model (`RetryInfo.retryDelay`, `QuotaFailure.violations[].quotaId`) [S/U].

Is regexing `str(e)` adequate? No. Reproduced against the current `llm._json` with stub clients [T, stub run]:

| Stub | What the current code does |
|---|---|
| `.text is None` (blocked) | `AttributeError`, no failover, 502 with a Python error string |
| 429 on first model | `raise` immediately, other models never tried (`BUSY` has no 429; `main.py` has the 429 message but only after `_json` gave up) |
| 429 whose message contains `...1500400404...` | matched by `MISSING` (`404`), silently burns all three models |
| truncated JSON | `JSONDecodeError`, no retry |

Robust approach: dispatch on `e.code` / `e.status` (ints and enums, not substrings), parse `RetryInfo` and `QuotaFailure` for per-minute vs per-day, fail over per model, treat empty/truncated/invalid output as a retryable model failure, and treat 400 as fatal. Working reference implementation, tested against nine stub scenarios (blocked, 429 per-minute, 429 per-day, 503 x2, 404, 400 bad key, truncated, invalid enum, all-fail): `/home/user/work/research/technical_tests/robust_llm.py` (`call_json`, `classify`, `make_config`). The SDK also has built-in retries (`types.HttpRetryOptions(attempts, http_status_codes=[...])`, constructs fine [T]); each retry still counts against quota, so keep `429` out of its list.

### 1.6 Data privacy: what to tell users

What the code really sends [P read `app/llm.py`, `app/main.py`]:

- **On every upload** (if a key is set): `meta` = row count, metric name, date-column name, **all column names**, plus the computed findings (`facts`: titles and detail strings such as "Hoodie drives 45% of amount", anomaly dates and totals) -> `narrate()`.
- **On every question:** the question (<=500 chars), column names and dtypes, **the first 3 distinct values of every column** (`unique()[:3]`, i.e. file order, not random), the generated SQL, and on a retry the failing SQL and the DuckDB error text; then the **first 15 result rows** as CSV plus the SQL to the verification call.

Google's terms for the Gemini API [S, copies of ai.google.dev/terms]:

- Unpaid ("free of charge", i.e. unpaid quota in the Gemini API or direct Google AI Studio use): Google uses submitted content and responses "to provide, improve, and develop Google products and services and machine learning technologies"; human reviewers "may read, annotate, and process your API input and output" (disconnected from your Google Account, API key and Cloud project first); and users are told not to submit sensitive, confidential or personal information.
- Paid Services (a Cloud project with active billing): Google does not use prompts or responses to improve products; limited logging for abuse detection only.
- Users in the EEA, Switzerland and the UK get the Paid-Services terms even on free quota. (Verify on the live page; I could not open it.)

Honest wording to use (README and a one-line UI notice near the upload box):

> **What leaves this server.** Lumen holds your file in memory (very large uploads may touch a temporary file that is deleted when the request ends). If AI features are on, Lumen sends the following to Google's Gemini API: when you upload, your column names, row count and a short list of computed findings (which can include category names, dates and totals); when you ask a question, your question, the column names and types, up to three example values per column, the generated SQL, and up to 15 result rows. This demo uses Google's free API tier: Google's terms say content sent on the free tier may be used to improve Google products and may be read by human reviewers, so **do not upload personal, confidential or sensitive data to this demo**. To keep data off Google's servers, run Lumen without a key (statistics, charts and forecasts still work; only plain-English questions and the narrated summary need Gemini). With a billing-enabled Google Cloud project, Google's paid-tier terms say prompts are not used to improve its products.

Code changes that make the sentence true and smaller: send sample values only for low-cardinality text columns, mask columns whose name or values look like email/phone/name/ID, and tell users that "Try sample data" uses synthetic data.

---

## 2. DuckDB 1.5.6: what the sandbox settings really do

All in the venv with DuckDB 1.5.6 (latest on PyPI today [P], released 2026-09-28 [S]). Scripts `duck1.py` to `duck11.py`.

### 2.1 Settings and their effects (each with its test)

| Setting | What it really does in 1.5.6 | Tiny test and result [T] |
|---|---|---|
| `enable_external_access=false` | Blocks file and URL access for all readers (`read_csv/parquet/text/blob/json`, `SELECT * FROM 'f.csv'`), `glob()`, `sniff_csv()` (CVE-2024-41672 is patched in 1.5.6), `COPY TO/FROM`, `EXPORT DATABASE`, `ATTACH 'file'`, `INSTALL` (needs the extension dir), `duckdb_extensions()`, and **Python replacement scans** (`SELECT * FROM df`). Does not block `ATTACH ':memory:'`, `LOAD json` (bundled), `duckdb_settings()`, `current_setting()`, `PRAGMA database_list`. **One-way**: cannot be switched back on at runtime even without a lock ("Cannot enable external access while database is running"). | duck1.py (19 statements, default vs off), duck2.py |
| `lock_configuration=true` | Freezes every setting, including `memory_limit`, `threads`, `temp_directory`, `allowed_*`, `disabled_filesystems`, `autoinstall_*`, `python_enable_replacements`, and `lock_configuration` itself. Limits must be set **before** locking. Python-API calls such as `con.register(...)` still work after the lock; a `cursor()` is also locked. | duck2.py, duck10.py |
| `allowed_directories` / `allowed_paths` | Exceptions to `enable_external_access=false`. Must be set **before** disabling access ("Cannot change allowed_directories when enable_external_access is disabled"). `..` is normalised (`allowed/../secret.csv` resolves to a path that is itself allowed; `allowed/../../../etc/hostname` is blocked); a symlink inside the allowed dir pointing outside is blocked; `glob` works inside. Lumen does not need either (it queries a registered DataFrame): leave empty. | duck2.py, duck9.py |
| `disabled_filesystems='LocalFileSystem'` | Extra layer: every local file operation fails ("File system LocalFileSystem has been disabled by configuration"); irreversible. The DuckDB advisory for CVE-2024-41672 gave exactly this as the workaround. Cannot be passed in `connect(config=...)` ("before the database is started"); use `SET`. | duck9.py, duck11.py |
| `memory_limit` | Enforced for buffer-managed operators: `list()` over 50M rows under a 200MB limit raised `OutOfMemoryException` at ~190 MiB. Sorts **spill to disk** instead of failing. **It is not a hard cap**: `length(repeat('x', 1e9))` allocated ~1 GB in 11.8 s under a 200 MB limit (process peak RSS 1.98 GB), and `unnest(generate_series(1,2e9))` tried a 16 GB allocation. Only an OS limit stopped them: under `ulimit -v 3000000` (RLIMIT_AS) `repeat('x', 3e9)` fails instantly with `OutOfMemoryException`. Units: `'512MB'` is stored as 488.2 MiB. | duck4.py, duck5.py, duck6.py, one-off ulimit runs |
| `temp_directory` / `max_temp_directory_size` | Default `.tmp` (relative to cwd): an in-memory DB **does spill user data to disk** (created and removed during a 30M-row sort under 200 MB, also when `enable_external_access=false`). `SET temp_directory=''` disables spilling (the same sort then raises `OutOfMemoryException`); `max_temp_directory_size='1MB'` caps it. Set `temp_directory` **before** disabling external access: `connect(config={'enable_external_access': False, 'temp_directory': ''})` fails with "Modifying the temp_directory has been disabled". | duck4.py, duck10.py, duck11.py |
| `threads` | Default = number of cores (4 here). `SET threads=2` works. On a small container use 1-2. | duck10.py |
| `python_enable_replacements` | Default **true**: SQL can read Python variables from the calling frame **and that frame's module globals** (`SELECT * FROM SECRET_GLOBAL` returned another DataFrame). `python_scan_all_frames` (default false) widens it to all frames. Either `python_enable_replacements=false` or `enable_external_access=false` closes it. | duck3.py |
| `autoload_known_extensions`, `autoinstall_known_extensions` | Default true: with network access, a query that needs a known extension tries to download it (`INSTALL httpfs` showed `Failed to download extension "httpfs" at URL http://extensions.duckdb.org/v1.5.6/...`). With `enable_external_access=false` it fails with `PermissionException` before any network call. The Python wheel bundles only `core_functions, icu, json, parquet`. Set both false and `allow_community_extensions=false` as defence in depth. | duck1.py, duck7.py |
| `enable_http_metadata_cache` (default false), `enable_external_file_cache` | Only cache metadata/contents of **remote** files read via httpfs. Irrelevant for Lumen; setting accepted, no effect on the sandbox. | duck9.py |
| Query timeout / row limit | **Do not exist**: no setting matching `timeout|limit|max|query` other than memory/temp/expression-depth ones. Use `interrupt()` (below) plus the `LIMIT` wrapper. | duck0 settings dump |

### 2.2 Settings that work together (tested end to end)

```python
con = duckdb.connect(":memory:", config={
    "threads": 2, "memory_limit": "512MB",
    "autoload_known_extensions": False, "autoinstall_known_extensions": False,
    "allow_community_extensions": False})
for stmt in ["SET temp_directory=''",                       # no spill to disk (OOM error instead)
             "SET disabled_filesystems='LocalFileSystem'",   # belt and braces
             "SET enable_external_access=false",             # one-way
             "SET lock_configuration=true"]:                 # ORDER MATTERS
    con.execute(stmt)
con.register("data", df)          # still allowed after the lock
```
[T duck11.py] After this: `SELECT * FROM df`, `read_csv`, `'/etc/hostname'` as a table, `COPY`, `INSTALL`, `LOAD spatial`, `ATTACH`, `glob`, `sniff_csv`, `read_text` and `SET threads=8` all fail; `PRAGMA database_list` and `duckdb_settings()` still run (read-only information). Wrap the process too: container memory limit or `resource.setrlimit(RLIMIT_AS, ~1.5 GB)` in a worker, because `memory_limit` alone does not stop one huge allocation.

### 2.3 Does `con.interrupt()` reliably stop long queries?

[T duck5.py, duck6.py, duck10.py] Mostly yes, with one important exception. Timer fired at 2.0 s in every case:

| Query | Stopped? | Latency after `interrupt()` |
|---|---|---|
| unbounded recursive CTE | yes | 2 ms |
| 1e6 x 1e6 cross join | yes | 1 ms |
| `sum(range(1e12))` | yes | <1 ms |
| 50M-row window function | yes | 1 ms |
| 100M-iteration string loop | yes | 1 ms |
| `list_sum(list_transform(range(1e8), ...))` | yes | 0.64 s |
| **single giant allocation `repeat('x', 3e9)`** | yes, but only after the allocation finished | **30.4 s** |

Interrupts are honoured between vectors/pipeline tasks, not inside one huge kernel. The connection is reusable afterwards and an idle `interrupt()` is harmless. The app's `threading.Timer(timeout, con.interrupt)` pattern is right; add an OS memory cap so the uninterruptible case cannot take the host down (Render free tier has 512 MB, per the other research file).

### 2.4 Parse-based validation (for the guard rewrite)

[T duck7.py, duck8.py] Both exist and work even under `enable_external_access=false` + lock.

- `con.extract_statements(sql)` (also `duckdb.extract_statements`): parse only, never executes; returns `Statement` objects with `.type` (`StatementType`), `.query`, `.named_parameters`, `.expected_result_type`. `len(result) == 1` catches stacked statements (`'SELECT 1; DROP TABLE x'` -> 2). **`type == SELECT` is not a safety proof**: `PRAGMA database_list`, `VALUES`, `SHOW TABLES`, `DESCRIBE`, `SUMMARIZE ...` and `SELECT * FROM read_csv('x')` all report `SELECT`; `PIVOT` becomes two statements `[CREATE, SELECT]`; `INSTALL` reports `LOAD`; `FROM data SELECT x` (FROM-first) parses; a syntax error raises `ParserException`.
- `json_serialize_sql(sql)` (bundled `json` extension): returns an AST for SELECT only (`{"error":true,"error_message":"Only SELECT statements can be serialized to json!"}` for `PRAGMA`/`COPY`); table references appear as `BASE_TABLE` (with `table_name`), `TABLE_FUNCTION` (with function name, e.g. `read_csv`, `glob`), `SUBQUERY`, `JOIN`; **`SELECT * FROM 'file.csv'` appears as a `BASE_TABLE` named `file.csv`**, so an allow-list must check names, not node types. `SELECT 1; SELECT 2` returns 2 statements.
- Suggested allow-list: exactly one statement; `type == SELECT`; walk the AST recursively; every `BASE_TABLE` is `data` or a CTE name defined in the same statement; zero `TABLE_FUNCTION` nodes (or only `range/generate_series/unnest`); then run in the locked sandbox. The blocklist regex can then go (it also rejects columns named `set`/`load`, which the README admits).

### 2.5 Other facts that touch the README's claims

- "Never written to disk": see correction 3 (upload spool > 1 MiB; DuckDB `.tmp` spill). `SET temp_directory=''` fixes the second; for the first, read the body with `request.stream()` into a bounded in-memory buffer or set a low upload cap.
- The README says "10-second timeout" and "1,000-row cap": both real in the code (`Timer` + `LIMIT 1000` wrapper) and consistent with 2.3; add the OS memory cap to the README as a real limit.

---

## 3. Forecasting

### 3.1 API facts [T unless stated]

- `statsmodels.tsa.holtwinters.ExponentialSmoothing` in 0.15.0: `(endog, trend=None, damped_trend=False, seasonal=None, *, seasonal_periods=None, initialization_method='estimated', ...)`; **`seasonal_periods` is keyword-only** (the app passes it by keyword, fine). `.fit()` -> results with `.resid`, `.forecast(h)`, `.sse`, `.aicc`. **Not deprecated** (statsmodels' own `tsa.rst` still documents it next to `ETSModel` [P]; no deprecation text in the module). statsmodels 0.15.0 was released 2026-08-27 [P release notes].
- `statsmodels.tsa.exponential_smoothing.ets.ETSModel(endog, error='add'|'mul', trend, damped_trend, seasonal, seasonal_periods, ...)`: the "innovations state space" family; statsmodels docs: these models "also support prediction intervals, simulation" (HoltWinters results do not give PIs) [P tsa.rst]. **0.15.0 fixed a log-likelihood bug in `ETSModel`** (PR #9400) [P], so AIC/AICc comparisons from older versions were unreliable; with 0.15 they can be trusted. Results expose `.aic`, `.aicc`, `.bic`, `.get_prediction(start, end).summary_frame(alpha)` with `pi_lower/pi_upper`.
- `ThetaModel(endog, period, deseasonalize, use_test, method)` exists, `.fit().forecast(h)` and `.prediction_intervals(h, alpha)`.
- **pandas 3 aliases:** `'MS'` works for `date_range` and `resample`; `'W'`, `'D'`, `'ME'`, `'QE'`, `'QS'`, `'YE'`, `'h'`, `'min'` work; the old `'M'`, `'Q'`, `'Y'`, `'A'`, `'H'`, `'T'`, `'BM'`, `'SM'` now raise `ValueError: Invalid frequency`. The app's `analytics.py` only uses `MS`/`W`/`D`. I ran the app's own `forecast()` on its demo data under pandas 3.0.6 + statsmodels 0.15.0 with `-W error::FutureWarning`: no warnings, 0.7 s, forecast index `2026-01-01...` as expected.
- **Weekly data** (`m=52`) fits in 0.1-0.3 s with the app's setting but needs 104+ points; with fewer than 3 years of weekly history, the 52 seasonal states are poorly identified [fit works; accuracy not benchmarked, U]. Prefer non-seasonal for weekly unless history is long.

### 3.2 Prophet

[T prophet_try.py in a throwaway venv] `pip download prophet --no-deps` and `pip install prophet` both succeed on Python 3.13.16 with pandas 3.0.6: **prophet 1.5.0** is a `py3-none-manylinux` wheel (11.9 MB) that **bundles the compiled Stan model and cmdstan 2.37.0** (788 files, 39.9 MB unpacked), so no separate cmdstan install. The environment it pulls in is 303 MB (matplotlib, holidays, cmdstanpy, ...). A 36-point fit took 0.2 s. So "heavy" is mostly installed size, not install pain. But accuracy on short series is the problem: Facebook's own guidance wants at least a few months, "preferably a year", of history [S]; independent comparisons (Kourentzes' M3 reanalysis; commentary) find Prophet behind exponential smoothing on standard benchmarks [S, I could not open the full analysis]. For 8-60 monthly points it adds size and risk without a documented accuracy gain. In my one smoke fit on AirPassengers (36 points, MAE 8.8) its default 80% interval contained only 1 of the 6 actuals [T prophet_try.py, a single series, so not evidence by itself]. **Recommendation: do not add Prophet.**

### 3.3 Backtest: what is the most defensible method for 8-60 points?

[T fc_bench.py, fc_lib.py, fc_analyze*.py; results in `technical_tests/analysis*.txt`] 690 rolling-origin windows, horizon 6, monthly, history lengths 8, 12, 24, 36, 48: 500 windows from 50 random series of `tsibbledata::aus_retail` (Australian retail turnover, via Rdatasets), 90 from six classic monthly series (AirPassengers, USAccDeaths, wineind, a10, debitcards, auscafe), 100 synthetic small-business-like series with known noise. Metrics: MASE (scaled by in-sample seasonal-naive error) and the geometric mean of per-window MAE ratios; 95% confidence intervals from a cluster bootstrap by series. This is one horizon, one frequency, mostly Australian data: indicative, not definitive.

Headline numbers (mean MASE, lower is better; ratio < 1 beats the reference):

| Method | L=8 | L=12 | L=24 | L=36 | L=48 | all |
|---|---|---|---|---|---|---|
| naive (repeat last) | 1.54 | 1.49 | 1.89 | 1.86 | 1.97 | 1.75 |
| seasonal naive | 1.54 | 1.06 | 1.10 | 1.10 | 1.05 | 1.17 |
| **app today** (damped HW, seasonal if >=24) | **2.25** | **2.01** | 0.89 | 0.78 | 0.73 | 1.34 |
| ETSModel, AICc over 18 configs | 1.50 | 1.33 | 1.50 | 0.82 | 0.74 | 1.17 |
| Theta (statsmodels) | 1.81 | 1.46 | 1.21 | 0.90 | 0.81 | |
| mean(ETS, Theta, seasonal naive) | 1.56 | 1.07 | 1.08 | 0.82 | 0.76 | 1.06 |
| **Policy: app HW if n >= 24, else seasonal naive (naive below 12)** | 1.54 | 1.06 | 0.89 | 0.78 | 0.73 | **1.00** |
| Policy: app HW if n >= 24, else mean(Theta, seasonal naive) | 1.63 | 0.98 | 0.89 | 0.78 | 0.73 | 1.00 |

Findings (95% CI in brackets, cluster bootstrap):
- The app's damped Holt-Winters is **1.32x worse than naive when n < 24 [1.24, 1.43]** and **0.49x of naive error when n >= 24 [0.43, 0.55]**. The drop at < 24 happens because it extrapolates a damped trend from too few points.
- **Seasonal naive is a very strong baseline** (26% lower error than naive overall) and nothing beats it by much below 24 points. This matches the M-competition lesson that simple benchmarks and combinations are hard to beat (Makridakis, Spiliotis, Assimakopoulos, M4: pure ML lagged statistical combinations; 12 of the 17 best entries were combinations [S]).
- **ETSModel with AICc selection is statistically tied with the app's HW at n >= 36** (ratio 0.989 [0.94, 1.05]) and **loses at n = 24**, because AICc rightly refuses the 14-parameter seasonal model on 24 points and so drops seasonality. So there is no accuracy reason to replace HW with ETS; the reasons to use ETS are native prediction intervals and principled model selection.
- The 3-way combination (ETS, Theta, seasonal naive) is the most robust single recipe: 10% lower error than seasonal naive overall, never far from the best at any length, but **9% worse than HW at n >= 24 [1.04, 1.14]** and costs about 1 s of ETS fitting per forecast on this box.
- **Interval honesty:** empirical coverage of the nominal 95% band: app HW 81%, ETSModel 84%, Theta 95% (but about 2.6x wider than ETS: median width/|actual| 0.70 vs 0.27 on retail). ETS half-widths x1.5 -> 94%; app x1.5 -> 91%. My quick STL+ETS variant had terrible coverage (9.5% at n = 24) because its band ignores seasonal and decomposition noise: do not use its intervals.
- No negative forecasts occurred on these positive series for any method, but the app's HW does produce them for intermittent data (-3.5 on a zeros-and-spikes series) [T fc_edge.py]; clip at 0 for non-negative metrics (the app clips only the lower bound).

### 3.4 Recommendation

1. **Minimum change (5 lines, no new dependency):** keep the current damped HW only when `len(s) >= 24` (>= 2 seasonal cycles for monthly). With 12-23 periods show a seasonal-naive "same month last year" projection (label it a baseline); with 8-11 show a flat last-value baseline and say "not enough history for a trend". Backtest: overall MASE 1.34 -> 1.00 (about 25% lower error), with no loss where HW already worked.
2. **If time allows:** replace the heuristic band by `ETSModel` prediction intervals (fit the 3 non-seasonal + 3 seasonal-if-n>=24 configs, pick by AICc, call `get_prediction(...).summary_frame(alpha=0.2)` and call it an 80% range, or scale to the observed coverage). Speed: a full 18-config AICc selection takes ~1 s median (p90 2.4 s, max 5.6 s) **only with `OMP_NUM_THREADS=1`**; with default BLAS threading in this shared sandbox the same selection took 8-35 s (load average 13-20 on 4 vCPU), because tiny matrices plus thread oversubscription is pathological. **Set `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` in the Dockerfile.** On a 0.1-vCPU host (Render free tier) expect it to be several times slower: keep the candidate set small there or stay with option 1.
3. **Label the claim:** "likely range" (not "95% range") unless you calibrate; keep the sentence "estimates, not promises" and add the method name ("damped Holt-Winters, backtested against a naive baseline").
4. **Theta vs seasonal-naive vs ETS, for the write-up:** Theta won the M3 competition and Hyndman & Billah showed it equals simple exponential smoothing with drift [S]; ETS/AICc is the standard automatic method in Hyndman & Athanasopoulos, *Forecasting: Principles and Practice* (ch. 8) [S, otexts.com blocked]; seasonal-naive is the benchmark everything must beat. In my data: tie between HW and ETS at >= 36 points, seasonal-naive best-or-tied below 24.

---

## 4. Competitive landscape and claim-checking

Prices are list prices reported by trackers on 2026-10-09 unless a primary page is named; vendors change these often.

### 4.1 Claim verdicts

| Claim in the pitch | Verdict | Evidence |
|---|---|---|
| "Power BI and Tableau are expensive" | **Soften.** Power BI Desktop is free; Pro is $14/user/month, PPU $24 (Pro was $10 until April 2025). Tableau lists Viewer $15, Explorer $42, Creator $75 per user/month (Standard) and $35/$70/$115 (Enterprise), billed annually; Tableau Public is free (public data only). For a 5-person NGO that is roughly $70/month for Power BI Pro, which is not "expensive" in the enterprise sense. Say "paid per seat and built for analysts". | [S] trackers: dashboardfox, cloudnuro, knowi, coefficient |
| "...and need training" | **Opinion, not checkable.** Both now ship AI assistants; say "steeper learning curve for a first look at a spreadsheet". | n/a |
| "Power BI Copilot sits behind paid enterprise licences" | **Imprecise.** Microsoft's Copilot overview says it needs a **paid Fabric capacity F2 or higher, or Power BI Premium P1+**; Pro or PPU alone are not enough; trial and free SKUs are not supported; Copilot usage draws capacity units. F2 is the smallest SKU, about $262-263/month (pausable), so "requires a paid capacity starting at about $260/month, not included in Pro" is accurate; "enterprise licence" is not. Older guides saying F64 are outdated. I found no 2026 announcement making Copilot free. | [S] excerpt of learn.microsoft.com "Copilot for Power BI overview"; Q&A threads; price [S] |
| "Looker Studio / Sheets Ask Gemini" | Looker Studio itself is free; **Conversational Analytics in Looker Studio requires a Looker Studio Pro subscription** (about $9/user/project/month) and is labelled Preview. Gemini in Sheets: for consumers it requires Google AI Pro/Ultra, for business Workspace Business Standard or above (Workspace update, Sept 2026); I could not confirm a button literally called "Help me analyze". | [S] Google Cloud docs excerpts; Workspace Updates blog |
| "free AI analytics for small businesses" (implied uniqueness) | **Not unique.** ChatGPT Free includes limited data analysis (reports of ~3 uploads/day); Claude Free has code execution and file creation enabled by default (Anthropic help article updated 2026-04-29); the Gemini app lets free users upload and analyse files; Excel "Analyze Data" is included in Microsoft 365 without a Copilot licence. | [S] TechRepublic Aug 2026, Anthropic support article, AlternativeTo, Microsoft support |
| "zero-config forecasts" | **Not unique.** Excel has `FORECAST.ETS` (AAA exponential smoothing) and Forecast Sheet; Power BI line charts have a Forecast option in the Analytics pane; Tableau forecasting uses exponential smoothing with prediction bands. | [S] Microsoft/Tableau help excerpts |
| "verified answers" | **Overclaim.** The verification is a second LLM pass over the first 15 result rows. Huang et al. (ICLR 2024) show LLMs struggle to self-correct reasoning without external feedback [S]. What is solid: the SQL and rows are shown, execution is read-only and sandboxed, the repair loop uses real DuckDB errors. Say "checked" and "show your work". | see 4.3 |
| "private by default" | **False on the free key** (section 1.6). | [S] Gemini API terms |
| "self-hostable, open source" | True for the app. With a key configured, data still goes to Google. Note competitors that are also self-hostable/open source: Metabase (AGPL, community edition), PandasAI (MIT except `pandasai/ee`), Wren AI (Apache-2.0, open core), DataLine (licence unclear, seeking maintainers). | [P] GitHub READMEs for Metabase, PandasAI; [S] others |

### 4.2 Competitor table

| Product | Price / free tier | Open source? | NL analytics? | Overlap with Lumen's pitch |
|---|---|---|---|---|
| Power BI | Desktop free; Pro $14, PPU $24 /user/month; Copilot needs F2+/P1+ capacity (about $260/month) | No | Copilot Q&A (paid capacity) | Dashboards; forecast in line chart; no free AI |
| Tableau | Viewer $15 / Explorer $42 / Creator $75 (Standard); Public free | No | Pulse / Agent in higher tiers (sources disagree on which) | Built-in forecast |
| Looker Studio | Free; Pro about $9/user/project/month | No | Conversational Analytics requires Pro (Preview) | Free dashboards |
| Google Sheets + Gemini | Paid plans for Gemini panel (AI Pro/Ultra or Workspace Business Std+) | No | Yes | Everyday spreadsheet |
| ChatGPT | Free tier with limited data analysis; Plus $20 | No | Yes (Python sandbox) | The main "upload a CSV and ask" competitor |
| Claude | Free tier has code execution + file creation (April 2026 help article) | No | Yes | Same |
| Julius AI | Free tier tiny (15 msgs/month, possibly cut to 5); Plus $16-35, Pro about $37-45 | No | Yes, chat-first | Closest commercial product to "ask your data" |
| PandasAI | Library free | MIT, except `pandasai/ee`; v3 pre-release per README mirrors | Yes (code gen in sandbox) | Library, not an app |
| Vanna | Free framework | MIT, but **repo archived 2026-03-29** (read-only) [P] | Yes (SQL) | Do not claim it as maintained |
| Metabase | OSS free; Starter about $100/month; Pro $575; AI add-on moving to usage pricing | Community edition AGPL [P]; commercial dirs under separate licence | Metabot (paid; OSS gets at most limited single-shot SQL, sources conflict) | Self-hostable BI |
| Hex | Community free with 100 Magic actions/editor/month; paid tiers $30-75/editor (sources disagree) | No | Magic | Notebook for analysts |
| Rows.com | **Acquired by Superhuman (announced 2026-02-23); standalone product reportedly wound down 2026-05-31** | No | Was AI Analyst | Drop it from the comparison |
| Quadratic | Free Personal tier (limited AI); Pro $18 | "Source available" (not OSI open source) per its own docs | Yes | Spreadsheet with AI + Python |
| Excel | Analyze Data included in Microsoft 365; Copilot $30/user/month add-on (business) or in Personal/Family/Premium plans | No | Copilot only | Ubiquitous baseline |

### 4.3 Honest positioning paragraph (safe to put in the pitch)

> Lumen is a free, open-source web app that gives a small shop or NGO a first look at a spreadsheet without anyone writing a prompt. On upload it computes the statistics itself (trend, unusual months, concentration, correlations) and shows them with plain-language next steps. When you ask a question, an LLM translates it into one read-only SQL query that runs in a locked-down, time-limited DuckDB sandbox, and the app shows you the SQL and the raw rows next to a short explanation, so you can see the work instead of trusting it. Forecasts come from a documented statistical method, with a stated range. It is designed to be self-hosted, and it works without any AI key. What it is not: the only free way to analyse a CSV with AI (ChatGPT, Claude and Gemini all do this with usage caps, and Excel, Power BI and Tableau have built-in forecasting), nor a replacement for BI tools. When the optional Gemini key is on, parts of your data are sent to Google, and on the free API tier Google may use them to improve its products.

Genuinely differentiated (defensible): insight-first on upload with no prompting; computed numbers rather than LLM-generated numbers; SQL and rows shown, sandboxed read-only execution; works with no key; open source and self-hostable; designed for non-technical small teams. Not differentiated (cut or soften): "free AI analytics", "zero-config forecasts", "verified", "private", "first NL-to-SQL".

### 4.4 References for why a verification step is needed (cite these)

1. **BIRD** (Li et al., NeurIPS 2023 Datasets & Benchmarks, arXiv:2305.03111): large-scale, dirty-data, execution-based text-to-SQL; human accuracy 92.96%. Today's best leaderboard entries are in the low 80s execution accuracy (Google "Gemini-SQL2" 80.04% single-model, Huawei DataGallery 82.39%, 2026 reports [S]; the 92.96 human figure and the leaderboard splits are not directly comparable).
2. **Spider 2.0** (Lei et al., ICLR 2025 oral, arXiv:2411.07763): 632 real enterprise workflows; the abstract reports an o1-preview-based agent solves **21.3%** versus 91.2% on Spider 1.0 and 73.0% on BIRD [S, abstract excerpt; I could not open arXiv]. Newer leaderboard claims are vendor-reported.
3. **"Text-to-SQL Benchmarks are Broken"** (Jin, Choi, Zhu, Kang, CIDR 2026; arXiv:2601.08778): annotation errors in 52.8% of BIRD Mini-Dev and 62.8-66.1% of the Spider 2.0-Snow examples audited; re-scoring changes leaderboard rank by up to 9 places [S]. Use it to say published accuracy numbers are themselves noisy, which is why the user should see the SQL.
4. **Snowflake Cortex Analyst engineering blog**: above 90% accuracy with a semantic model versus about 51% for single-prompt GPT-4o on Snowflake's internal real-world BI set [S; vendor-reported, say so]. Supports "context and checks matter more than the model".
5. **Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet"** (ICLR 2024, arXiv:2310.01798): intrinsic self-correction without external feedback often does not help and can hurt [S]. Supports verifying with execution results and showing evidence, and warns against calling an LLM second opinion "verified".

---

## 5. Other things found while testing (not asked, but they affect the demo)

- `app/main.py` calls `llm.narrate()` on every upload, including "Try sample data". Cache the narrative for the sample dataset (and for identical uploads) so judges do not burn quota (also in the other research file).
- `Dockerfile` is `python:3.11-slim` while everything above was tested on 3.13.16. PyPI metadata [P]: numpy 2.5.3 needs Python >= 3.12, pandas 3.0.6 >= 3.11, statsmodels 0.15.0, google-genai 2.29.0 and duckdb 1.5.6 >= 3.10, all list 3.13. On 3.11 pip would silently pick an older numpy than the one I tested. Switch the base image to `python:3.13-slim` (I did not build the image) and add `ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`.
- Pin: `duckdb==1.5.6`, `google-genai==2.29.0`, `pandas==3.0.6`, `statsmodels==0.15.0` (and test once).
- `statsmodels` 0.15 deprecates `random_state`/`seed` kwargs in favour of `rng` (FutureWarning) [P release notes]. Lumen does not use them.

## 6. Reproduce

`/home/user/work/research/technical_tests/`: `sdk_test.py`, `live_err.py` (SDK objects and the real error shape), `robust_llm.py` (proposed `call_json`), `duck1.py`-`duck11.py` (DuckDB), `fc_lib.py`, `fc_bench.py`, `fc_analyze*.py`, `fc_edge.py`, `fc_time.py`, `prophet_try.py` (forecasting), `forecast_bench_results.jsonl` (raw per-window forecasts), `analysis*.txt` (printed tables). Run with `/home/user/work/venv/bin/python -I -W ignore <script>` and `OMP_NUM_THREADS=1` for the forecasting ones; the benchmark needs the Rdatasets CSVs from `raw.githubusercontent.com/vincentarelbundock/Rdatasets` (paths are hard-coded to the scratch directory; edit `DATA`).

### Key URLs

- Google skill and migration notes: https://github.com/google-gemini/gemini-skills/tree/main/skills/gemini-api-dev
- Gemini CLI model constants: https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/config/models.ts
- python-genai README and CHANGELOG: https://github.com/googleapis/python-genai
- Gemini deprecations / rate limits / terms / safety / structured output: https://ai.google.dev/gemini-api/docs/deprecations , /rate-limits , https://ai.google.dev/terms , /gemini-api/docs/safety-settings , https://blog.google/technology/developers/gemini-api-structured-outputs/
- Interactions API announcement: https://blog.google/innovation-and-ai/technology/developers-tools/interactions-api-general-availability/
- Gemini 3 developer guide (temperature, thinking_level): https://ai.google.dev/gemini-api/docs/gemini-3
- DuckDB securing guide: https://duckdb.org/docs/stable/operations_manual/securing_duckdb/overview ; 1.5.6 post: https://duckdb.org/2026/09/28/announcing-duckdb-156 ; sniff_csv advisory: https://corgea.com/advisories/vulnerabilities/CVE-2024-41672
- statsmodels 0.15 notes: https://github.com/statsmodels/statsmodels/blob/main/docs/source/release/version0.15.0.rst ; tsa docs: https://github.com/statsmodels/statsmodels/blob/main/docs/source/tsa.rst
- Forecasting: https://otexts.com/fpp3/expsmooth.html ; Hyndman & Billah, "Unmasking the Theta method"; Makridakis, Spiliotis & Assimakopoulos, M4 results (IJF 2020)
- Microsoft Copilot for Power BI overview: https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction
- NL-to-SQL: https://arxiv.org/abs/2305.03111 , https://arxiv.org/abs/2411.07763 , https://arxiv.org/abs/2601.08778 , https://arxiv.org/abs/2310.01798 , https://www.snowflake.com/en/engineering-blog/cortex-analyst-text-to-sql-accuracy-bi
