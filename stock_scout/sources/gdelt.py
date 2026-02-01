from __future__ import annotations

import json
from dataclasses import dataclass
from statistics import mean
from typing import List, Optional
from urllib.parse import quote_plus

from ..http import fetch_text


GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


@dataclass(frozen=True)
class NewsSummary:
    articles: List[dict]
    volume: int
    avg_tone: Optional[float]


def _build_query(ticker: str) -> str:
    ticker_clean = ticker.upper().strip()
    return (
        f'"{ticker_clean}" AND (stock OR shares OR earnings OR revenue OR guidance OR forecast)'
    )


def fetch_news_summary(ticker: str, maxrecords: int = 10) -> NewsSummary:
    query = quote_plus(_build_query(ticker))
    url = (
        f"{GDELT_DOC_URL}?query={query}&mode=ArtList&maxrecords={maxrecords}&format=json"
    )
    result = fetch_text(url)
    if not result.ok or not result.text:
        return NewsSummary([], 0, None)
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError:
        return NewsSummary([], 0, None)

    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    tones: List[float] = []
    for article in articles:
        tone = article.get("tone")
        try:
            tone_val = float(tone)
        except (TypeError, ValueError):
            continue
        tones.append(tone_val)
    avg_tone = round(mean(tones), 2) if tones else None
    return NewsSummary(articles=articles, volume=len(articles), avg_tone=avg_tone)
