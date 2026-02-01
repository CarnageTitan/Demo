from __future__ import annotations

import csv
from dataclasses import dataclass
from statistics import stdev
from typing import List, Optional, Tuple

from ..http import fetch_text


STOOQ_DAILY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"


@dataclass(frozen=True)
class PriceSummary:
    return_1m: Optional[float]
    return_6m: Optional[float]
    volatility_3m: Optional[float]
    latest_close: Optional[float]


def _stooq_symbol(ticker: str) -> str:
    return f"{ticker.lower().strip()}.us"


def _parse_prices(csv_text: str) -> List[Tuple[str, float]]:
    reader = csv.DictReader(csv_text.splitlines())
    prices: List[Tuple[str, float]] = []
    for row in reader:
        try:
            close = float(row.get("Close", "") or row.get("close", ""))
        except (TypeError, ValueError):
            continue
        date = row.get("Date", "") or row.get("date", "")
        if date:
            prices.append((date, close))
    return prices


def _calc_return(prices: List[Tuple[str, float]], lookback: int) -> Optional[float]:
    if len(prices) <= lookback:
        return None
    latest = prices[-1][1]
    prev = prices[-(lookback + 1)][1]
    if prev <= 0:
        return None
    return round(((latest - prev) / prev) * 100, 2)


def _calc_volatility(prices: List[Tuple[str, float]], window: int) -> Optional[float]:
    if len(prices) <= window:
        return None
    returns: List[float] = []
    for idx in range(-window, -1):
        prev = prices[idx - 1][1]
        curr = prices[idx][1]
        if prev <= 0:
            continue
        returns.append((curr - prev) / prev)
    if len(returns) < 2:
        return None
    return round(stdev(returns) * 100, 2)


def fetch_price_summary(ticker: str) -> PriceSummary:
    symbol = _stooq_symbol(ticker)
    result = fetch_text(STOOQ_DAILY_URL.format(symbol=symbol))
    if not result.ok or not result.text:
        return PriceSummary(None, None, None, None)
    prices = _parse_prices(result.text)
    if not prices:
        return PriceSummary(None, None, None, None)
    return PriceSummary(
        return_1m=_calc_return(prices, lookback=21),
        return_6m=_calc_return(prices, lookback=126),
        volatility_3m=_calc_volatility(prices, window=63),
        latest_close=prices[-1][1],
    )
