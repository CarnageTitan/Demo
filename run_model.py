#!/usr/bin/env python3
"""
Quant Trading Model - Stock Buy Recommendations

Uses free APIs (yfinance primary, Alpha Vantage optional) to fetch data
and scores stocks on Value, Momentum, RSI, and Volume factors.

Usage:
  python run_model.py                    # Analyze default watchlist
  python run_model.py AAPL MSFT GOOGL    # Analyze specific tickers
  python run_model.py --top 15           # Show top 15 recommendations
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_fetcher import fetch_yfinance, fetch_stock_fundamentals
from src.quant_model import score_stock

# Default watchlist: diversified large/mid caps across sectors
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "WMT", "JNJ", "PG", "UNH", "HD", "DIS", "NFLX", "AMD",
    "INTC", "CRM", "ADBE", "CSCO", "PEP", "KO", "COST", "XOM", "CVX",
    "ABBV", "MRK", "TMO", "ABT", "LLY", "PFE", "BAC", "GS", "MS",
]


def get_prices_and_volumes(price_data, tickers: list, symbol: str):
    """Extract Close and Volume series for a ticker from yfinance download result."""
    import pandas as pd

    if price_data is None or price_data.empty:
        return None, None

    # Single ticker: flat columns
    if len(tickers) == 1:
        prices = price_data["Close"] if "Close" in price_data.columns else None
        volumes = price_data["Volume"] if "Volume" in price_data.columns else None
        return prices, volumes

    # Multiple tickers: MultiIndex (Ticker, OHLCV)
    if isinstance(price_data.columns, pd.MultiIndex):
        lev0 = price_data.columns.get_level_values(0)
        if symbol in lev0:
            try:
                sub = price_data[symbol]
                prices = sub["Close"] if "Close" in sub.columns else None
                volumes = sub["Volume"] if "Volume" in sub.columns else None
                return prices, volumes
            except (KeyError, TypeError):
                pass
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Quant Trading Model - Stock Recommendations")
    parser.add_argument(
        "tickers",
        nargs="*",
        default=None,
        help="Stock symbols to analyze (default: built-in watchlist)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top recommendations to show (default: 10)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0,
        help="Minimum score to include (0-100, default: 0)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1y",
        help="History period for yfinance (default: 1y)",
    )
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else DEFAULT_WATCHLIST
    tickers = [t.upper() for t in tickers]

    print("=" * 60)
    print("  QUANT TRADING MODEL - Stock Buy Recommendations")
    print("=" * 60)
    print(f"\nFetching data for {len(tickers)} stocks (yfinance, no API key required)...")
    print()

    # Fetch price data
    price_data = fetch_yfinance(tickers, period=args.period)
    if price_data is None or price_data.empty:
        print("ERROR: Could not fetch price data. Check your connection and ticker symbols.")
        return 1

    # Fetch fundamentals
    fundamentals = fetch_stock_fundamentals(tickers)

    # Score each stock
    scores = []
    for symbol in tickers:
        prices, volumes = get_prices_and_volumes(price_data, tickers, symbol)
        fund = fundamentals.get(symbol, {})
        result = score_stock(symbol, prices, volumes, fund)
        scores.append(result)

    # Sort by total score descending
    scores.sort(key=lambda x: x["total_score"], reverse=True)

    # Filter by min score
    scores = [s for s in scores if s["total_score"] >= args.min_score]

    # Display
    print(f"{'Symbol':<8} {'Score':<7} {'Price':<10} {'P/E':<8} {'1M %':<8} {'RSI':<6} {'Signal'}")
    print("-" * 60)

    for s in scores[: args.top]:
        price_str = f"${s['price']:.2f}" if s["price"] else "N/A"
        pe_str = f"{s['pe_ratio']:.1f}" if s["pe_ratio"] else "N/A"
        mom_str = f"{s['momentum_1m_pct']:+.1f}%" if s["momentum_1m_pct"] is not None else "N/A"
        rsi_str = f"{s['rsi']:.0f}" if s["rsi"] is not None else "N/A"

        if s["total_score"] >= 70:
            signal = "STRONG BUY"
        elif s["total_score"] >= 60:
            signal = "BUY"
        elif s["total_score"] >= 50:
            signal = "HOLD"
        else:
            signal = "WEAK"

        print(f"{s['symbol']:<8} {s['total_score']:<7.1f} {price_str:<10} {pe_str:<8} {mom_str:<8} {rsi_str:<6} {signal}")

    print()
    print("Top picks to consider:")
    strong = [x["symbol"] for x in scores if x["total_score"] >= 65]
    if strong:
        print(f"  Strong candidates (score >= 65): {', '.join(strong[:5])}")
    print()
    print("Disclaimer: This is for research/education only. Not financial advice.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
