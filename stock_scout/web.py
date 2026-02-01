from __future__ import annotations

import html
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .analyze import analyze_with_gemini, get_api_key
from .cli import _build_default_term
from .report import (
    build_report,
    compute_metrics,
    format_report_text,
    report_to_dict,
)
from .rank import rank_stocks, rank_to_dict
from .scrape import ScrapeConfig, build_search_query, scrape_tweets


app = FastAPI(title="StockScout")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


DEFAULT_NEWS_RECORDS = _env_int("NEWS_RECORDS", 10)


def _page(content: str, title: str = "StockScout") -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; color: #111; }}
      h1 {{ margin-bottom: 0.25rem; }}
      form {{ display: grid; gap: 12px; max-width: 520px; }}
      label {{ font-weight: 600; }}
      input, select {{ padding: 8px; font-size: 14px; }}
      .row {{ display: grid; gap: 8px; grid-template-columns: 1fr 1fr; }}
      .actions {{ margin-top: 12px; }}
      .notice {{ background: #f5f5f5; padding: 12px; border-radius: 6px; }}
      pre {{ background: #0b0b0b; color: #f4f4f4; padding: 16px; border-radius: 6px; }}
      table {{ border-collapse: collapse; width: 100%; max-width: 900px; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background: #f0f0f0; }}
      textarea {{ padding: 8px; font-size: 14px; width: 100%; min-height: 80px; }}
      footer {{ margin-top: 24px; font-size: 12px; color: #555; }}
    </style>
  </head>
  <body>
    {content}
    <footer>
      Disclaimer: This output is for informational purposes only and is not
      financial advice.
    </footer>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    content = f"""
    <h1>StockScout</h1>
    <p>Scrape Twitter for stock chatter, then summarize with Gemini.</p>
    <p><a href="/rank">Try free-source stock ranking</a></p>
    <form method="post" action="/analyze">
      <div>
        <label for="ticker">Ticker</label>
        <input id="ticker" name="ticker" placeholder="TSLA" required />
      </div>
      <div>
        <label for="query">Custom query (optional)</label>
        <input id="query" name="query" placeholder="(TSLA OR $TSLA OR &quot;TSLA stock&quot;)" />
      </div>
      <div class="row">
        <div>
          <label for="limit">Tweet limit</label>
          <input id="limit" name="limit" type="number" min="5" max="200" value="50" />
        </div>
        <div>
          <label for="days">Days back</label>
          <input id="days" name="days" type="number" min="1" max="30" value="7" />
        </div>
      </div>
      <div class="row">
        <div>
          <label for="lang">Language</label>
          <input id="lang" name="lang" value="en" />
        </div>
        <div>
          <label for="model">Gemini model</label>
          <input id="model" name="model" value="{html.escape(DEFAULT_MODEL)}" />
        </div>
      </div>
      <div>
        <label>
          <input type="checkbox" name="include_retweets" />
          Include retweets
        </label>
      </div>
      <div>
        <label>
          <input type="checkbox" name="use_gemini" checked />
          Use Gemini assessment
        </label>
      </div>
      <div class="actions">
        <button type="submit">Analyze</button>
      </div>
    </form>
    """
    return HTMLResponse(_page(content))


@app.get("/rank", response_class=HTMLResponse)
def rank_form() -> HTMLResponse:
    content = f"""
    <h1>StockScout Rankings</h1>
    <p>Rank US stocks using free sources (SEC filings, Stooq prices, GDELT news).</p>
    <form method="post" action="/rank">
      <div>
        <label for="tickers">Tickers (comma-separated)</label>
        <textarea id="tickers" name="tickers" placeholder="AAPL, MSFT, AMZN"></textarea>
      </div>
      <div class="row">
        <div>
          <label for="news_records">News records per ticker</label>
          <input id="news_records" name="news_records" type="number" min="3" max="30" value="{DEFAULT_NEWS_RECORDS}" />
        </div>
      </div>
      <div class="actions">
        <button type="submit">Rank</button>
      </div>
    </form>
    """
    return HTMLResponse(_page(content))


@app.post("/rank", response_class=HTMLResponse)
def rank_submit(
    tickers: str = Form(...),
    news_records: int = Form(DEFAULT_NEWS_RECORDS),
) -> HTMLResponse:
    items = [item.strip() for item in tickers.split(",") if item.strip()]
    if not items:
        return HTMLResponse(_page("<p class='notice'>Provide at least one ticker.</p>"))

    rankings = rank_stocks(items, news_records=max(3, min(news_records, 30)))
    rows = []
    for rank in rankings:
        sig = rank.signals
        rows.append(
            "<tr>"
            f"<td>{html.escape(rank.ticker)}</td>"
            f"<td>{rank.score}</td>"
            f"<td>{rank.data_quality}</td>"
            f"<td>{sig.price_return_6m if sig.price_return_6m is not None else 'N/A'}</td>"
            f"<td>{sig.price_return_1m if sig.price_return_1m is not None else 'N/A'}</td>"
            f"<td>{sig.revenue_growth_1y if sig.revenue_growth_1y is not None else 'N/A'}</td>"
            f"<td>{sig.news_tone if sig.news_tone is not None else 'N/A'}</td>"
            f"<td>{sig.volatility_3m if sig.volatility_3m is not None else 'N/A'}</td>"
            "</tr>"
        )
    table = """
    <table>
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Score</th>
          <th>Data quality</th>
          <th>Return 6m %</th>
          <th>Return 1m %</th>
          <th>Revenue growth 1y %</th>
          <th>News tone</th>
          <th>Volatility 3m %</th>
        </tr>
      </thead>
      <tbody>
    """ + "".join(rows) + """
      </tbody>
    </table>
    """
    content = f"""
    <h1>StockScout Rankings</h1>
    <p><a href="/rank">Run another ranking</a></p>
    {table}
    <p class="notice">
      Scores are heuristic, based on free public data. They are not investment advice.
    </p>
    """
    return HTMLResponse(_page(content))


@app.post("/analyze", response_class=HTMLResponse)
def analyze(
    request: Request,
    ticker: str = Form(...),
    query: Optional[str] = Form(None),
    limit: int = Form(50),
    days: int = Form(7),
    lang: str = Form("en"),
    model: str = Form(DEFAULT_MODEL),
    include_retweets: Optional[str] = Form(None),
    use_gemini: Optional[str] = Form(None),
) -> HTMLResponse:
    ticker_clean = ticker.upper().strip()
    if not ticker_clean:
        return HTMLResponse(_page("<p class='notice'>Ticker is required.</p>"), status_code=400)

    term = query.strip() if query and query.strip() else _build_default_term(ticker_clean)
    config = ScrapeConfig(
        query=term,
        limit=max(1, min(limit, 500)),
        days=max(1, min(days, 60)),
        lang=lang.strip() or "en",
        exclude_retweets=not bool(include_retweets),
    )
    full_query = build_search_query(term, config.days, config.lang, config.exclude_retweets)

    try:
        tweets = scrape_tweets(config)
    except Exception as exc:
        error = html.escape(str(exc))
        return HTMLResponse(_page(f"<p class='notice'>Scrape failed: {error}</p>"), status_code=500)

    metrics = compute_metrics(tweets)
    assessment = None
    if use_gemini:
        api_key = get_api_key()
        if api_key:
            try:
                assessment = analyze_with_gemini(
                    ticker=ticker_clean,
                    query=full_query,
                    metrics=metrics,
                    tweets=tweets,
                    model_name=model or DEFAULT_MODEL,
                    api_key=api_key,
                )
            except Exception as exc:
                error = html.escape(str(exc))
                notice = f"<p class='notice'>Gemini failed: {error}</p>"
                report = build_report(ticker_clean, full_query, tweets, assessment, metrics=metrics)
                text = html.escape(format_report_text(report))
                return HTMLResponse(_page(notice + f"<pre>{text}</pre>"))
        else:
            assessment = None

    report = build_report(ticker_clean, full_query, tweets, assessment, metrics=metrics)
    report_text = html.escape(format_report_text(report))
    content = f"""
    <h1>StockScout</h1>
    <p><a href="/">Run another search</a></p>
    <pre>{report_text}</pre>
    """
    return HTMLResponse(_page(content))


@app.get("/api/analyze")
def analyze_api(
    ticker: str,
    query: Optional[str] = None,
    limit: int = 50,
    days: int = 7,
    lang: str = "en",
    include_retweets: bool = False,
    use_gemini: bool = True,
    model: str = DEFAULT_MODEL,
) -> JSONResponse:
    ticker_clean = ticker.upper().strip()
    term = query.strip() if query and query.strip() else _build_default_term(ticker_clean)
    config = ScrapeConfig(
        query=term,
        limit=max(1, min(limit, 500)),
        days=max(1, min(days, 60)),
        lang=lang.strip() or "en",
        exclude_retweets=not include_retweets,
    )
    full_query = build_search_query(term, config.days, config.lang, config.exclude_retweets)
    tweets = scrape_tweets(config)
    metrics = compute_metrics(tweets)
    assessment = None
    if use_gemini:
        api_key = get_api_key()
        if api_key:
            assessment = analyze_with_gemini(
                ticker=ticker_clean,
                query=full_query,
                metrics=metrics,
                tweets=tweets,
                model_name=model or DEFAULT_MODEL,
                api_key=api_key,
            )
    report = build_report(ticker_clean, full_query, tweets, assessment, metrics=metrics)
    return JSONResponse(report_to_dict(report))


@app.get("/api/rank")
def rank_api(
    tickers: str,
    news_records: int = DEFAULT_NEWS_RECORDS,
) -> JSONResponse:
    items = [item.strip() for item in tickers.split(",") if item.strip()]
    rankings = rank_stocks(items, news_records=max(3, min(news_records, 30)))
    return JSONResponse(
        {
            "rankings": [rank_to_dict(rank) for rank in rankings],
            "sources": ["SEC EDGAR", "Stooq", "GDELT"],
        }
    )
