bash

cat /home/claude/asin-review-vercel/api/check.py
Output

"""
Vercel serverless function: checks ONE ASIN per call.
Called as: /api/check?asin=B08XXXXXXX

Vercel functions are short-lived (no background jobs, no shared memory
between calls), so the frontend (public/index.html) loops over all the
ASINs and calls this endpoint once per ASIN, with a small delay between
calls, updating the progress bar as results come in.
"""

import json
import re
import random
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

TIMEOUT = 12
MAX_RETRIES = 2
RETRY_DELAY = 2.5  # seconds to wait before retrying within the same call

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 "
    "Firefox/126.0",
]


def fetch_asin_data(asin: str):
    url = f"https://www.amazon.in/dp/{asin}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            time.sleep(RETRY_DELAY)

        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            last_error = str(e)
            continue

        if resp.status_code != 200:
            last_error = f"HTTP {resp.status_code}"
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        title_el = soup.select_one("#productTitle")
        title = title_el.get_text(strip=True) if title_el else ""

        rating = ""
        rating_el = soup.select_one("#acrPopover") or soup.select_one(
            "span[data-hook='rating-out-of-text']"
        )
        if rating_el:
            rating_text = rating_el.get("title") or rating_el.get_text(strip=True)
            match = re.search(r"[\d.]+", rating_text or "")
            if match:
                rating = match.group()

        review_count = ""
        count_el = soup.select_one("#acrCustomerReviewText") or soup.select_one(
            "span[data-hook='total-review-count']"
        )
        if count_el:
            count_text = count_el.get_text(strip=True)
            match = re.search(r"[\d,]+", count_text)
            if match:
                review_count = match.group().replace(",", "")

        if not title and not rating and not review_count:
            last_error = "No data parsed (possible block/captcha or invalid ASIN)"
            continue

        return {
            "asin": asin,
            "title": title,
            "rating": rating,
            "review_count": review_count,
            "status": "OK",
            "error": "",
        }

    return {
        "asin": asin,
        "title": "",
        "rating": "",
        "review_count": "",
        "status": "FAILED",
        "error": last_error,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        asin = (query.get("asin", [""])[0] or "").strip().upper()

        if not asin:
            result = {
                "asin": "",
                "title": "",
                "rating": "",
                "review_count": "",
                "status": "FAILED",
                "error": "No ASIN provided",
            }
        else:
            result = fetch_asin_data(asin)

        body = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
