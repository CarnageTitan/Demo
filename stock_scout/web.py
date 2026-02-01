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
from .scrape import ScrapeConfig, build_search_query, scrape_tweets


app = FastAPI(title="StockScout")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


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
