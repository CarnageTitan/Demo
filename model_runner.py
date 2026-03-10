"""
Reusable model runner - returns JSON-serializable results for web app.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_fetcher import fetch_yfinance, fetch_stock_fundamentals
from src.quant_model import score_stock

DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "WMT", "JNJ", "PG", "UNH", "HD", "DIS", "NFLX", "AMD",
    "INTC", "CRM", "ADBE", "CSCO", "PEP", "KO", "COST", "XOM", "CVX",
    "ABBV", "MRK", "TMO", "ABT", "LLY", "PFE", "BAC", "GS", "MS",
]


def _safe_float(x):
    """Convert to JSON-serializable float."""
    if x is None:
        return None
    try:
        f = float(x)
        return round(f, 2) if abs(f) < 1e10 else f
    except (TypeError, ValueError):
        return None


def get_prices_and_volumes(price_data, tickers: list, symbol: str):
    import pandas as pd

    if price_data is None or price_data.empty:
        return None, None

    if len(tickers) == 1:
        prices = price_data["Close"] if "Close" in price_data.columns else None
        volumes = price_data["Volume"] if "Volume" in price_data.columns else None
        return prices, volumes

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


def run_model(tickers=None, top=50, min_score=0, period="1y"):
    """
    Run quant model and return list of stock results (JSON-serializable).
    """
    tickers = tickers or DEFAULT_WATCHLIST
    tickers = [t.upper().strip() for t in tickers if t and t.strip()]

    if not tickers:
        return {"error": "No tickers provided", "results": []}

    price_data = fetch_yfinance(tickers, period=period)
    if price_data is None or price_data.empty:
        return {"error": "Could not fetch price data", "results": []}

    fundamentals = fetch_stock_fundamentals(tickers)

    scores = []
    for symbol in tickers:
        prices, volumes = get_prices_and_volumes(price_data, tickers, symbol)
        fund = fundamentals.get(symbol, {})
        raw = score_stock(symbol, prices, volumes, fund)

        # Map to signal label
        s = raw["total_score"]
        if s >= 70:
            signal = "STRONG BUY"
        elif s >= 60:
            signal = "BUY"
        elif s >= 50:
            signal = "HOLD"
        else:
            signal = "WEAK"

        scores.append({
            "symbol": symbol,
            "total_score": _safe_float(raw["total_score"]),
            "signal": signal,
            "price": _safe_float(raw["price"]),
            "pe_ratio": _safe_float(raw["pe_ratio"]),
            "pb_ratio": _safe_float(raw["pb_ratio"]),
            "dividend_yield": _safe_float(raw["dividend_yield"]),
            "momentum_1m_pct": _safe_float(raw["momentum_1m_pct"]),
            "rsi": _safe_float(raw["rsi"]),
            "value_score": _safe_float(raw["value_score"]),
            "momentum_score": _safe_float(raw["momentum_score"]),
            "rsi_score": _safe_float(raw["rsi_score"]),
            "volume_score": _safe_float(raw["volume_score"]),
        })

    scores.sort(key=lambda x: x["total_score"] or 0, reverse=True)
    scores = [s for s in scores if (s["total_score"] or 0) >= min_score]
    scores = scores[:top]

    return {"error": None, "results": scores, "tickers_analyzed": len(tickers)}
