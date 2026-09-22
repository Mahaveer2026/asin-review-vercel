# ASIN Review Checker (Vercel version)

Checks star rating + total review count for a list of Amazon.in ASINs
(parent + all child variations), and lets you download an Excel report
— hosted on Vercel so anyone can just open a link, no install needed.

## How it works

Vercel doesn't support long-running background jobs, so this version
works differently from a normal server:
- `api/check.py` is a small serverless function that checks **one**
  ASIN per call.
- `index.html` runs in the visitor's browser: it loops through the
  pasted/uploaded ASINs, calling `api/check.py` once per ASIN (with a
  short delay between calls), updating the progress bar and table live,
  and building the downloadable Excel file entirely in the browser at
  the end.

## Deploy to Vercel (no command line needed)

1. Create a free account at **github.com** if you don't have one.
2. Create a new repository (e.g. `asin-review-vercel`), set it to
   **Public**, and create it.
3. On the new repo's page, click **"uploading an existing file"** and
   drag in all the files from this folder (`index.html`, `vercel.json`,
   `requirements.txt`, and the `api` folder with `check.py` inside it).
   Commit the changes.
4. Create a free account at **vercel.com** — choose **"Continue with
   GitHub"** so the two accounts are linked.
5. On the Vercel dashboard, click **"Add New" → "Project"**, then
   select the `asin-review-vercel` repository you just created.
6. Leave the settings as default (Framework Preset: "Other") and click
   **Deploy**.
7. After a minute or two, Vercel gives you a live link like
   `https://asin-review-vercel.vercel.app` — share this with anyone;
   it works straight from the browser, nothing to install.

## A few things to know

- Because requests come from Vercel's shared cloud IPs (not your home
  connection), Amazon may rate-limit more aggressively than when
  running the tool locally — expect a higher number of "FAILED" rows
  on busy runs. Simply re-check the failed ASINs again later.
- There's a 300-ASIN limit per run in this version (Vercel functions
  have a short max execution time per call, so very large batches
  should be split — just run it again with the remaining ASINs).
- Keep the browser tab open while it's running — since the loop runs
  in the browser itself, closing the tab stops the checking.
