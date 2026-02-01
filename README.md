# StockScout

StockScout is a small CLI app that scrapes Twitter for stock chatter, then
uses the Gemini API to summarize sentiment and potential risks. It outputs a
clear, easy-to-read report (or JSON if you prefer).

> Disclaimer: This project is for informational purposes only and is **not**
> financial advice.

## Features

- Scrape recent tweets for a ticker or custom query
- Quick metrics (engagement, unique users, hashtags)
- Gemini-based sentiment and risk summary
- Text or JSON output
- Free-source ranking (SEC filings, price data, news)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your Gemini API key:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Usage (CLI)

Basic usage:

```bash
python -m stock_scout --ticker TSLA --limit 50 --days 7
```

Skip Gemini (metrics only):

```bash
python -m stock_scout --ticker AAPL --no-gemini
```

JSON output:

```bash
python -m stock_scout --ticker NVDA --json
```

Custom query:

```bash
python -m stock_scout --ticker META --query '(META OR $META OR "Meta stock")'
```

## Web App

Run locally:

```bash
uvicorn stock_scout.web:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

API endpoint:

```
GET /api/analyze?ticker=TSLA&limit=50&days=7&use_gemini=true
```

Ranking endpoint (free sources):

```
GET /api/rank?tickers=AAPL,MSFT,AMZN
```

> Rankings are currently scoped to US tickers (Stooq `.us` symbols + SEC EDGAR).

### Deploy on Render

1. Create a **Web Service** from this repo.
2. Build command:
   ```bash
   pip install -r requirements.txt
   ```
3. Start command:
   ```bash
   uvicorn stock_scout.web:app --host 0.0.0.0 --port $PORT
   ```
4. Add your environment variables (see below).

## Environment Variables

- `GEMINI_API_KEY` (required for Gemini assessment)
- `GOOGLE_API_KEY` (alternative to `GEMINI_API_KEY`)
- `GEMINI_MODEL` (optional, default: `gemini-1.5-flash`)
- `SEC_USER_AGENT` (recommended for SEC EDGAR access; include contact email)
- `NEWS_RECORDS` (optional, default: `10`)
- `PORT` (Render provides this automatically)

## Accuracy & Limitations

- This is **not** financial advice. It is a sentiment snapshot based on public tweets.
- The ranking view uses free public sources (SEC filings, Stooq prices, GDELT news)
  and a simple heuristic score. Treat it as a starting point, not a decision.
- Twitter data can include bots, spam, and coordinated campaigns.
- Scrape results are limited by query size, time window, and rate limits.
- Gemini summaries can be incomplete or incorrect; treat them as a starting point,
  not a decision.

## Notes

- Twitter scraping is done via `snscrape`, which may be rate limited.
- The Gemini assessment is a sentiment summary, not investment advice.