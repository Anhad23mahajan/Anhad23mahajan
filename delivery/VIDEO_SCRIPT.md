# Demo video script (target 3:15, hard limit 4:00)

**Rules to meet:** 2 to 4 minutes, public on YouTube (set visibility to **Public**), shows the problem and how the project works. No copyrighted music. Test the link in an incognito window while logged out.

**Setup (10 min):** open the live site in Chrome at 100% zoom, hide the bookmarks bar, close other tabs and notifications, window about 1440x900. Record with Xbox Game Bar (Win+G, Record) or OBS Studio. Record the screen and your voice together. Do one practice run first. Speak slowly; about 150 words a minute. If you stumble, keep going or re-record only that section: you can join clips in Clipchamp (built into Windows 11).

**Have ready:** the NGO donations sample (it has the best story), and one messy spreadsheet to upload for the cleaning shot. A good one: `title_rows_total.xlsx` (after running `deliver.ps1` it is at `%USERPROFILE%\lumen-delivery\team\tests\fixtures\`; an Excel file with title rows on top and a TOTAL row at the bottom).

---

## 0:00 to 0:20. The problem (show the Lumen home page)

> "Small shops, NGOs and student clubs collect sales and donation data, but most of it never turns into a decision. Power BI and Tableau cost money and need training, and when you ask a chatbot about a spreadsheet you get an answer you can't check. This is our ForgeHacks AI plus Business entry: Lumen, free AI analytics that tells you what matters and shows its work."

## 0:20 to 0:55. Messy data goes in (upload the Excel file)

Click **Choose a file**, pick `title_rows_total.xlsx`. When the dashboard loads, scroll to **Data Preview** and click between **Raw Input** and **Cleaned Output**.

> "Real spreadsheets are messy. This one has title rows above the header and a TOTAL row at the bottom that would double-count everything. Lumen finds the real header, drops the total, fixes number and date formats, tells me what it changed in a data-health strip, and shows raw next to cleaned. If it guessed the wrong measure, I can pick another and everything recomputes."

## 0:55 to 1:40. Insights before you ask (click **Use another file**, then the NGO donations sample)

Point at the summary and findings. Open **Show the numbers** on the first spike.

> "Now a charity's three years of donations. Before I ask anything, Lumen has found a spike on 10 December 2024: about 81 times a normal day, and it names the cause, a single corporate gift of about 25 thousand dollars. These insights are computed in code, not guessed by an AI, and the numbers behind them are one click away."

Then scroll to **What changed** or the trend finding if present:

> "It also tells me what is growing, where I depend too heavily on one campaign, and gives me recommended next steps, each with a because line quoting the evidence, for example the donors who gave before and have gone quiet."

## 1:40 to 2:30. Ask in plain English, and see it checked (type a question)

Type: **Which campaign raised the most money?** (or any question you like). Press Ask. When the answer appears, open **How this was worked out**.

> "I ask in plain English. The AI writes a database query, but I don't have to trust it. Lumen checks it four ways, and I can see every check: the query is parsed and must be read-only; it runs in a sandbox with no file or network access; a second, differently written query has to return the same values; and every number in the explanation has to appear in the result. If a check fails, I'm told, and made-up numbers are thrown away."

If the AI is busy and you get an error: click one of the suggested questions instead. Say: "When the AI is unavailable, the sample questions still answer from stored queries run live on the data, with a clear banner."

## 2:30 to 2:55. Forecast (scroll to Forecast)

> "Lumen forecasts the next months. It chooses the method by testing on my own history, and tells me how it did against a simple guess, here beating the naive forecast. It shows ranges, not promises, and warns me when there is too little history to trust it."

## 2:55 to 3:15. Close (click **How answers are checked**, then show the README or GitHub page)

> "It's free and open source under the MIT licence. It runs without any AI key, it can be self-hosted so your data stays on your machine, and it has more than two hundred and fifty automated tests, including attacks against the query sandbox. Lumen turns business data into clear insights, forecasts and next steps, so people without an analyst can make better decisions. Thank you."

---

## After recording

1. Upload to YouTube: title **Lumen: free AI analytics that shows its work (ForgeHacks 2026)**; visibility **Public**; not "made for kids"; description: one line plus the GitHub and live links.
2. Wait for processing to finish. Open the link in an incognito window and watch the first ten seconds.
3. Check the length is under 4:00.
4. Send me the link if you want me to check the text on the description.
