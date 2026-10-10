# Devpost fields: copy and paste

**Project name:** Lumen

**Track:** AI + Business (cannot be changed after you submit)

**Tagline / elevator pitch (short description):**
Free, open-source AI analytics for people without an analyst: upload a spreadsheet, see what matters before you ask, get checked answers in plain English, tested forecasts and next steps.

**Built with (tags):** python, fastapi, pandas, duckdb, statsmodels, google-gemini, plotly, docker, render

**Links:** GitHub: https://github.com/Eshaan1e24/Lumen  |  Try it: (your Render address)  |  Video: (your YouTube link)

**Images to upload (in this order):** the architecture diagram (`docs/architecture.png` in the repo), then your three live-site screenshots (checked AI answer, forecast box, findings with "Show the numbers" open), then `docs/screenshots/01-dashboard.png`, `05-ngo-donations.png`, `06-mobile.png`.

---

## Written description (paste into the main text box)

### The problem and who it is for
Small shops, NGOs and student organisations collect sales, donations, stock and expense data, but rarely turn it into decisions. Power BI and Tableau are paid tools that need training, and Power BI's Copilot needs paid capacity. General chatbots can read a CSV, but give an answer with no standing way to check it. The people who most need clear answers (a shop owner, an NGO coordinator, a club treasurer) are left with a spreadsheet they cannot interpret. Lumen is for anyone with business data and no data analyst.

### What it does
- **Cleans real, messy spreadsheets:** finds the true header row below title rows, drops TOTAL rows, reads European number formats, currencies, Excel sheets, odd encodings and date styles, and shows raw versus cleaned side by side.
- **Tells you what matters before you ask:** trend, spikes and drops with the segment that caused them, concentration risk, and "what changed and why", which splits the change between two periods into exact per-segment contributions (and volume versus price when units exist).
- **Answers plain-English questions, with checks you can see:** the AI writes a read-only SQL query; it is parsed and allowed only if it is a single SELECT, run in a sandbox, cross-checked against a second differently written query, and every number in the explanation must trace back to the result. If a check fails the user sees it, and unverifiable wording is replaced by a plain summary built in code.
- **Forecasts that are tested first:** the method is chosen by backtesting on the user's own history, ranges come from the model's own past errors, and Lumen reports how it did against a simple guess and declines when there is too little history.
- **Says what it cleaned and lets you correct its guesses:** a data-health strip lists total rows removed, spellings merged and out-of-range scores ignored, and a picker lets the user change the main measure or date column and recompute everything.
- **Recommends next steps with evidence:** rule-based in code (win back donors who went quiet, chase the status that is owed money, repeat what worked), each with a "because" line quoting the numbers. Same with or without an AI key.
- **Fair comparisons:** a longer month or an extra weekly row is not mistaken for growth; windows with different amounts of data are compared per day or per reporting date.
- **Works without AI:** everything except free-text questions runs with no API key, and sample questions still answer from stored queries run live on the data.

### How we built it (technical approach)
FastAPI backend; pandas for ingestion and cleaning; DuckDB as the query engine; statsmodels for forecasting models; Google Gemini (structured JSON output, automatic fail-over across models) for question-to-SQL, a second query, and explanations; Plotly front end served locally with a strict content security policy so the page makes no third-party requests. The AI's role is deliberately narrow and verified: statistics are computed in code, SQL is validated by DuckDB's own parser (an earlier keyword blocklist was bypassed in our security review, so we replaced it), and explanations are checked against the data. Sessions live in memory with a time limit, uploads and questions are rate-limited, and the server is packaged in Docker for a 512 MB free host.

### How we know it works (evidence in the repo)
257 automated tests, including: 75 attack and benign cases for the SQL guard; failure paths against a scripted fake Gemini (quota, retired model, blocked reply, bad JSON, bad key, disagreeing queries, made-up numbers); the HTTP API end to end; 44 messy real-world-style files for ingestion, and regression tests from a black-box review: we generated 17 unseen datasets with planted facts, found that our first version missed most of them (although nothing crashed), and fixed the causes: doubled totals from TOTAL rows, wrong main measure, spikes quoted as "a trillion times normal", and unfair month comparisons. A spike-detector benchmark (false alarms on pure noise: 2.7%; planted spikes of 5 times a normal day or more are found 100% of the time; small spikes are honestly not flagged). A forecaster benchmark which showed the new forecaster is about as accurate as plain Holt-Winters (median MASE 0.820 against 0.812), so we do not claim better accuracy; its value is that it tests itself and reports it. A 20-question accuracy harness for the live AI, with reference answers computed independently in pandas. Memory measured at 147 MB idle and 314 MB peak.

### Challenges
Making the AI's answers trustworthy without pretending the AI is perfect; discovering in our own security review that a keyword blocklist could be bypassed and replacing it with a parser-based check; measuring honestly (our forecaster did not beat the baseline on accuracy, and a "confidence" label we tried did not predict accuracy, so we removed it); fitting the whole app into a free 512 MB host; and handling spreadsheets as they really are.

### Real-world impact
It gives small organisations the same kind of data-driven decision support that larger companies pay for, for free. Because it is open source, runs without an AI key, and can be self-hosted, a charity can keep its donor data on its own machine. The next step is saved dashboards, multi-table joins, a weekly emailed report, and multilingual questions.

### Honest limits
AI answers can still misread a question, and the number check covers digits, not names (the result table is always shown beside the explanation); the checks reduce that risk but do not remove it. The hosted demo accepts files up to 5 MB, rate-limits questions, and uses Google's free Gemini tier, which may use prompts to improve Google's products, so no sensitive data should be uploaded to a shared demo. Forecasts are estimates. Built with AI coding assistance (Claude), as permitted by the ForgeHacks rules; the AI features inside Lumen use the Google Gemini API.

---

## Before you press Submit

- [ ] All four team members are listed (Eshaan Sumesh, Anhad Mahajan, Aman Saxena, Harsh Salunkhe), with their real names.
- [ ] Track is **AI + Business**.
- [ ] Repo link works while logged out of GitHub, and the README shows the live and video links.
- [ ] Video plays while logged out, is Public, and is under 4:00.
- [ ] Live link opens (give it a minute if it was asleep).
- [ ] After Submit, reopen the project and confirm the status says **Submitted**, not Draft.
