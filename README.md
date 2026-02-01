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

## Usage

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

## Notes

- Twitter scraping is done via `snscrape`, which may be rate limited.
- The Gemini assessment is a sentiment summary, not investment advice.