"""
Stock data fetcher supporting yfinance (primary) and Alpha Vantage (optional).
yfinance: No API key needed, best for most use cases.
Alpha Vantage: Set ALPHA_VANTAGE_API_KEY env var. Free tier: 5 req/min, 25/day.
"""

import os
from typing import Optional
import pandas as pd


def fetch_yfinance(tickers: list[str], period: str = "1y") -> Optional[pd.DataFrame]:
    """Fetch historical price data using yfinance (no API key required)."""
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed. Run: pip install yfinance")
        return None

    try:
        data = yf.download(
            tickers,
            period=period,
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True,
        )
        return data
    except Exception as e:
        print(f"yfinance fetch error: {e}")
        return None


def fetch_stock_fundamentals(tickers: list[str]) -> dict:
    """Fetch fundamental data (P/E, P/B, etc.) using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        return {}

    results = {}
    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            fast_info = ticker.fast_info

            results[symbol] = {
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "avg_volume": info.get("averageVolume"),
                "volume": fast_info.last_volume if hasattr(fast_info, "last_volume") else info.get("volume"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
        except Exception as e:
            print(f"  Warning: Could not fetch fundamentals for {symbol}: {e}")
            results[symbol] = {}

    return results


def fetch_alpha_vantage(
    symbol: str,
    api_key: Optional[str] = None,
) -> Optional[dict]:
    """
    Fetch overview/quote from Alpha Vantage. Optional - requires free API key.
    Get key at: https://www.alphavantage.co/support/#api-key
    """
    api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return None

    try:
        import requests

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": api_key,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "Symbol" in data:
            return data
        return None
    except Exception as e:
        print(f"Alpha Vantage error for {symbol}: {e}")
        return None
