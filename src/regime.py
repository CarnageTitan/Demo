"""
Simple market-regime overlay using VIX (retail-friendly, no paid data).
"""

from __future__ import annotations

from typing import Optional


def fetch_vix_close() -> Optional[float]:
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        data = yf.download("^VIX", period="1mo", interval="1d", progress=False)
        if data is None or data.empty:
            return None
        close = data["Close"]
        if hasattr(close, "iloc"):
            last = close.iloc[-1]
            return float(last) if last == last else None  # NaN check
        return float(close)
    except Exception:
        return None


def equity_multiplier(vix: Optional[float]) -> float:
    """
    Scale equity exposure down when fear is elevated. Returns (0.5, 1.0].
    If vix unknown, return 1.0 (fully invested).
    """
    if vix is None or vix != vix:
        return 1.0
    if vix >= 35:
        return 0.50
    if vix >= 28:
        return 0.65
    if vix >= 22:
        return 0.80
    if vix >= 18:
        return 0.92
    return 1.0
