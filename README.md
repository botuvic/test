# Web Scraper Agent

A Python CLI agent that scrapes any URL, summarises the content with Claude (Anthropic), and saves the structured results to a JSON file.

## Features

- Fetches and cleans web page content (strips scripts, styles, nav, etc.)
- Extracts page title and meta description
- Sends content to **Claude** for AI-powered summarisation
- Returns structured output: `summary`, `key_points`, `topics`, `sentiment`
- Saves each run to a timestamped JSON file in `results/`

## Quickstart

```bash
# 1. Clone the repo and enter it
git clone https://github.com/your-org/web-scraper-agent.git
cd web-scraper-agent

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and set your ANTHROPIC_API_KEY

# 5. Run the scraper
python scraper.py https://example.com
```

## Output

Results are saved to `results/<timestamp>_<domain>.json`:

```json
{
  "url": "https://example.com",
  "scraped_at": "20240101T120000Z",
  "title": "Example Domain",
  "meta_description": "...",
  "domain": "example.com",
  "summary": "Example.com is a placeholder domain ...",
  "key_points": ["Point one", "Point two"],
  "topics": ["web", "placeholder"],
  "sentiment": "neutral"
}
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `OUTPUT_DIR` | No | `results` | Directory for JSON output |
| `MAX_CHARS` | No | `20000` | Max page characters sent to Claude |

## Project Structure

```
.
├── scraper.py        # Main agent
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── .gitignore
└── README.md
```

## Requirements

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)

## License

MIT
