# HANDOFF: Lumen for ForgeHacks 2026 (written Oct 9 2026, ~23:45 IST)

If you are a fresh Claude session reading this: you are taking over end to end. The user (Anhad) said "take over everything,
make judgement calls, do everything end to end, make no mistakes". Read this whole file, then continue from section 8.

## 1. Mission and hard constraints
- Hackathon: ForgeHacks Online 2026 (Devpost). Track: **AI + Business** (locked at submission, cannot change).
- **Deadline: Sat Oct 10 2026, 12:00 PM EDT = 16:00 UTC = 21:30 IST.** Aim to submit by ~18:30 IST (2-3 h margin).
  A saved Devpost draft does NOT count; confirm status "Submitted".
- Required: title + short description; track; PUBLIC 2-4 min demo video (YouTube Public, test logged out, aim 3:00-3:30);
  public GitHub repo with clear README; written description (problem+users, technical approach, impact); screenshots /
  architecture diagram / deployment link. Missing video or code = not judged. All members must be on Devpost (they are, per user).
- Judging (unweighted): Real-World Impact & Relevance ("must answer the prompt"), Technical Implementation & AI Use
  ("not just a wrapper"), Innovation, Execution & Completeness, Presentation.
- **Official AI + Business prompt (verified from the organizers' page screenshot):** "Build an AI-powered solution that turns
  business data into clear insights, predictions, or recommendations that help people make better decisions."
  Organizer footer: "Build around the specific prompt. A clear problem and a useful prototype go a long way."
  Mirror these words in README / Devpost / video: business data -> clear insights -> predictions -> recommendations -> better decisions.
- Prize reality: real cash only $275 total; AI+Business track prize = $10 credits (top-3 overall excluded). Goal = top-3 overall / judge impression.
- AI coding tools are explicitly allowed by the rules. Recommend (user agreed to consider) one README line: "Built with AI coding assistance, as permitted by the ForgeHacks rules." Never claim the code was hand-written.
- Team: Anhad Mahajan (user, GitHub Anhad23mahajan), Eshaan Sumesh (GitHub Eshaan1e24, owns the Lumen repo, started it),
  Aman Saxena, Harsh Salunkhe. Harsh "won't do anything for now" (so UI is free to change; still keep edits low-conflict).
  Devpost project #1459644; all members registered (user confirmed).

## 2. Delivery rules the user set (IMPORTANT)
- **Final submission repo = https://github.com/Eshaan1e24/Lumen (public, MIT intended).** Its `main` is still at commit `66c6405`.
- Eshaan refused to install the Claude GitHub App, so Claude CANNOT push there (add_repo push_check refused).
- **Eshaan wants every commit in the submission repo authored by Anhad (collaborator), with NO Claude author/co-author anywhere in that repo.**
  So: deliver finished code as plain files/patches + a **PowerShell (.ps1) script** that Anhad runs on Windows to create several logical commits
  under his own git identity and push. User explicitly asked: "just give me PowerShell commands and i will commit."
  Commits should be several, small, meaningful (history currently only 3 commits, all Eshaan's: judges may think it is a bulk import);
  add a dated "Built during the hackathon" section to README.
- My scratch/backup branch `claude/confident-brown-ayxkb3` of Anhad23mahajan/Anhad23mahajan (the profile repo) carries Claude trailers; that is fine and
  separate. Keep pushing to it (stop hook requires pushes). The project lives under `lumen/` there; `handoff/` holds this file + agent work.
  Do not open a PR unless asked. Never push to other branches.
- Export idea: `git format-patch --relative=lumen <baseline>..HEAD` produces patches with Claude as author, so for the Anhad-authored delivery
  generate the final tree as a snapshot (zip or the branch) and have the .ps1 apply per-group file sets with `git add <paths>; git commit -m "..."`
  using Anhad's identity (NOT `git am`). Handle Windows line endings (.gitattributes `* text=auto` or `core.autocrlf`).

## 3. Repo state
- Baseline (verbatim copy of Eshaan1e24/Lumen@66c6405): commit `c449719` in the profile repo branch, under `lumen/`.
- Later commits on this branch: `197e81f` (app/sqlguard.py + tests + LICENSE + .dockerignore), `db8a308` (app/limits.py + tests). Then a handoff commit.
- Lumen = FastAPI + pandas + DuckDB + Gemini (google-genai) + statsmodels, single static/index.html with Plotly (CDN). Features already present:
  upload+auto-profile+starter charts+KPIs+preprocessing preview (raw vs cleaned), NL question -> Gemini writes one DuckDB SELECT -> guard -> sandbox -> LLM
  "verify"+explain, statistical insights (trend first/last third, MAD anomalies, share-of-total + correlation "drivers"), Holt-Winters forecast, Gemini-phrased
  recommendations with template fallback, demo shop data, Dockerfile, README with Mermaid architecture.
- New, TESTED, NOT YET WIRED into app/main.py / llm.py (QA agent was running against the old source, so existing files were left untouched):
  - `lumen/app/sqlguard.py`: structural guard via DuckDB `json_serialize_sql` + hardened sandbox. 75 tests in `tests/test_sqlguard.py`.
  - `lumen/app/limits.py`: LRU+TTL SessionStore, RateLimiter (per-client window/day + global daily budget), streaming `read_capped`, xlsx zip-bomb check, env-tunable limits
    (LUMEN_MAX_UPLOAD_MB default 5, MAX_ROWS 200k, MAX_COLS 200, MAX_SESSIONS 6, SESSION_TTL 1800s). `tests/test_limits.py`. Total 81 tests pass (`python -m pytest -q` in lumen/).
  - `lumen/LICENSE` (MIT), `.dockerignore`, `pytest.ini`, `requirements-dev.txt`.

## 4. Verified facts (by running or reading primary sources)
- Environment: this sandbox cannot reach render.com, huggingface.co, cdn.plot.ly, forgehacks.dev, drive.google.com, ai.google.dev, duckdb.org. PyPI, devpost.com, GitHub proxy work.
  No Gemini key in the sandbox (user must not paste keys in chat; keys go in env secrets; a new session is needed to pick them up). So live Gemini behaviour is UNTESTED.
- Installed in the sandbox venv (/home/user/work/venv, NOT persistent): pandas 3.0.6, numpy 2.5.3, duckdb 1.5.6, statsmodels 0.15.0, scipy 1.18.1, google-genai 2.29.0, fastapi 0.115.14, uvicorn 0.32.1, python 3.13.
  `requirements.txt` is unpinned (`pandas>=2.2`), so a fresh Docker build gets pandas 3. numpy 2.5.3 and scipy 1.18.1 need Python >=3.12; the Dockerfile uses python:3.11-slim => use 3.13 and pin exact versions.
- SECURITY (verified by me): old regex guard is bypassed by `select * from query(replace('select * from duck#db_settings()','#',''))` (returns 162 settings incl. server paths);
  it also rejects legitimate `'Copy'` literals and columns named `set`. Engine sandbox (`enable_external_access=false`, `lock_configuration=true`) held; replacement scans disabled by it; no path traversal on /assets; esc() in the UI OK.
- Upload risks (security agent): whole body read before size check (500 MB POST -> 2.1 GB RSS); 1.7 MB CSV with 100k columns took 37 s / 513 MB; huge .xlsx unbounded; FIFO eviction (51 demo clicks evict others); no rate limiting; DuckDB memory_limit is not a hard cap for a single repeat('a',1e9).
- Hosting: **Hugging Face Docker Spaces are PAID (PRO) since ~July 2026 (user's own screenshot confirmed "Paid").** Primary = **Render Free (Docker)**, 512 MB RAM, cold starts; user already created a Render account + workspace "Lumen" (no card). Backup = Google Cloud Run (needs billing card).
  Render maintenance notice: Oct 14 06:30 IST (infrastructure upgrade) => README/Devpost must carry screenshots + video as fallback. Keep warm via cron-job.org GET /api/health every 5 min (UptimeRobot HEAD gets 405). Only one free service per workspace.
  Render deploy plan (give user exact clicks when code is final): New > Web Service > public repo https://github.com/Eshaan1e24/Lumen > Docker > Free; env GEMINI_API_KEY (secret), LUMEN_MAX_UPLOAD_MB=5, LUMEN_TRUST_PROXY=1, OMP_NUM_THREADS=1; health path /api/health; disable auto-deploy after final push; test from phone in incognito.
- Agent measured app memory ~295 MB normal, 472 MB with a 25 MB upload (tight on 512 MB) -> upload default 5 MB, sessions cap 6. Re-measure after changes.
- Gemini (technical agent, from primary changelogs; live behaviour untested): model order to use: [env GEMINI_MODEL, gemini-3.8-flash (GA 2026-09-02), gemini-3.5-flash, gemini-3.5-flash-lite (GA 2026-07-21), gemini-3.1-flash-lite]. gemini-2.5-flash retires ~Oct 16-20. Free-tier numbers unpublished (reports 20-1000 req/day). One judge ~11-21 calls.
  Use `response_mime_type` + `response_json_schema=PydanticModel.model_json_schema()` then `model_validate_json`; thinking_level LOW; do NOT set temperature (new models ignore/400). `.text` is None on blocked responses (crashes `.strip()`); dispatch on `e.code`/`e.status` not regex on text (404 inside a project number was misread); 429 must fail over to next model; truncated JSON handling. Invalid key = 400 INVALID_ARGUMENT. A tested replacement exists: handoff/agent_work/research/technical_tests/robust_llm.py.
- DuckDB setting order: `temp_directory=''`, `disabled_filesystems='LocalFileSystem'`, `enable_external_access=false`, then `lock_configuration=true`. Pin duckdb==1.5.6.
- Forecasting (technical agent backtest, 690 windows): damped Holt-Winters is 32% WORSE than naive under 24 points, ~2x better from 24 up; "95%" band covered only 81%. => use HW/ETS only at n>=24 else seasonal-naive; label as "likely range". Set OMP_NUM_THREADS=1 (ETS selection 8-35 s without). Skip Prophet. statsmodels ExponentialSmoothing not deprecated; 'MS' fine on pandas 3.
- Claims to FIX in README/pitch: "never written to disk" is false (uploads >1 MiB spool to temp; DuckDB can spill); "self-host keeps data local" false when a Gemini key is set (Gemini also gets question, SQL, column names, findings; free tier may be used for training/human review); "verified" -> "checked"; Power BI Copilot needs paid Fabric F2+/P1+ capacity (~$260/mo), not an "enterprise licence"; free AI CSV analysis exists in ChatGPT/Claude/Gemini app; Excel/Power BI/Tableau have forecasting; Vanna repo archived 2026-03-29; Rows.com shut down. Honest differentiation: insight-first (tells you before you ask), checked answers with visible SQL, backtested forecasts, free/open-source/self-hostable with a clear privacy statement. Full positioning + 5 NL-to-SQL refs (BIRD, Spider 2.0, annotation-error paper, Snowflake blog, Huang et al.) in handoff/agent_work/research/technical.md.
- Field: ~88 public submissions; 39 with video+repo; 29 with live link. Closest rival DecisionLens AI. Live URL + video already upper half.
- Sponsors: no "best use of X" prize; only optional Featherless (OpenAI-compatible) as fallback LLM, LAST priority and only if time.

## 5. Agent work products (copied into handoff/agent_work/, may be incomplete)
Reports: `research/hackathon.md` (done), `research/technical.md` (done). Security: `sec/` (guard_v2.py, hardened_llm_snippet.py, pocs/ — its REPORT.md could not be written; findings are in section 4).
STILL RUNNING when this was written (partial outputs only; their final reports may never have arrived):
- QA agent (ae57268...): `qa/` has repro scripts r01..r13, results json, `qa/patched/qa_fixes.patch` (candidate fixes, UNREVIEWED), pandas2-vs-3 comparison. No REPORT.md yet. RE-RUN/continue the QA battery under pandas 3.0.6 if needed. Seen so far: likely bugs include insights() correlation selection (`abs(best[1])` always truthy), clean() bool->int, day-first dates, number formats, partial periods, metric choice. VERIFY each before fixing.
- ML agent: `ml/forecasting.py`, `ml/drivers.py` (+ tests, bench scripts, results logs). Goal: backtest-selected forecaster with calibrated intervals; STL/robust anomaly with segment attribution; variance bridge (what changed and why, sums exactly); change-points; concentration. UNREVIEWED: run `ml/test_forecasting.py`, `ml/test_drivers.py`, read results_final.log before integrating; do not oversell numbers.
- UI agent: `ui/shots/gallery*` (Devpost-style screenshots), `ui/lumen-patched/` (patched copy of static/ with vendored Plotly), `ui/snippets/`, `ui/scripts/` (Playwright scripts; Plotly served by route interception), bugs.json. No REPORT.md yet. Review before applying.
- Eval: `eval/golden_cases.py` = 20 NL questions with pandas-computed truths on demo_df() (for scoring the live pipeline once a key exists; needs the lumen dir on sys.path).

## 6. Decisions made (judgement calls)
1. Treat project as harden+deepen, not rebuild. Keep Eshaan's architecture and UI look; additive changes; new UI in separate files, tiny edits to index.html.
2. Adopt structural SQL guard (app/sqlguard.py); wire into llm.py; keep error messages friendly.
3. Pin all deps to the tested versions; Docker base python:3.13-slim; OMP_NUM_THREADS=1; add HEALTHCHECK; non-root user optional.
4. Upload default 5 MB (env-tunable), column cap, row cap, streaming read, session LRU/TTL, rate limit /api/ask (default 8/10 min, 60/day/client, 400/day global) + friendly 429 text; **keyless "demo mode"** that replays stored answers for the sample dataset with an honest banner (so the live link never breaks). Optional: bring-your-own-key box.
5. Strengthen "not just a wrapper": (a) answer checking that is NOT the LLM grading itself: programmatically verify numbers in the explanation appear in the result set; optionally an independent second SQL (self-consistency) and compare; show "checked/unchecked" honestly. (b) "what changed and why" variance bridge; (c) backtested forecast with honest accuracy + naive comparison; (d) eval harness with measured accuracy (needs key; make it one command, report numbers only if actually run).
6. Honest copy everywhere (see section 4 claims to fix).
7. Billing on the Gemini key is the user's optional call (cap ~ $5 per ~1000 questions, agent estimate unverified); build so it works free.

## 7. Open items needing the user (do not block work)
- Gemini API key from aistudio.google.com (personal account, billing off), to be pasted ONLY as a Render secret `GEMINI_API_KEY` at deploy time. Never in chat/repo.
- Tomorrow: run the PowerShell commit script; click-by-click Render deploy; set up cron-job.org ping (free); record the demo video (2-4 min, YouTube Public) ~14:00-15:00 IST; fill Devpost; submit by ~18:30 IST.
- User's PC is Windows (PowerShell). Needs Git installed + configured name/email + GitHub auth to push to Eshaan's repo as collaborator.

## 8. Plan from here (priority order; ~18 h between usage reset at 03:30 IST and the deadline at 21:30 IST)
P0 (ship-critical)
 1. Re-create venv, run `python -m pytest -q` in lumen/ (expect 81 pass). Review QA artifacts; reproduce and fix verified bugs (pandas-3 issues, correlation bug, clean() bool, dates, number formats, partial periods, metric choice).
 2. Wire sqlguard + limits + robust Gemini client into main.py/llm.py; structured JSON output; model fallback by status code; blocked-response handling; friendly errors; rate limit; demo mode.
 3. Pin requirements; Dockerfile (python:3.13-slim, OMP_NUM_THREADS=1, HEALTHCHECK, honour $PORT); render.yaml optional; vendor Plotly (and fonts or system font stack) into static/ so no third-party CDN; CSP optional.
 4. README rewrite (honest claims, architecture diagram, run/deploy, privacy, limits, "Built with AI assistance", "Built during the hackathon" dated list, the exact track prompt, tech approach, evals/backtest numbers only if actually produced).
 5. Screenshots (Playwright with vendored Plotly) + Mermaid architecture diagram (+ PNG/SVG export if possible) for Devpost.
 6. PowerShell delivery script (grouped commits under Anhad's identity, CRLF-safe) + exact Render deploy clicks + video script/shot list + Devpost description text.
P1 (differentiation)
 7. Integrate reviewed ML modules: backtested forecaster (n>=24 rule, seasonal-naive fallback), variance bridge/"what changed and why", daily anomalies with attribution; new UI cards in separate JS/CSS; sample datasets (shop sales, NGO donations, inventory/expenses).
 8. Answer checking (numbers-in-result check + optional dual-SQL) + eval harness (`evals/run_eval.py` using golden_cases) - report numbers only if run with a key.
P2 (only if time) Featherless fallback LLM; PDF/print report; BYO-key box.
Always: run full tests + a manual smoke (upload demo, ask path with a stubbed LLM, forecast) before declaring anything done; re-check deadline timeline; commit+push to the scratch branch regularly.

## 9. Resume commands
```
cd /home/user/Anhad23mahajan && git status && git log --oneline | head
python3 -m venv /home/user/work/venv && /home/user/work/venv/bin/pip install -r lumen/requirements.txt pytest httpx
cd lumen && /home/user/work/venv/bin/python -m pytest -q
# run app:  /home/user/work/venv/bin/uvicorn app.main:app --port 8011
```
Eshaan's clone (read-only reference) may need re-cloning: `GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Eshaan1e24/lumen /home/user/eshaan1e24/lumen`. Re-check `git ls-remote` that main is still 66c6405 (if it moved, merge his changes first).

## 10. Update (after the usage limit hit)
The QA, ML and UI agents were terminated by the session rate limit before sending final reports. Their partial outputs were saved
(handoff/agent_work/{qa,ml,ui}); newer UI files (extra screenshots incl. sample-dataset picker, trust panel, report/PDF export, verify jsons, lumen-patched,
snippets) were added in a second save. Treat all of it as UNREVIEWED candidate work: read the scripts, re-run them, and verify numbers before using anything.
The security and both research agents DID finish; their conclusions are in section 4. `qa/patched/qa_fixes.patch` is an unreviewed candidate patch set.

## 11. STATE AT ~06:00 IST OCT 10 (supersedes sections 3, 5, 8 where they conflict)
DONE and pushed on branch claude/confident-brown-ayxkb3 (HEAD f4e9953 or later), all under lumen/, 219 tests pass (python -m pytest -q in lumen/, venv at /home/user/work/venv_clean from `pip install -r requirements-dev.txt`, Python 3.13):
- Backend rewritten: app/sqlguard.py (parser guard + sandbox), app/limits.py, app/llm.py (fail-over, 2nd-query cross-check at 8 sig digits, number grounding, narrative, demo mode, describe()), app/samples.py (shop/donations/inventory + stored questions), app/main.py, app/forecasting.py (from ML agent, tested), app/drivers.py (bridge + daily anomalies, own tests), analytics.py (QA patch + wiring).
- UI: static/index.html + lumen-app.js + lumen-extra.css + lumen-fixes.css + vendor/ (local Plotly/fonts); forecast panel has NO confidence badge by design.
- Evidence: tests/ (sqlguard 75, llm, api, drivers, forecasting, fixtures 44 files, evals), evals/ (cases, scoring, run_eval needs key, bench_anomaly, bench_forecast).
- Measured: spike FP 2.7% (4/150), 5x spike 60/60, 3x 27%, 2x ~2%; forecaster median MASE 0.820 vs old HW 0.812 (NO accuracy gain: do not claim), beats naive 73%, 95% range covers 93.7% (old 95.2%); confidence labels did not predict accuracy; memory 147 MB idle / 314 MB peak.
- Docs: README (placeholders LIVE_URL_PLACEHOLDER / VIDEO_URL_PLACEHOLDER only), docs/architecture.png + .mmd, docs/screenshots/*.png (real build, demo mode).
- delivery/: START_HERE.md, deliver.ps1 (clones this branch + Eshaan's repo, copies lumen/, 11 logical commits under the user's git identity, aborts if Eshaan's main moved past 66c6405), set-links.ps1, DEPLOY_RENDER.md, VIDEO_SCRIPT.md, DEVPOST_TEXT.md. These were also sent to the user as files.
NOT DONE / depends on the user:
- User runs deliver.ps1 (push to Eshaan1e24/Lumen main), deploys on Render (needs Gemini key as env secret), cron-job.org keepalive, records + uploads video (YouTube Public), runs set-links.ps1, fills Devpost, submits by ~17:30 IST (deadline 21:30 IST).
- No live Gemini test has ever run (no key in sandbox). First real-AI run happens on the deployed site; if answers misbehave, check llm.generate() error handling and prompts. `GEMINI_API_KEY=... python -m evals.run_eval` measures accuracy (writes evals/results/latest.md) - optional.
- PowerShell scripts were never executed (no PowerShell here); if the user reports an error, fix the script.
Useful: if asked to change anything after delivery, remember the user commits as himself; give patches as file edits + a short PowerShell snippet, never push to Eshaan's repo from here (no access).

## 12. State at 07:00 IST on Oct 10 (end of Phase 4)

- Code: all work is on `claude/confident-brown-ayxkb3` under `lumen/`. 257 tests pass (pinned venv, Python 3.13).
- Phase 4 came from a black-box review: 17 unseen datasets with 27 planted facts. First build: 0 crashes, but 23 of 27 facts missed. Fixed: TOTAL rows doubling totals, label spelling variants, wrong main measure, rating codes (99), trillion-times spikes, unfair month comparisons (now per day / per reporting date, whole breakdown like for like), mega-record defining the trend, status flags ranking before business dimensions, false duplicate warnings, 300-column slowdown.
- New: rule-based recommender with "because" evidence (`app/recommend.py`), segment findings (`app/segments.py`), data-health notices, measure/date picker + `POST /api/reanalyze`, cell-bounded session store (`LUMEN_MAX_CELLS`).
- Docs updated to match: README, delivery/DEVPOST_TEXT.md, VIDEO_SCRIPT.md, DEPLOY_RENDER.md, docs/screenshots (retaken from the final build).
- Known limits (also in the README): live Gemini path never run (no key in the build sandbox, test it first on the deployed site); name check added later on Oct 10 (labels from the data that are named but absent from the result); wide pivot files, debit/credit columns and text periods are not understood; uploaded files cannot answer questions without a key.
- Remaining for the user: run deliver.ps1, Gemini key, Render deploy (DEPLOY_RENDER.md), record video, set-links.ps1, submit on Devpost before 12:00 PM EDT (21:30 IST).
