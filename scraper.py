#!/usr/bin/env python3
"""
Web Scraper Agent
-----------------
Scrapes a URL, summarises the content using the Anthropic API,
and saves results to a timestamped JSON file.
"""

import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

import anthropic
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-5"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "results")
MAX_CHARS = int(os.getenv("MAX_CHARS", 20_000))   # clip huge pages before sending


# ---------------------------------------------------------------------------
# Scraping helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 15) -> str:
    """Download a web page and return cleaned plain text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; WebScraperAgent/1.0; "
            "+https://github.com/your-org/web-scraper-agent)"
        )
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)


def extract_metadata(url: str, raw_html: str) -> dict:
    """Pull <title> and <meta description> from the raw HTML."""
    soup = BeautifulSoup(raw_html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()
    return {"title": title, "meta_description": meta_desc, "domain": urlparse(url).netloc}


# ---------------------------------------------------------------------------
# Summarisation agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a precise research assistant. The user will provide raw text extracted
from a web page. Your job is to return a structured JSON object - nothing else -
with the following keys:

  summary       : A clear, neutral summary of the page (3-5 sentences).
  key_points    : A list of up to 7 bullet-point strings with the most
                  important facts or takeaways.
  topics        : A list of up to 5 topic/keyword strings.
  sentiment     : One of: positive | neutral | negative | mixed.

Output only valid JSON. No markdown fences, no extra text.
"""


def summarise(text: str, metadata: dict) -> dict:
    """Send page text to Claude and parse the structured JSON response."""
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and fill in your key."
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    clipped = text[:MAX_CHARS]
    if len(text) > MAX_CHARS:
        clipped += "\n\n[...content clipped for length...]"

    user_message = (
        f"Page title: {metadata.get('title', 'N/A')}\n"
        f"Domain: {metadata.get('domain', 'N/A')}\n\n"
        f"Content:\n{clipped}"
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_results(url: str, metadata: dict, analysis: dict) -> str:
    """Merge everything into one record and write to a JSON file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_domain = metadata.get("domain", "unknown").replace(".", "_")
    filename = f"{OUTPUT_DIR}/{timestamp}_{safe_domain}.json"

    record = {
        "url": url,
        "scraped_at": timestamp,
        **metadata,
        **analysis,
    }

    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)

    return filename


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(url: str) -> dict:
    """Full pipeline: fetch -> metadata -> summarise -> save."""
    print(f"[1/4] Fetching {url} ...")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebScraperAgent/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    raw_html = resp.text

    print("[2/4] Extracting metadata and text ...")
    metadata = extract_metadata(url, raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()
    clean_text = "\n".join(
        ln for ln in soup.get_text(separator="\n", strip=True).splitlines() if ln.strip()
    )

    print("[3/4] Summarising with Claude ...")
    analysis = summarise(clean_text, metadata)

    print("[4/4] Saving results ...")
    output_path = save_results(url, metadata, analysis)

    print(f"\n Done! Results saved to: {output_path}")
    print(json.dumps(analysis, indent=2))
    return {"output_path": output_path, **analysis}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <url>")
        sys.exit(1)
    run(sys.argv[1])
