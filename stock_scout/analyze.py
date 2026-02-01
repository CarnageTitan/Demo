from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .scrape import TweetItem


@dataclass(frozen=True)
class GeminiAssessment:
    rating: str
    confidence: int
    thesis: str
    risks: List[str]
    red_flags: List[str]
    sentiment_summary: str
    raw: Optional[str] = None


def get_api_key() -> Optional[str]:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _sample_tweets(tweets: Iterable[TweetItem], limit: int) -> List[str]:
    sampled: List[str] = []
    for tweet in tweets:
        if len(sampled) >= limit:
            break
        sampled.append(_clip(tweet.content, 280))
    return sampled


def _build_prompt(
    ticker: str,
    query: str,
    metrics: Dict[str, Any],
    tweets: List[TweetItem],
) -> str:
    samples = _sample_tweets(tweets, limit=25)
    tweets_block = "\n".join(f"- {text}" for text in samples) or "- No tweets found."
    return f"""
You are analyzing public Twitter sentiment about the stock ticker {ticker}.
Use the tweet samples and metrics below to provide a cautious assessment.
This is NOT financial advice. Focus on sentiment, credibility, and risks.

Return a JSON object with these keys:
rating: one of "bullish", "neutral", "bearish"
confidence: integer 0-100
thesis: short paragraph
risks: array of short bullet strings
red_flags: array of short bullet strings
sentiment_summary: short paragraph

Ticker: {ticker}
Search query: {query}
Metrics (from scraped tweets):
{json.dumps(metrics, indent=2)}

Tweet samples:
{tweets_block}
""".strip()


def _parse_response(text: str) -> GeminiAssessment:
    cleaned = text.strip()
    try:
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        payload = json.loads(cleaned[start:end])
    except Exception:
        return GeminiAssessment(
            rating="neutral",
            confidence=0,
            thesis="Unable to parse Gemini response. See raw output.",
            risks=["Response parsing failed."],
            red_flags=["Response parsing failed."],
            sentiment_summary="No summary available.",
            raw=cleaned,
        )

    rating = str(payload.get("rating", "neutral")).lower()
    if rating not in {"bullish", "neutral", "bearish"}:
        rating = "neutral"
    confidence = payload.get("confidence", 0)
    try:
        confidence_int = int(confidence)
    except (TypeError, ValueError):
        confidence_int = 0

    return GeminiAssessment(
        rating=rating,
        confidence=max(0, min(confidence_int, 100)),
        thesis=str(payload.get("thesis", "")).strip(),
        risks=[str(item).strip() for item in payload.get("risks", []) if str(item).strip()],
        red_flags=[
            str(item).strip()
            for item in payload.get("red_flags", [])
            if str(item).strip()
        ],
        sentiment_summary=str(payload.get("sentiment_summary", "")).strip(),
        raw=cleaned,
    )


def analyze_with_gemini(
    ticker: str,
    query: str,
    metrics: Dict[str, Any],
    tweets: List[TweetItem],
    model_name: str,
    api_key: Optional[str],
) -> GeminiAssessment:
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError(
            "google-generativeai is not installed. Install requirements.txt first."
        ) from exc

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    prompt = _build_prompt(ticker, query, metrics, tweets)
    response = model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else str(response)
    return _parse_response(text)
