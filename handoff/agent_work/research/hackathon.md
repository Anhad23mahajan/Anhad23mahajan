# ForgeHacks Online 2026: fact-check of the brief, hosting research, video rules

Researched 2026-10-09, 17:00-17:45 UTC (22:30-23:15 IST). Time left to the deadline when I finished: about 22 h 30 min.
Raw page snapshots and test scripts are in `/home/user/work/research/evidence/` (see the last section).

Source tags used throughout:
- **[D]** = I fetched and read the page myself in this session (curl through the proxy).
- **[S]** = only a web-search excerpt or summary was available; I did not open the page. Treat as secondary.
- **[U]** = UNVERIFIED (no source I could read supports it, or sources conflict).
- **[T]** = I tested it myself (local run of the app, scripts in `evidence/`).

Things I could NOT reach (egress policy or DNS): `www.forgehacks.dev`, `drive.google.com` (the organizers' participant packet), `help.devpost.com`, `info.devpost.com`, `render.com`, `huggingface.co`, `support.google.com`, `archive.org`, most vendor docs. Everything about those comes from search excerpts and is tagged [S]. I did not try to route around the blocks.

---

## 0. Corrections to the brief, in priority order

1. **Prize headline is misleading.** Devpost shows "$1,382,700 in cash". That figure is the exact sum of every perk, with the $785.50 per-participant credit bundle multiplied by 1,709 "winners" [D, I reproduced the total: 10,715 + 1,341,565 + 29,900 + 520 = 1,382,700]. Real cash is **$275** in total ($100 + $50 + $25 for places 1-3, plus $100 for the Cybersecurity track). The AI + Business track prize is **$10 of ProjectAAL credits (500 AI credits), a certificate and recognition**, "NOT A CASH PRIZE", and top-3 overall teams are not eligible for it. Plan for the "overall top 3" or the "Audience Favorite" certificate, not for the track prize.
2. **The schedule has real conflicts** (section 1). The deadline itself is unanimous: **Sat 10 Oct 2026, 12:00 PM EDT = 16:00 UTC = 21:30 IST.** Winner announcement is Oct 12 (Rules, organizer update) or Oct 18 (Devpost Dates page). Judging ends Oct 11 (Rules, update) or Oct 12 5 PM EDT (Dates page). Keep the live demo up through at least **Oct 20** (IST Oct 19 00:30 is the latest announcement time).
3. **"Start date Oct 1 vs Oct 3" is explained.** Oct 1 12:00 PM EDT is the Devpost *submission period* opening (project drafts existed from Oct 2). Oct 3 12:00 PM EDT is the *build window / "hackathon begins"* stated in the Rules and two organizer posts. A first commit on Oct 8 is after both, so the "created during the hackathon" test passes either way (section 6).
4. **Your track choice is permanent.** Organizer update: "Your track must be selected when you submit your project and cannot be changed afterward." The brief did not mention this.
5. **"Public GitHub repo" is slightly softer in the Rules** ("Code must be publicly viewable (or privately shared with organizers if required for judging)"), but the Overview says "GitHub repository with source code and a clear README". Keep it public; it is the safest reading.
6. **Screenshots / architecture diagram / deployment link** is an "or" list in the rules, not three required items. Do all three anyway (criterion 4 says "Working demo, polish, usability").
7. **AI + Business prompt wording matches the brief** (section 4), but I only saw it through a search-engine excerpt of forgehacks.dev [S], not on the page itself. The official prompts are also in the organizers' participant packet (Google Drive), which I could not open. Someone on the team should open it (link in section 4) and paste the prompt verbatim into the README and Devpost text, because judging criterion 1 says "Must answer the prompt accordingly".
8. **Hugging Face Spaces is no longer a free Docker host** (section 8). Docker/Gradio Spaces on the free `cpu-basic` hardware reportedly need a PRO subscription since about July 2026. The brief's "free CPU basic 16GB" is out of date for new free accounts.
9. **Render free has 512 MB RAM and 0.1 CPU** (not enough headroom for a 25 MB upload: I measured 472 MB peak). It is still workable for this app if the upload limit is lowered (section 8).
10. **The app's sample-data button and every upload call Gemini** (`narrate()` in `app/llm.py`), so judges clicking "Try sample" can drain a small free quota. Cache it (section 8.6).
11. **Eligibility text conflicts**: Overview says "Above legal age of majority in country of residence"; Rules say 13+ (under-18s need guardian permission). Only matters if a teammate is under 18; ask the organizers.
12. **Two different Discord invites** are published (Overview: `discord.gg/HmS3CHYAv6`; update 46776: `discord.gg/s5U4xUWXc`). I did not join either. The newer organizer post is more likely current, but I cannot tell [U].

---

## 1. Dates, with exact conversions (Part 1a)

EDT = UTC-4 on all these dates (US daylight time ends Sun 1 Nov 2026). IST = UTC+5:30.

| Milestone | What the source says | UTC | IST | Source |
|---|---|---|---|---|
| Submission period opens | Oct 1, 12:00 PM EDT (`data-iso-date="2026-10-01T12:00:00-04:00"`); API says "Oct 01 - 10, 2026" | Oct 1 16:00 | Thu Oct 1 21:30 | [D] Dates page; [D] `devpost.com/api/hackathons?search=forgehacks` |
| Build window / "hackathon begins" | Oct 3, 12:00 PM EDT | Oct 3 16:00 | Sat Oct 3 21:30 | [D] Rules; [D] updates 46753 and 46776 |
| **Submission deadline** | Oct 10, 12:00 PM EDT | **Oct 10 16:00** | **Sat Oct 10 21:30** | [D] Overview banner, Dates page (ISO `2026-10-10T12:00:00-04:00`), Rules, updates 45555/46756/46776 (all agree) |
| Judging starts | Oct 10, 1:00 PM EDT | Oct 10 17:00 | Oct 10 22:30 | [D] Dates page |
| Judging ends | Oct 12, 5:00 PM EDT (Dates page) **vs** "October 10-11" (Rules, update 46776; no clock time given) | Oct 12 21:00 (if "through Oct 11" means end of day EDT, my assumption: Oct 12 03:59) | Oct 13 02:30 (assumption case: Oct 12 09:29) | [D] |
| Audience Favorite public vote | October 10-11 | | | [D] Overview, update 46776 |
| **Winners announced** | **Oct 12, 3:00 PM EDT** (Rules; update 46776 "Monday, October 12 at 3:00 PM ET") **vs Oct 18, 3:00 PM EDT** (Dates page ISO `2026-10-18T15:00:00-04:00`) | Oct 12 19:00 **or** Oct 18 19:00 | Oct 13 00:30 **or** Oct 19 00:30 | [D] |

Which to trust:
- **Deadline:** all sources agree; the Dates-page timestamp is machine-readable with an explicit -04:00 offset. Confirmed: **21:30 IST on Sat 10 Oct**. Aim to press Submit by about 18:00 IST (T-3.5 h). Devpost drafts can be edited until the deadline.
- **Start:** use Oct 3 (organizer prose in three places). Oct 1 is just the Devpost portal setting.
- **Judging / winners:** the Rules and the organizers' Oct 3 post agree with each other, while the Devpost Dates page looks like a stale or differently-intended configuration. I cannot tell which was edited last [U]. For hosting purposes take the latest dates: **keep the demo live until at least Oct 20.**
- The rules say changes are announced via "Devpost updates and/or Discord", so re-check the Updates tab and Discord on Oct 10 morning.

---

## 2. Required submission items and rule text (Part 1b)

Exact text, [D] Overview "Requirements" section (also in `evidence/devpost-overview.txt`):

> **What to Build** Build a working AI-powered project that addresses a real-world problem within one of the six official tracks. Your solution should demonstrate clear use of AI/ML (models, APIs, agents, computer vision, NLP, recommendation systems, etc.) and show how it could create tangible value for users or communities.
>
> **What to Submit**
> - Project title and short description (clear problem + solution)
> - Track selection (Mention one of the six official tracks)
> - Public demo video (2-4 minutes max) that shows: The problem you are solving / How the project works / Posted online like on Youtube
> - GitHub repository with source code and a clear README
> - Written project description covering: Problem statement and target users / Technical approach and technical components used / How the solution creates real-world impact
> - Screenshots, architecture diagram, or deployment link for testing
>
> Incomplete submissions (missing video or code) will not be eligible for judging.

Relevant [D] Rules text (`/rules`):
- "Teams of 1-4 participants." "All team members must be listed on the Devpost submission."
- "You may use open-source libraries, public datasets, and pre-trained models."
- "Code must be publicly viewable (or privately shared with organizers if required for judging)."
- "AI coding tools (e.g. Copilot, ChatGPT, Claude, etc.) may be used to help build your project. This is separate from your project's own use of AI/ML, which is scored under Technical Implementation below."
- "Projects must be substantially created during the hackathon period. Pre-existing projects are not eligible unless clearly stated what was added during the event."
- "One submission per team. If a team submits multiple projects, organizers will judge only the most recently submitted one."
- "Teams retain full ownership ... By submitting, you grant organizers and sponsors a non-exclusive, royalty-free license to display, reference, and promote your submission (e.g. project name, description, screenshots, video)".
- "Organizers, judges, and mentors (and their immediate family members) are not eligible".
- "Organizers may update these rules if necessary ... communicated via Devpost updates and/or Discord announcement."

Organizer update 46776 [D] (posted Oct 3) adds:
- "every member must be registered on Devpost", "Your track must be selected when you submit your project and cannot be changed afterward."
- "Your project has to be built during the event. Existing libraries, frameworks and boilerplate are fine."
- "Submissions lock: Saturday, October 10 at 12:00 PM ET."
- The Featherless credit is "$25 in request credits, not unlimited access as we announced earlier."

Things that are NOT in the public rules (so no, the brief has not missed them, but I cannot see the logged-in submission form):
- No required video host beyond "Posted online like on Youtube"; no sponsor-tool or sponsor-API requirement; no word limits; no stated team-composition rule beyond 1-4; no "must be started after X" beyond "substantially created during the hackathon period"; no mention of "Built with" tags or "Try it out" links being mandatory. Devpost's standard form has both ("Built With", "Try it out"), and all 88 sampled live submissions display them, so fill both in. Word limits and mandatory form fields: **[U]**.
- Required-field enforcement by Devpost for the video field: [U] (cannot see the form).

---

## 3. Judging criteria (Part 1c)

Identical on the Overview and Rules pages [D]. The five names in the brief are exactly right.

| Criterion | Exact wording |
|---|---|
| Real-World Impact & Relevance | "How clearly the project addresses a genuine problem. Potential for actual use or meaningful benefit to users/communities. Must answer the prompt accordingly." |
| Technical Implementation & AI Use | "Quality of the AI/ML components, technical depth, correctness, and thoughtful integration of AI (not just a wrapper)." |
| Innovation & Creativity | "Originality of the idea or approach. Fresh combinations of technology or novel application to the problem space." |
| Execution & Completeness | "Working demo, polish, usability, and how much was actually shipped during the hackathon." |
| Presentation & Communication | "Clarity of the video, README, and written description. Ability to explain the problem, solution, and impact simply." |

- **No weights are published.** Equal weighting is not stated either [U].
- "A panel of mentors and industry/academic judges will score submissions. Ties will be broken by the judging panel. ... Judging decisions are final."
- The Overview lists roughly 35 people as judges or mentors (14 labelled "Mentor"), from companies including NVIDIA, Apple, Microsoft, Intuit, Walmart Global Tech (Senior Data Scientist), AMD (Business Analyst), Cockroach Labs, PayPal. Several are data or analytics people, which suits an analytics app.
- What the wording implies for Lumen: "not just a wrapper" rewards the deterministic stats engine, the SQL guard + sandbox + verification pass; show those in the video. "how much was actually shipped during the hackathon" rewards a visible commit history and a README section listing what was built in the window.

---

## 4. Track prompts (Part 1d)

- Overview [D] says "Track prompts will be released closer to the event" and "Find the released prompts at https://forgehacks.dev". Update 46776 [D] says the six prompts are in the **participant packet**: https://drive.google.com/file/d/10DcagvYeoBv7NEyu33H_6ciDRE5UMOsW/view?usp=sharing . I could not open it (drive.google.com is blocked by the egress policy), and `www.forgehacks.dev` does not resolve for my fetch tools. **A teammate must open the packet and copy the exact AI + Business text.**
- Through search-engine excerpts of `www.forgehacks.dev` [S], I got this wording for AI + Business, which matches the brief word for word:
  > "AI + Business: Automating workflows and driving smarter decisions. Prompt: Build an AI-powered solution that turns business data into clear insights, predictions, or recommendations that help people make better decisions."

  Another excerpt of the same site paraphrased it as "converts company data into insights, forecasts, or suggestions that support better choices", so I rate the brief's wording **probably exact, not verified on the page itself.**
- Other tracks, same [S] source (paraphrase quality varies):
  - Healthcare: "Build an AI-powered solution that makes healthcare information and interactions clearer, more accessible, or easier to act on."
  - Education: "Build an AI-powered solution that helps learners move beyond memorization to understand concepts, make connections, and apply what they learn."
  - Climate: "Build an AI-powered solution that helps people understand environmental changes, prepare for climate impacts, use resources wisely, or create resilient systems."
  - Cybersecurity and Creativity: only paraphrases (scams/impersonation/fraud; "a new way to make things, work together, share ideas, or engage with art and media"). Not needed for us.
- Independent corroboration from public submissions [D]: BriefCheck writes "For the AI + Business track, the idea is simple: the brief and the plan are the business data, each flagged gap is the insight, and the question it suggests is the recommendation", and several analytics entries describe turning "business data" into "insights ... decisions". That is consistent with the wording above.
- How Lumen maps (for the README/video): business data (CSV/Excel) -> clear insights (auto profiling + robust-z anomaly + trend + drivers) -> predictions (Holt-Winters forecast with 95% range) -> recommendations (grounded in computed findings) -> better decisions (plain-English Q&A that shows the SQL and rows). Say "insights, predictions, recommendations" using the organizers' words.

---

## 5. Prizes and sponsors (Part 1e)

All [D] from the Overview prize section.

| Prize | What it actually contains |
|---|---|
| 1st | $100 cash + $300 Featherless credits + $2,000 Momen credits + $1,000 Adaption credits + $60 ProjectAAL credits + $50 AoPS gift card + 5 Saily eSIMs + CodeCrafters VIP (2 yr) + DevSwarm Pro + CleanShot X + 6 months Agentboxd Team + 1 month Fulminare Maximus ("Total value $7,295, cash portion $100") |
| 2nd | $50 cash + $25 AoPS + $30 ProjectAAL + Saily + CodeCrafters (1 yr) + DevSwarm + CleanShot X ($2,090 value) |
| 3rd | $25 cash + $25 AoPS + $15 ProjectAAL + Saily + CodeCrafters (6 mo) + DevSwarm + CleanShot X ($1,330 value) |
| **AI + Business track** | **$10 ProjectAAL credits (500 AI credits), certificate, recognition on site and socials.** Highest-scoring project in the track; "Projects that place in the top three overall aren't eligible, so the prize goes to the next-highest project in the track." |
| Other tracks | Same $10 ProjectAAL bundle; Cybersecurity adds $100 cash + 6 months Agentboxd Team |
| Audience Favorite | Certificate only. "Decided by public vote on Devpost, October 10-11." |
| All Participants ("1,709 winners") | Perk bundle (Adaption $500, Momen $100, n8n Cloud Pro 1 month (first 300), Kariaa $40 (first 1,000), YouCam API $27.50 (first 1,000), Featherless $25 request credits, Agentboxd Builder 30 days (first 1,500), DevSwarm 1 month, ProjectAAL $5, Fulminare Lumen 1 month) "distributed at the start of the hackathon", redeemed via Discord / packet. "Certificate of participation for every team that submits." |
| All Teams ("100 winners") | "$299 in Tin Computer credits per team. One month of the Growth plan ... distributed after the event." How the 100 are chosen is not stated [U]; submitting a complete project is the only sensible way to be in the pool. |

Sponsor-specific "best use of X" categories: **none are listed.** The rules contain no requirement to use any sponsor tool. So there is no prize upside from a sponsor integration, only the (modest) judging value of a feature that genuinely helps.

Sponsors with an API an analytics app could honestly use:

| Sponsor | API relevant to us? | Time | Judging value | Recommendation |
|---|---|---|---|---|
| **Featherless AI** | Yes: OpenAI-compatible endpoint `https://api.featherless.ai/v1`, case-sensitive model IDs [S]. JSON-mode / structured-output support not documented in what I found [U]. | 45-90 min incl. testing SQL generation | Moderate and honest: a **fallback LLM** when Gemini returns 429/503, which directly protects the live demo. Not scored as a sponsor feature. | **Optional, last priority.** Only if the must-dos are done (deploy, rate limit, video, submission). Test that the open model produces valid JSON/SQL (the SQL guard + DuckDB sandbox still protect you), update the README privacy note (data now goes to a second provider), and say so in the video. Skip if it threatens the deadline. |
| n8n Cloud Pro | Workflow automation, not an LLM/data API. A "send weekly report" webhook is possible. | 1 h | Low; reads as gimmicky | Skip |
| Momen, Adaption, ProjectAAL, Kariaa, Fulminare, Agentboxd, DevSwarm, Tin Computer, YouCam, CleanShot X, Saily, CodeCrafters, AoPS | Momen is a no-code builder [S]; Adaption sells training-data tooling [S]; Agentboxd is an email inbox for agents (and its prize is for Cybersecurity); YouCam is a beauty-AI API; ProjectAAL, Kariaa, Fulminare, Tin Computer: **I could not find any public information** [U]. | n/a | None for a CSV analytics app | Skip. Do not claim "powered by" any of them. |

Gemini is not a listed sponsor; there is no Google prize.

---

## 6. Rules questions (Part 1f)

- **Same project in another hackathon?** The Rules are silent. Only "One submission per team" (within this event) is stated. I found no Devpost-wide rule; individual hackathons vary and some forbid it [S, club guides]. **[U] for ForgeHacks.** Don't dual-submit before results without asking the organizers (Overview has "Email the hackathon manager"; Discord `#mentor-help` per update 46776). If you later reuse it, disclose.
- **Public code required?** Yes in practice: "Code must be publicly viewable (or privately shared with organizers if required for judging)." Missing code makes the entry "not eligible for judging". No licence is required (Lumen's README says MIT, fine).
- **Pre-existing libraries allowed?** Yes: "open-source libraries, public datasets, and pre-trained models"; update 46776: "Existing libraries, frameworks and boilerplate are fine."
- **"Substantially created during the hackathon period" and your Oct 8 first commit.** I checked the real history [D/T]: `https://github.com/Eshaan1e24/lumen` has 3 commits: `7117c50` "Initial Lumen project" **2026-10-08 08:27:47 +0530** (= Oct 8 02:57 UTC = Oct 7 22:57 EDT, 654 lines added across 10 files), `6ebb38d` 2026-10-09 13:15 IST, `66c6405` 2026-10-09 21:10 IST. That is 4.5 days after the Oct 3 build start and 6.5 days after the Oct 1 portal opening, so the test passes under either start date. Risks and fixes:
  - **Thin history.** Three commits will look like a single bulk import to a judge scrutinising "how much was actually shipped". Commit in small, descriptive steps from now until the deadline, and put a short "Built during the hackathon" section in the README (dated list of what was built: profiling, forecasting, SQL guard, preprocessing preview, multi-model fallback ...). If any code came from earlier projects, say so explicitly; the rule requires it.
  - **Whose repo.** All 3 upstream commits are authored by `Eshaan1e24`. Everyone who worked on it must be a registered Devpost member and listed on the submission ("All team members must be listed on the Devpost submission"). If Eshaan is not on the team, this is someone else's project.
  - **Don't submit the profile repo.** `/home/user/Anhad23mahajan/lumen` is a commit by Claude on 2026-10-09 17:02 UTC, "Import Lumen baseline from Eshaan1e24/Lumen@66c6405 (unmodified)", inside the profile repo `Anhad23mahajan/Anhad23mahajan` whose own history starts 2026-08-21. I diffed `app/` against upstream: identical. Submitting the profile repo would show August commits and a profile README. Submit the dedicated project repo.

---

## 7. What the field looks like (Part 1g)

- Project gallery: **"The hackathon managers haven't published this gallery yet"** [D], and `/discussions` returns 404 [D]. Registered participants: 3,132 on the page, 3,135 by the Devpost API a few minutes later [D]. Final submission count is unknown [U].
- I found submitted projects through Devpost's public search (`devpost.com/software/search?query=...`) and confirmed each project page links to `forgehacks-2026.devpost.com`. **88 were found**; this is a search-biased sample, not the full set (list with taglines in `evidence/forgehacks-2026-sampled-submissions.json`). Of those 88 [D, scripted]: 43 embed a YouTube/Vimeo video, 62 link a GitHub repo, **39 have both video and repo** (the minimum for being judged), 29 link a live deployment (Vercel 15, GitHub Pages 7, Render 6, Netlify 2, Streamlit 1). So roughly half of early entries lack a video, and only about a third have a live link. A working public URL plus video already puts Lumen in the upper half.
- Closest competitors in the AI + Business lane (all [D]):
  - **DecisionLens AI** https://devpost.com/software/decisionlens-ai-wrido7 : CSV of revenue/COGS/opex -> validation, KPIs, anomaly detection (median/MAD), backtested forecast, evidence-grounded AI brief, what-if simulator; live Vercel link, video, GitHub. Same idea as Lumen with a tighter finance focus. The bar for polish.
  - **A Multi-Agent System for Stateful Data Analysis ("Graph Analytics")** https://devpost.com/software/a-multi-agent-system-for-stateful-data-analysis : Gemini + LangGraph + FastAPI + React, natural-language data analysis, PDF report; video but no live URL.
  - **BriefCheck** https://devpost.com/software/briefcheck-bhac9f : 188 tests, 25 test cases with measured accuracy, honest "What doesn't work yet" section, no hosted demo.
  - Others: BillBook AI, InsightLoop (live Vercel), MSME LoanRisk AI, Startup AI (live on Render), EcoStay AI, IntelliSLA (live on Render). One entry (NEXUS Intelligence Platform) pastes a very long architecture spec and cites a video URL that is not a valid YouTube ID; ignore it as a quality benchmark.
- Judgement on polish: the entries that look strongest share five things: a live URL, a short video, measured results or tests, an explicit "what is deterministic vs what the LLM does" statement, and a candid limitations section. Lumen already has the architecture story (AI writes SQL, guarded and sandboxed; stats are computed, not guessed). The gaps are the public URL, the demo-mode fallback, and a few measured numbers (e.g. how many of N test questions return correct SQL). I found no results from earlier ForgeHacks winners to calibrate against (the 2025 edition had 21 registrants [D, API]); this is judgement, not data.

---

## 8. Hosting (Part 2)

### 8.1 Measured resource profile of the app [T]

I ran a copy of the repo's `app/` + `static/` in a scratch venv (Python 3.13.16, FastAPI 0.115.14, pandas 3.0.6, numpy 2.5.3, duckdb 1.5.6, statsmodels 0.15.0, 4-core machine, no `GEMINI_API_KEY`). The Dockerfile uses Python 3.11; I could not build Docker here, so 3.11 memory is assumed similar [U]. Scripts: `evidence/memtest.py`.

| State | RSS |
|---|---|
| Idle after start | 155 MB |
| After `/api/demo` (sample data) | 168 MB |
| After first forecast (statsmodels imported lazily) | 257 MB |
| After 3.4 MB / 100k-row CSV upload + forecast | 276 MB |
| After 13.6 MB / 400k-row upload | 321-353 MB |
| After 23.5 MB / 690k-row upload (limit is 25 MB) | 393 MB, **peak 472 MB** (`VmHWM`) |

Timings on a fast local CPU: boot 1.1 s, sample 0.24 s, first forecast 1.0 s, 100k-row upload 1.1 s. At Render's 0.1 CPU expect several times slower [U]; plan for a slow first interaction after any restart.

Other facts from reading the code: sessions live in a dict capped at 50 DataFrames (`SESSIONS` in `app/main.py`); `GET /api/health` exists (and answers `HEAD` with **405** [T]); `/api/demo` works with no key (narrative falls back to template text [T]); `/api/ask` returns 503 without a key.

### 8.2 Comparison (terms checked as of Oct 2026; tags show how well verified)

| Option | Free terms | Fit for a one-instance, in-memory FastAPI container | Verdict |
|---|---|---|---|
| **Render Free web service** | 512 MB RAM, 0.1 CPU; 750 free instance-hours per workspace per month (an always-awake service uses ~744 h/month, so only ONE such service fits); spins down after 15 min without inbound traffic, wake-up "up to a minute"; ephemeral disk; Docker runtime works on Free; usually no card, sometimes a reversed $1 verification [S: render.com/docs/free, render.com/free article, Render community threads, July 2026 review]. Hobby workspace bandwidth was cut to 5 GB/month in 2026 [S]. | Works if upload limit is lowered (peak 295 MB normal, 472 MB at the 25 MB limit). Sessions are lost on every spin-down/redeploy, so keep it warm. | **PRIMARY** |
| **Google Cloud Run** | Request-based billing free tier (us-central1 pricing): **180,000 vCPU-s, 360,000 GiB-s, 2 million requests per month**, resets monthly, aggregated per billing account [D: cloud.google.com/run/pricing]. Idle `min-instance` is billed at $0.0000025 per vCPU-s and per GiB-s [D]. Needs a billing account (card) [S]. | 1 vCPU / 1 GiB is comfortable. Needs `--max-instances 1` because of in-memory sessions. Scale-to-zero cold start of a few seconds (blog estimates 1-3 s for FastAPI; heavier with pandas/duckdb) [S]. | **BACKUP** (card needed) |
| Hugging Face Spaces (Docker) | 2 vCPU / 16 GB, sleeps after 48 h idle (not configurable on free hardware) [S: huggingface_hub docs]. **But** creating a Docker/Gradio Space on `cpu-basic` now requires a PRO subscription ($9/month); free accounts get HTTP 402/403 "cpu-basic quota" (forum threads dated July 2026, docs excerpt; not an official announcement I could read) [S]. Static Spaces remain free. | Technically ideal (16 GB, `app_port: 8000`, secrets as env vars). | Not free. Use only if a teammate already has PRO. |
| Railway | One-time $5 trial credit for 30 days, 1 GB RAM cap, 5 services/project; **unverified accounts have restricted outbound network** (could block Gemini calls); afterwards $1/month free credit [S: docs.railway.com]. | Credit would last roughly a month at 0.5 GB always-on, then stops. | No |
| Fly.io | No free tier for new accounts: trial of 2 h runtime or 7 days; card required after [S]. | | No |
| Koyeb | Sources conflict: one says a 512 MB scale-to-zero free service still exists, others (July 2026) say it was removed; Mistral announced acquisition Feb 2026; a $29 card pre-authorisation was reported [S]. | | [U] Skip |
| Vercel / Netlify | Vercel Python functions up to 500 MB bundle, but functions are stateless, so in-memory sessions break; Hobby is non-commercial [S]. Netlify: serverless too [U, not researched]. | Architecturally unsuitable. | No |
| AWS | New accounts: Free Plan with $100 credit (+ up to $100 for tasks); plan ends at 6 months or credits used [S]. | Works but needs console/ECS/App Runner knowledge and a card. | No for a first deploy |
| Azure | Free account $200/30 days with card; "Azure for Students" $100 credit/12 months with school email and no card [S]. | Works via App Service; more setup. | Only if a teammate already has it |
| Oracle Cloud Always Free | Ampere A1 allowance reportedly cut to 2 OCPU / 12 GB in June 2026 [S]; you administer a VM yourself. | | No |
| GitHub Codespaces | 120 core-hours and 15 GB-month storage per month for personal Free accounts; default idle timeout 30 min [S]. | Dev tool, stops when idle. | No |
| GitHub Pages | Static files only. | Good for a **static snapshot** fallback (screenshots / exported charts). | Fallback only |

### 8.3 Recommendation

- **Primary: Render, Free web service, Docker runtime, one instance**, kept warm by a free pinger, with the upload limit lowered. Reason: no card normally, point-and-click from a GitHub repo, a plain public HTTPS `*.onrender.com` URL. The two real risks are the 512 MB limit and the 15-minute spin-down, both handled below.
- **Backup: Google Cloud Run** with `--max-instances 1`. Deploy it tonight as a second URL even if Render works; if Render misbehaves you only swap the link in Devpost and README. If nobody on the team can add a card, the backup is the static-snapshot page plus the video (and Hugging Face only if someone has PRO).
- If one teammate has a card and is comfortable with a terminal, Cloud Run is technically the better primary (1 GiB, full vCPU). The call above favours "never deployed before, GitHub account only".

### 8.4 Files to add or change in the repo before deploying (suggested, not applied; I was told not to edit that repo)

1. `.dockerignore` (stops a local `.env` from ever being copied into an image by `COPY . .`):
   ```
   .git
   .env
   .venv
   __pycache__/
   *.pyc
   ```
2. Dockerfile (current one works; these are hardening tweaks):
   ```dockerfile
   FROM python:3.11-slim
   ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 MALLOC_ARENA_MAX=2
   WORKDIR /srv
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   RUN useradd -m -u 1000 appuser
   USER appuser
   ENV PORT=8000
   EXPOSE 8000
   CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
   ```
   `uvicorn` runs one process by default; keep `--workers 1` because sessions are in-memory. Pin the versions you tested (`pip freeze > requirements.txt` from a working env): `pandas>=2.2` currently resolves to pandas 3.0.x, which I tested on 3.13 only.
3. In `app/main.py`: change `MAX_BYTES = 25 * 1024 * 1024` to about `5 * 1024 * 1024` for the public instance (peak memory about 295 MB instead of 472 MB; I measured 3.4 MB / 100k rows at 276 MB), and change the session cap `len(SESSIONS) > 50` to about `> 5`. Make both env-driven so you can raise them locally.
4. Optionally make the health route answer `HEAD` as well (`@app.api_route("/api/health", methods=["GET", "HEAD"])`), because some uptime monitors use HEAD and would otherwise see a 405 [T].
5. Optional `render.yaml` (dashboard clicks work without it; the file makes it reproducible). `plan: free` must be explicit, because the Blueprint default is not free [S]:
   ```yaml
   services:
     - type: web
       name: lumen-forgehacks
       runtime: docker
       plan: free
       region: oregon            # or virginia/frankfurt/singapore; most judges look US-based
       dockerfilePath: ./Dockerfile
       healthCheckPath: /api/health
       autoDeploy: true          # switch to false after the final deploy
       envVars:
         - key: GEMINI_API_KEY
           sync: false           # you paste the value in the Render dashboard, never in git
   ```
   `dockerfilePath` and region names come from search excerpts of the Blueprint docs, not from the docs page itself [U]; if a field is rejected, delete it and use the dashboard.

### 8.5 Step by step: Render (primary)

1. **Repo.** Decide which GitHub repo is "the" submission repo (it is `Eshaan1e24/lumen` today). The person who owns it should do steps 2-4, or fork it into their own account, or use Render's "Public Git Repository" option if offered (paste the URL; no GitHub permission needed, but no auto-deploy) [U, UI]. Push the changes from 8.4 and make sure `.env` is not committed.
2. **Sign up** at render.com with "Continue with GitHub" (free Hobby workspace; no card expected, but Render sometimes asks for a $1 reversible card check [S]).
3. **New + -> Web Service** -> choose the repo -> Name `lumen-forgehacks` -> Language/Runtime **Docker** -> Branch `main` -> Region (pick one) -> **Instance Type: Free**.
4. **Environment Variables:** add `GEMINI_API_KEY` = your key (use a key made only for this demo; do not reuse a personal key). Leave `PORT` alone: Render injects `PORT` (default 10000) and the Dockerfile `CMD` already reads `${PORT}` [S]. Under Advanced set **Health Check Path** `/api/health`. Click **Create Web Service**.
5. **Wait for the build** (first build is several minutes). In Logs look for `Uvicorn running on http://0.0.0.0:...`. Open `https://lumen-forgehacks.onrender.com`. Test: **Try sample data**, upload a small CSV, forecast, ask a question. Check the Metrics tab for memory.
6. **Keep it warm** (8.7). Verify by leaving it alone for 20 minutes and reloading from a phone on mobile data.
7. **Freeze.** Once the final version is live: Settings -> Build & Deploy -> Auto-Deploy **Off**, so a stray push does not restart the service and wipe sessions during judging. Put the URL at the top of the README, in Devpost "Try it out", and in the video description.
8. Calendar: keep it running at least through **Oct 20**, then delete the service and the API key (Section 8.6, item 6).

### 8.6 Protecting the Gemini free quota, and a no-key "demo mode"

**What I could not establish:** current free-tier numbers. Search results conflict badly: one September 2026 guide says Gemini 3.5/3.6/3.7/3.8 Flash get about **20 requests per day** and Flash-Lite 500; other guides say hundreds to 1,500; a guide checked against Google's docs on 28 Sept 2026 says Google publishes no fixed figures and shows limits per project in AI Studio [S, all secondary]. **Tonight, open Google AI Studio -> your project -> rate limits and read the real numbers for the exact model you use**, then size the caps below. Design for the worst case (tens of calls per day).

How the app spends Gemini calls today (from `app/llm.py`, `app/main.py`):
- Every `/api/demo` click and every upload runs `narrate()`: 1 call.
- Every question runs a plan call + a verification call (2), plus up to a retry on SQL error and extra calls on 503, across up to 4 model names.
- A 429 is *not* treated as "try the next model"; it raises and the user sees "free quota is used up".

Mitigations, in order of value:
1. **Cache the sample-data narrative** (compute once per process; reuse for every "Try sample data" click). Zero Gemini calls for the most common judge action.
2. **Per-IP and global caps on AI calls.** I wrote and tested a 25-line guard (`evidence/guard_snippet.py`; tested: 5 requests from one IP gave `[True, True, True, False, False]` with limit 3, and the global cap cut off a second IP). Call `ai_allowed(request)` at the top of `/api/ask` and `narrate`; when it returns False, fall through to demo mode. Suggested starting values: 5 questions per IP per 10 minutes, 40 questions per UTC day (raise after you read the real quota). In-process counters are fine because there is one worker; keep `--proxy-headers` so the client IP comes from `X-Forwarded-For`.
3. **Treat 429/RESOURCE_EXHAUSTED like 503**: move to the next model in `MODELS` (each model has its own quota) before giving up. Put a cheaper Flash-Lite model first for `narrate()` and keep the main model for SQL.
4. **Demo mode with zero key** (honest and cheap): generate once, with your real key, 5-6 sample questions on the built-in sample data and save `{question, sql, chart spec, answer text}` to a JSON file in the repo. When there is no key, or the guard says no, match the question against that list and **run the stored SQL live in DuckDB** against the sample dataframe (so the numbers and charts are real), and show a banner: "Demo mode: showing pre-recorded AI-written SQL for sample questions because live AI is rate-limited or offline." The rest (profiling, charts, insights, forecast, template recommendations) already works with no key [T]. Do not present cached answers as live.
5. **Key hygiene:** create a separate API key for the demo in an AI Studio project with no billing attached (so it cannot create a bill); never commit `.env` (it is in `.gitignore`; the `.dockerignore` above covers the image); don't show it in the video. Rotate or delete the key after the winners are announced and the demo is retired.
6. **Privacy note:** the README says only schema, 3 sample values per column and result rows are sent to Gemini; free-tier prompts may be used by Google to improve products (secondary source [S]), so tell judges to upload only non-sensitive data and offer the sample button.

### 8.7 Keeping it warm

- **cron-job.org** (free; it states the shortest interval is 1 minute and requests time out after 30 s) [S: its FAQ]: create a job for `GET https://<name>.onrender.com/api/health` every **5 minutes**. Use a real route; a ping to a path the app doesn't serve may not count as app activity.
- **UptimeRobot free**: 50 monitors, 5-minute interval [S]. Its terms are contradictory in the sources (several say the free plan has been personal/non-commercial only since late 2024; one says May 2026 terms allow any use). A hackathon demo is non-commercial, so either reading is fine, but confirm on their site. It may use HEAD, which gets a 405 from `/api/health` today [T]. The request still wakes the app, but the monitor will show "down" until you add HEAD support (8.4 item 4) or pick GET.
- **GitHub Actions `schedule`** is a poor primary pinger: best-effort timing, high-load delays or dropped runs, and scheduled workflows are auto-disabled after 60 days without repo activity [S]. Fine as a second pinger.
- A 10-minute ping leaves a margin under Render's 15-minute rule. The ping uses free instance hours, but one always-awake service (744 h in a 31-day month) fits inside the 750-hour pool. **Do not run a second free web service in the same workspace** or both will be suspended mid-month.
- Warm-keeping does not protect against Render restarting the service or against a redeploy; sessions would still be lost then ("Session expired. Upload your file again."). The demo-mode and "Try sample data" paths recover instantly, which is another reason to lead the video with them.

### 8.8 Step by step: Google Cloud Run (backup), using the browser Cloud Shell

I read the Cloud Run pricing page directly; the commands below are standard `gcloud` usage that I could not re-check against the docs (blocked), so test them tonight [U].

1. console.cloud.google.com -> create a project (e.g. `lumen-forgehacks`) -> link a **billing account** (card required; the free tier above still applies) -> create a budget alert of a few dollars.
2. Open **Cloud Shell** (the `>_` button) and run:
   ```
   git clone https://github.com/Eshaan1e24/lumen && cd lumen
   gcloud run deploy lumen --source . --region us-central1 --allow-unauthenticated \
     --memory 1Gi --cpu 1 --max-instances 1 --min-instances 0 --timeout 120 \
     --set-env-vars GEMINI_API_KEY=PASTE_DEMO_KEY_HERE
   ```
   Say yes when asked to enable APIs / create an Artifact Registry repository. Cloud Run sets `PORT` (8080) itself and the Dockerfile `CMD` reads `${PORT}`.
3. The command prints `https://lumen-xxxxx-uc.a.run.app`. Test it exactly as in Render step 5.
4. `--max-instances 1` is mandatory (in-memory sessions). With `--min-instances 0` the instance stops when idle and sessions are lost; during judging windows you can run `gcloud run services update lumen --region us-central1 --min-instances 1`. The idle price is $0.0000025 per vCPU-s plus $0.0000025 per GiB-s [D], about $0.43 per day for 1 vCPU + 1 GiB before free-tier credits; how the free-tier credit applies to idle time is [U], so set the budget alert and revert to 0 afterwards.
5. Prefer us-central1 (the free tier is defined on us-central1 pricing).
6. After judging: `gcloud run services delete lumen --region us-central1`.

### 8.9 Hugging Face Spaces (only if a teammate already has PRO) [S]

Create a Space, SDK **Docker**; add this front matter at the top of `README.md` in the Space repo:
```
---
title: Lumen
emoji: 📊
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8000
---
```
Add `GEMINI_API_KEY` under Settings -> Variables and secrets (available to the container as an environment variable; changing it restarts the Space). Free hardware sleeps after 48 h without requests and cannot be configured; wake-up time is not documented [S]. Because Hub docs now say Docker Spaces on free `cpu-basic` need PRO, do not count on this without checking the creation dialog first.

### 8.10 Last-resort static fallback

Keep one URL that cannot go down: a GitHub Pages (or repo README) page with 5-6 screenshots of the sample-data run, the architecture diagram, and the video embedded. Judges who hit a dead backend still see the product.

---

## 9. YouTube / Devpost video rules (Part 3)

- **What the hackathon says** [D]: "Public demo video (2-4 minutes max) that shows: The problem you are solving; How the project works; Posted online like on Youtube". "Incomplete submissions (missing video or code) will not be eligible for judging."
- **Hosts Devpost embeds:** a Devpost staff answer relayed on a Databricks community thread says the video must be "uploaded to and made publicly visible on YouTube, Vimeo, Facebook Video, or Youku so that it can playback on Devpost" [S, relayed, not read directly; Devpost's own help article could not be reached]. Consistent with what I saw: 43 live ForgeHacks project pages embed YouTube (`youtube.com/embed/...`) or Vimeo (`player.vimeo.com/video/...`) [D]. Use YouTube; avoid Facebook Video and Youku (login or region problems), and avoid Google Drive/Dropbox/Loom links (not reliably embeddable or may need a login).
- **Public vs Unlisted:** YouTube's own help says unlisted videos "can be seen and shared by anyone with the link" and don't appear in search [S: support.google.com/youtube/answer/157177]; Private is owner-and-invitees only and will fail. Many hackathons accept "public or unlisted", but **ForgeHacks says "Public"**, and there is also a public Audience Favorite vote. **Set it to Public.** Unlisted would probably work technically, but nothing in the rules says it is allowed. Whether the organizers or judges would reject an unlisted link: [U].
- **Length enforcement:** Devpost does not measure it (the field is just a link). The rule is "2-4 minutes max". How strictly judges apply it: [U] for this event; other Devpost hackathons tell judges to stop watching at the limit [S]. Treat 4:00 as a hard stop that nobody watches past. Aim for 3:00-3:30, finish the live product demo by 2:30, and put the problem + the live URL in the first 30 seconds.
- **Make sure judges can watch without logging in:** open the link in a private/incognito window while logged out, and once on a phone with Wi-Fi off. In YouTube Studio, check Visibility = Public, "Allow embedding" ON, audience = "No, it's not made for kids" (made-for-kids disables features and comments), no age restriction. Put the video URL in the Devpost video field, README, and the GitHub repo description.
- **Common traps:** (a) YouTube processes HD for minutes to hours after upload, so upload tonight, not at 20:00 IST on Saturday [S]; (b) copyrighted music can trigger a Content ID claim that mutes or geo-blocks the video [S: support.google.com/youtube/answer/6364458], so use no music or royalty-free; (c) accounts that are not phone-verified are capped at 15-minute uploads, irrelevant at 4 minutes [S]; (d) never show `.env` or the API key; (e) if you add captions, check they cover the narration.
- **Content checklist from the criteria:** state the problem and the prompt wording, show the live URL working on sample data, upload a messy file to show preprocessing, show one question with the SQL and rows visible, show the forecast with its range, show the demo-mode banner honestly, end with measured results and limitations. Add timestamps in the YouTube description (helps "Presentation & Communication").

---

## 10. Open items I could not close

| Item | Why | How to close |
|---|---|---|
| Verbatim six prompts | Organizers' packet is on Drive (blocked); forgehacks.dev unreachable here | A teammate opens https://drive.google.com/file/d/10DcagvYeoBv7NEyu33H_6ciDRE5UMOsW/view and the site; copy the AI + Business paragraph |
| Winners date (Oct 12 vs Oct 18) and judging end (Oct 11 vs Oct 12) | Devpost Dates page conflicts with Rules and the organizers' post | Ask in Discord `#mentor-help` or the hackathon manager email; keep the demo live through Oct 20 regardless |
| Real Gemini free-tier limits for your model | Sources conflict (20 vs 1,500 requests/day) | AI Studio rate-limit page for your project |
| Whether Public vs Unlisted is policed; whether 4:00 is enforced | Not in the rules | Choose Public; stay under 3:45 |
| Whether Render Free accepts your exact `render.yaml` keys; Render/Cloud Run commands | Docs blocked | Do the dashboard flow; test commands tonight |
| Dual submission to another hackathon | Rules silent | Ask organizers if it matters |
| Credit-redemption steps for sponsors | In packet / Discord | Not needed for the plan above |
| Whether all team members are on the Devpost project | Cannot see the draft | Check the Devpost project's team list tonight |

## 11. Sources and evidence

Read directly [D]:
- https://forgehacks-2026.devpost.com/ , /rules , /details/dates , /updates , /resources , /project-gallery (empty), /discussions (404), and updates `/updates/46776-forgehacks-is-live-track-prompts-and-your-participant-packet`, `/updates/46753-forgehacks-starts-tomorrow`, `/updates/45555-we-re-halfway-through-forgehacks`, `/updates/46756-24-hours-left`
- https://devpost.com/api/hackathons?search=forgehacks (submission_period_dates, registrations)
- 88 project pages under https://devpost.com/software/ (list in `evidence/forgehacks-2026-sampled-submissions.json`)
- https://cloud.google.com/run/pricing
- https://github.com/Eshaan1e24/lumen (cloned read-only; `git log`)
- The local repo `/home/user/Anhad23mahajan/lumen` (read only; copied to a scratch dir for the memory test)

Search excerpts only [S]: www.forgehacks.dev (prompts, tagline), eventopia.in listing, render.com/docs/free, render.com/free and the Render "platforms with a real free tier" article, Render community threads, jwatte.com Render review (Aug 2026 plan change), huggingface.co/docs/hub (spaces-overview, spaces-gpus), huggingface_hub space_runtime docs, discuss.huggingface.co threads 177580, 177629, 177957, 178731, docs.railway.com free-trial and pricing, Fly.io pricing write-ups (temps.sh, kuberns, costbench), Koyeb write-ups (snapdeploy.dev, agentdeals.dev), Vercel limits (vercel.com/docs/functions/limitations, community threads), AWS free-tier write-ups (infratally.com, i-programmer.info), Azure free/students pages, GitHub Codespaces billing docs, Oracle Always Free cut (infoq.com/news/2026/07, linuxiac), UptimeRobot terms write-ups (host-tracker.com, notifier.so), cron-job.org FAQ, GitHub Actions schedule write-ups, Gemini free-tier write-ups (memetik.ai, aipromptshub.co, tokenmix.ai and others; all secondary), Gemini model IDs (Google/Vertex pages, GitHub changelog), YouTube help articles 157177 and 6364458, Databricks community thread quoting Devpost staff on video hosts, Featherless docs/examples and OpenClaw provider page.

Files written by me:
- `/home/user/work/research/hackathon.md` (this report)
- `/home/user/work/research/evidence/devpost-*.txt` (text of the Overview, Rules, Dates, and update posts as fetched at the time stamped in `_fetched_at_utc.txt`), `devpost-iso-dates.txt`
- `/home/user/work/research/evidence/forgehacks-2026-sampled-submissions.json` (88 sampled public submissions)
- `/home/user/work/research/evidence/memtest.py` (memory/timing harness) and `guard_snippet.py` (tested rate limiter)
