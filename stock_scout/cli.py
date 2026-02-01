from __future__ import annotations

import argparse
import sys
from typing import Optional

from .analyze import analyze_with_gemini, get_api_key
from .report import build_report, compute_metrics, format_report_json, format_report_text
from .scrape import ScrapeConfig, build_search_query, scrape_tweets


DEFAULT_MODEL = "gemini-1.5-flash"


def _build_default_term(ticker: str) -> str:
    symbol = ticker.upper()
    return f'({symbol} OR ${symbol} OR "{symbol} stock")'


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape Twitter for stock chatter and analyze with Gemini."
    )
    parser.add_argument("--ticker", "-t", required=True, help="Stock ticker symbol.")
    parser.add_argument(
        "--query",
        help="Custom Twitter search term. Defaults to a ticker-based query.",
    )
    parser.add_argument("--limit", type=int, default=50, help="Number of tweets to pull.")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="How many days back to search for tweets.",
    )
    parser.add_argument("--lang", default="en", help="Tweet language (default: en).")
    parser.add_argument(
        "--include-retweets",
        action="store_true",
        help="Include retweets in results.",
    )
    parser.add_argument(
        "--no-gemini",
        action="store_true",
        help="Skip Gemini assessment and only show tweet metrics.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = _parse_args(argv)
    ticker = args.ticker.upper().strip()
    if not ticker:
        print("Ticker cannot be empty.", file=sys.stderr)
        sys.exit(2)

    term = args.query or _build_default_term(ticker)
    config = ScrapeConfig(
        query=term,
        limit=args.limit,
        days=args.days,
        lang=args.lang,
        exclude_retweets=not args.include_retweets,
    )
    full_query = build_search_query(term, config.days, config.lang, config.exclude_retweets)

    try:
        tweets = scrape_tweets(config)
    except Exception as exc:
        print(f"Failed to scrape tweets: {exc}", file=sys.stderr)
        sys.exit(1)

    metrics = compute_metrics(tweets)
    assessment = None
    if not args.no_gemini:
        api_key = get_api_key()
        if not api_key:
            print(
                "Missing GEMINI_API_KEY or GOOGLE_API_KEY. Skipping Gemini assessment.",
                file=sys.stderr,
            )
        else:
            try:
                assessment = analyze_with_gemini(
                    ticker=ticker,
                    query=full_query,
                    metrics=metrics,
                    tweets=tweets,
                    model_name=args.model,
                    api_key=api_key,
                )
            except Exception as exc:
                print(f"Gemini assessment failed: {exc}", file=sys.stderr)

    report = build_report(
        ticker=ticker,
        query=full_query,
        tweets=tweets,
        assessment=assessment,
        metrics=metrics,
    )

    if args.json:
        print(format_report_json(report))
    else:
        print(format_report_text(report))


if __name__ == "__main__":
    main()
