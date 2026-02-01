from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .sources.edgar import EdgarSummary, fetch_edgar_summary
from .sources.gdelt import NewsSummary, fetch_news_summary
from .sources.stooq import PriceSummary, fetch_price_summary


@dataclass(frozen=True)
class StockSignals:
    ticker: str
    price_return_1m: Optional[float]
    price_return_6m: Optional[float]
    volatility_3m: Optional[float]
    latest_close: Optional[float]
    revenue_growth_1y: Optional[float]
    latest_10k: Optional[str]
    latest_10q: Optional[str]
    days_since_10k: Optional[int]
    days_since_10q: Optional[int]
    news_volume: int
    news_tone: Optional[float]


@dataclass(frozen=True)
class StockRank:
    ticker: str
    score: float
    data_quality: float
    signals: StockSignals


def _normalize(values: Dict[str, Optional[float]], invert: bool = False) -> Dict[str, Optional[float]]:
    clean = [val for val in values.values() if val is not None]
    if not clean:
        return {key: None for key in values}
    min_val = min(clean)
    max_val = max(clean)
    if min_val == max_val:
        normalized = {key: 0.5 if val is not None else None for key, val in values.items()}
    else:
        normalized = {
            key: ((val - min_val) / (max_val - min_val)) if val is not None else None
            for key, val in values.items()
        }
    if invert:
        return {
            key: (1 - val) if val is not None else None
            for key, val in normalized.items()
        }
    return normalized


def _collect_signals(ticker: str, news_records: int) -> StockSignals:
    price = fetch_price_summary(ticker)
    edgar = fetch_edgar_summary(ticker)
    news = fetch_news_summary(ticker, maxrecords=news_records)
    return StockSignals(
        ticker=ticker,
        price_return_1m=price.return_1m,
        price_return_6m=price.return_6m,
        volatility_3m=price.volatility_3m,
        latest_close=price.latest_close,
        revenue_growth_1y=edgar.revenue_growth_1y,
        latest_10k=edgar.latest_10k,
        latest_10q=edgar.latest_10q,
        days_since_10k=edgar.days_since_10k,
        days_since_10q=edgar.days_since_10q,
        news_volume=news.volume,
        news_tone=news.avg_tone,
    )


def rank_stocks(tickers: Iterable[str], news_records: int = 10) -> List[StockRank]:
    cleaned = []
    for ticker in tickers:
        ticker_clean = ticker.upper().strip()
        if ticker_clean and ticker_clean not in cleaned:
            cleaned.append(ticker_clean)

    signals: Dict[str, StockSignals] = {
        ticker: _collect_signals(ticker, news_records=news_records) for ticker in cleaned
    }

    returns_6m = {t: s.price_return_6m for t, s in signals.items()}
    returns_1m = {t: s.price_return_1m for t, s in signals.items()}
    revenue_growth = {t: s.revenue_growth_1y for t, s in signals.items()}
    news_tone = {t: s.news_tone for t, s in signals.items()}
    volatility = {t: s.volatility_3m for t, s in signals.items()}

    norm_returns_6m = _normalize(returns_6m)
    norm_returns_1m = _normalize(returns_1m)
    norm_revenue_growth = _normalize(revenue_growth)
    norm_news_tone = _normalize(news_tone)
    norm_volatility = _normalize(volatility, invert=True)

    weights = {
        "return_6m": 0.4,
        "return_1m": 0.2,
        "revenue_growth": 0.2,
        "news_tone": 0.1,
        "volatility": 0.1,
    }

    ranks: List[StockRank] = []
    for ticker, sig in signals.items():
        metrics: List[Tuple[Optional[float], float]] = [
            (norm_returns_6m.get(ticker), weights["return_6m"]),
            (norm_returns_1m.get(ticker), weights["return_1m"]),
            (norm_revenue_growth.get(ticker), weights["revenue_growth"]),
            (norm_news_tone.get(ticker), weights["news_tone"]),
            (norm_volatility.get(ticker), weights["volatility"]),
        ]
        score_total = 0.0
        weight_total = 0.0
        for value, weight in metrics:
            if value is None:
                continue
            score_total += value * weight
            weight_total += weight
        if weight_total > 0:
            score = round((score_total / weight_total) * 100, 2)
            data_quality = round(weight_total / sum(weights.values()), 2)
        else:
            score = 0.0
            data_quality = 0.0
        ranks.append(
            StockRank(
                ticker=ticker,
                score=score,
                data_quality=data_quality,
                signals=sig,
            )
        )

    ranks.sort(key=lambda item: item.score, reverse=True)
    return ranks


def rank_to_dict(rank: StockRank) -> Dict[str, object]:
    payload = asdict(rank.signals)
    return {
        "ticker": rank.ticker,
        "score": rank.score,
        "data_quality": rank.data_quality,
        "signals": payload,
    }
