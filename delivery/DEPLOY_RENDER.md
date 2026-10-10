# Deploy Lumen on Render (free), step by step

Render's screens change over time, so a label may differ slightly from what is written here. I could not open Render from my environment, so these steps come from Render's documented flow plus the files in the repo. If a screen does not match, send me a screenshot.

**Before you start:** `deliver.ps1` has pushed the finished code to https://github.com/Eshaan1e24/Lumen (check that the repo shows files like `Dockerfile`, `app/`, `static/`).

## 1. Get a Gemini key (5 min)

1. Open https://aistudio.google.com and sign in with a personal Google account.
2. Click **Get API key**, then **Create API key** (choose "in new project" if asked). Copy it somewhere private. It starts with `AIza`.
3. Keep billing off. Never paste the key in chat, GitHub or a file in the repo.

## 2. Create the web service (10 min)

1. Go to https://dashboard.render.com, click **New +**, then **Web Service**.
2. Choose **Public Git Repository** (a tab or option) and paste `https://github.com/Eshaan1e24/Lumen`. Continue. (Using the public URL means Eshaan does not need to authorise anything.)
3. Fill in:
   - **Name:** `lumen`
   - **Region:** Singapore (closest to India)
   - **Branch:** `main`
   - **Language / Runtime:** Docker (Render finds the `Dockerfile` by itself)
   - **Root Directory:** leave empty
   - **Instance Type:** **Free**
4. Open **Environment Variables** (or Advanced) and add four variables:

   | Key | Value |
   |---|---|
   | `GEMINI_API_KEY` | your key |
   | `LUMEN_MAX_UPLOAD_MB` | `5` |
   | `LUMEN_MAX_CELLS` | `3000000` |
   | `LUMEN_TRUST_PROXY` | `1` |

5. Under **Advanced**: set **Health Check Path** to `/api/health`. Set **Auto-Deploy** to **No** (so a later push cannot break the live demo).
6. Click **Create Web Service**. The first build takes about 5 to 10 minutes. Wait for the status **Live**. Your address is shown at the top, like `https://lumen-xxxx.onrender.com`.

Do not add a payment card. If Render asks for one, stop and tell me.

## 3. Test it (15 min)

Open the address (the first load can take a minute). Check:

1. The page shows the three sample cards. Click **Campus shop sales**. A dashboard appears.
2. Type your own question, for example *Which region sold the most hoodies in 2025?* and click Ask. You should see a green **Checked** badge and four ticks under "How this was worked out". (If you see "Demo mode", the key is missing or wrong: check the `GEMINI_API_KEY` variable under **Environment**; Render restarts the service by itself when you save a variable.)
3. Click a suggested question. It must answer.
4. Scroll to the Forecast box. It must draw a chart and a "How this forecast was tested" box.
5. Upload a small CSV of your own (under 5 MB). It must load.
6. Open the address on your phone in a private tab and repeat step 1.

If anything fails, copy the last 30 lines of the **Logs** tab and send them to me.

## 4. Keep it awake (5 min)

Free services go to sleep after about 15 minutes without visitors. To prevent that, use a free pinger:

1. Create a free account at https://cron-job.org.
2. **Create cronjob**: title `lumen keepalive`, URL `https://YOUR-ADDRESS.onrender.com/api/health`, schedule **every 5 minutes**, method GET. Save.

(Do not use a pinger that sends HEAD requests: `/api/health` answers GET only.)

## 5. Take your live screenshots (15 min)

With the key set, take three screenshots of the live site for Devpost: (a) an AI answer with the green Checked badge and the checks list open, (b) the forecast box, (c) the findings panel with one "Show the numbers" open. These are more convincing than the demo-mode shots in the repo.

## 6. After you submit

- Do not redeploy or push to `main`.
- Render has maintenance planned for **Oct 14, 6:30 AM IST**. A short outage is possible, which is why the README and Devpost page also carry screenshots and the video.
- Leave the service running until at least Oct 20 (judging runs to about Oct 12 to 18). Afterwards you can delete the service and the Gemini key.

## Know the limits

- The free instance has 512 MB of memory: the 5 MB upload limit and the cap on total data held in memory are deliberate.
- The Gemini free tier has a daily limit that Google does not publish clearly. Lumen limits questions per visitor and in total per day, and falls back to stored sample questions when the AI is unavailable, so the demo keeps working.
