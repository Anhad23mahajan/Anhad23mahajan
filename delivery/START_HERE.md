# Lumen: your checklist for Saturday, Oct 10

Deadline: **9:30 PM IST** (12:00 PM EDT). Aim to press Submit by **5:30 PM IST** so you have 4 hours of margin. A saved draft does not count: the status must say Submitted.

| # | When (IST) | What | Time needed | File |
|---|---|---|---|---|
| 1 | Now | Tell Eshaan you are about to push the finished code to `main` of Lumen. Install Git for Windows if `git --version` fails in PowerShell. | 5 min | |
| 2 | Now | Run `deliver.ps1` (commits the code under your name and pushes to Eshaan's repo). | 10 min | `deliver.ps1` |
| 3 | By 9:30 AM | Get your Gemini key (aistudio.google.com, Get API key). Deploy on Render. | 30 min | `DEPLOY_RENDER.md` |
| 4 | By 11:00 AM | Test the live site (steps are in the deploy file). Take 3 screenshots of the live site with the AI on: an answer showing all four green checks, the forecast box, and the insights panel. | 30 min | |
| 5 | 1:00 to 3:00 PM | Record the video, upload to YouTube as **Public**, test it in an incognito window. | 2 h | `VIDEO_SCRIPT.md` |
| 6 | 3:00 PM | Run `set-links.ps1` (puts the live URL and video URL into the README). | 5 min | `set-links.ps1` |
| 7 | 3:15 to 5:00 PM | Fill in Devpost: copy the text, add the images, check all four members are listed, track = AI + Business. | 1 h 30 min | `DEVPOST_TEXT.md` |
| 8 | By 5:30 PM | Submit. Reopen the project page and confirm it says **Submitted**. | 10 min | |
| 9 | After | Do NOT push anything else or redeploy. Keep the Render service alive until at least Oct 20. | | |

## If something goes wrong

- **A step fails:** copy the red error text (or a screenshot) and send it to me. Do not improvise on `main`.
- **Gemini quota or errors during the video:** Lumen falls back to stored sample questions with an honest banner. Record the AI part again later, or use the sample questions.
- **Render is slow to wake up:** the first visit after a quiet period takes about a minute. The keep-alive ping in the deploy file prevents it.
- **You run out of time:** the minimum valid submission is the public repo with its README, the public video, the written description and a screenshot. The live link is a bonus.

## The honest-claims rule

Everything in the README and the Devpost text has been checked against measurements. If you change wording, do not add claims such as "most accurate", "100% correct" or "fully secure". The project's strength is that it shows its checks and admits its limits.
