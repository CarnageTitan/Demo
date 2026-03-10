"""
Quantitative scoring model: Value, Momentum, and Quality factors.
Scores stocks 0-100; higher = stronger buy signal.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_rsi(prices: pd.Series, window: int = 14) -> float:
    """Compute Relative Strength Index. Returns 0-100."""
    if prices is None or len(prices) < window + 1:
        return 50.0  # Neutral default

    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50.0


def compute_momentum_score(prices: pd.Series) -> float:
    """
    Momentum score 0-100 based on price trajectory.
    Positive momentum = higher score.
    """
    if prices is None or len(prices) < 20:
        return 50.0

    returns_1m = (prices.iloc[-1] / prices.iloc[-21] - 1) * 100 if len(prices) >= 21 else 0
    returns_3m = (prices.iloc[-1] / prices.iloc[-63] - 1) * 100 if len(prices) >= 63 else 0
    returns_6m = (prices.iloc[-1] / prices.iloc[-126] - 1) * 100 if len(prices) >= 126 else 0

    # Weighted momentum: recent matters more
    momentum = 0.5 * returns_1m + 0.3 * returns_3m + 0.2 * returns_6m
    # Scale to 0-100: assume -20 to +20% is typical range
    score = 50 + np.clip(momentum * 2.5, -50, 50)
    return float(score)


def compute_volume_trend(volumes: pd.Series, window: int = 20) -> float:
    """Score 0-100: higher if volume is increasing (interest building)."""
    if volumes is None or len(volumes) < window * 2:
        return 50.0

    recent = volumes.iloc[-window:].mean()
    older = volumes.iloc[-window * 2 : -window].mean()
    if older == 0:
        return 50.0
    change_pct = (recent / older - 1) * 100
    score = 50 + np.clip(change_pct * 2, -50, 50)
    return float(score)


def value_score(pe: Optional[float], pb: Optional[float], div_yield: Optional[float]) -> float:
    """
    Value factor 0-100: lower P/E and P/B = higher score.
    Higher dividend yield = bonus.
    """
    score = 50.0

    if pe is not None and pe > 0 and pe < 100:
        # Prefer P/E 5-25 range; penalize extreme
        if 5 <= pe <= 15:
            score += 20
        elif 15 < pe <= 25:
            score += 10
        elif pe > 50:
            score -= 15
        elif pe < 5:
            score += 5  # Could be value trap, modest boost

    if pb is not None and pb > 0 and pb < 20:
        if pb <= 2:
            score += 15
        elif pb <= 4:
            score += 5
        elif pb > 8:
            score -= 10

    if div_yield is not None and div_yield > 0:
        score += min(div_yield * 500, 15)  # Cap bonus

    return float(np.clip(score, 0, 100))


def score_stock(
    symbol: str,
    prices: Optional[pd.Series],
    volumes: Optional[pd.Series],
    fundamentals: dict,
) -> dict:
    """
    Compute composite quant score for one stock.
    Returns dict with scores and metadata.
    """
    result = {
        "symbol": symbol,
        "total_score": 0.0,
        "value_score": 50.0,
        "momentum_score": 50.0,
        "rsi_score": 50.0,
        "volume_score": 50.0,
        "price": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "dividend_yield": None,
        "momentum_1m_pct": None,
        "rsi": None,
    }

    # Fundamentals
    pe = fundamentals.get("pe_ratio")
    pb = fundamentals.get("pb_ratio")
    div = fundamentals.get("dividend_yield")
    if div and div < 1:
        div = div  # Already decimal
    elif div and div >= 1:
        div = div / 100  # Convert from percentage

    result["pe_ratio"] = pe
    result["pb_ratio"] = pb
    result["dividend_yield"] = div

    # Value
    result["value_score"] = value_score(pe, pb, div)

    # Price for display
    if prices is not None and len(prices) > 0:
        result["price"] = float(prices.iloc[-1])

    # Momentum
    result["momentum_score"] = compute_momentum_score(prices) if prices is not None else 50.0
    if prices is not None and len(prices) >= 21:
        result["momentum_1m_pct"] = float((prices.iloc[-1] / prices.iloc[-21] - 1) * 100)

    # RSI (contrarian: 30-70 is good, avoid overbought >70)
    rsi_raw = compute_rsi(prices, 14) if prices is not None else 50.0
    result["rsi"] = rsi_raw
    if 30 <= rsi_raw <= 70:
        result["rsi_score"] = 70
    elif rsi_raw < 30:
        result["rsi_score"] = 80  # Oversold = potential buy
    else:
        result["rsi_score"] = 30  # Overbought = caution

    # Volume trend
    result["volume_score"] = compute_volume_trend(volumes) if volumes is not None else 50.0

    # Composite: 35% value, 35% momentum, 15% RSI, 15% volume
    result["total_score"] = (
        0.35 * result["value_score"]
        + 0.35 * result["momentum_score"]
        + 0.15 * result["rsi_score"]
        + 0.15 * result["volume_score"]
    )

    return result
