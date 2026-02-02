from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .analyze import GeminiAssessment
from .scrape import TweetItem


HASHTAG_RE = re.compile(r"#([A-Za-z0-9_]{1,50})")
CASHTAG_RE = re.compile(r"\$([A-Za-z]{1,6})")


@dataclass(frozen=True)
class Report:
    ticker: str
    query: str
    tweet_count: int
    metrics: Dict[str, Any]
    assessment: Optional[GeminiAssessment]


def _extract_tags(pattern: re.Pattern[str], texts: Iterable[str]) -> Counter:
    counter: Counter = Counter()
    for text in texts:
        for tag in pattern.findall(text):
            counter[tag.upper()] += 1
    return counter


def compute_metrics(tweets: List[TweetItem]) -> Dict[str, Any]:
    if not tweets:
        return {
            "avg_likes": 0,
            "avg_retweets": 0,
            "avg_replies": 0,
            "unique_users": 0,
            "top_hashtags": [],
            "top_cashtags": [],
        }

    avg_likes = sum(t.like_count for t in tweets) / len(tweets)
    avg_retweets = sum(t.retweet_count for t in tweets) / len(tweets)
    avg_replies = sum(t.reply_count for t in tweets) / len(tweets)
    unique_users = len({t.username for t in tweets})
    texts = [t.content for t in tweets]

    hashtags = _extract_tags(HASHTAG_RE, texts).most_common(5)
    cashtags = _extract_tags(CASHTAG_RE, texts).most_common(5)

    return {
        "avg_likes": round(avg_likes, 2),
        "avg_retweets": round(avg_retweets, 2),
        "avg_replies": round(avg_replies, 2),
        "unique_users": unique_users,
        "top_hashtags": [{"tag": tag, "count": count} for tag, count in hashtags],
        "top_cashtags": [{"tag": tag, "count": count} for tag, count in cashtags],
    }


def build_report(
    ticker: str,
    query: str,
    tweets: List[TweetItem],
    assessment: Optional[GeminiAssessment],
    metrics: Optional[Dict[str, Any]] = None,
) -> Report:
    if metrics is None:
        metrics = compute_metrics(tweets)
    return Report(
        ticker=ticker,
        query=query,
        tweet_count=len(tweets),
        metrics=metrics,
        assessment=assessment,
    )


def report_to_dict(report: Report) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ticker": report.ticker,
        "query": report.query,
        "tweet_count": report.tweet_count,
        "metrics": report.metrics,
        "assessment": None,
    }
    if report.assessment:
        payload["assessment"] = {
            "rating": report.assessment.rating,
            "confidence": report.assessment.confidence,
            "thesis": report.assessment.thesis,
            "risks": report.assessment.risks,
            "red_flags": report.assessment.red_flags,
            "sentiment_summary": report.assessment.sentiment_summary,
        }
    return payload


def format_report_text(report: Report) -> str:
    metrics = report.metrics
    lines = [
        "StockScout Report",
        "=" * 18,
        f"Ticker: {report.ticker}",
        f"Search query: {report.query}",
        f"Tweets analyzed: {report.tweet_count}",
        "",
        "Twitter Snapshot",
        "-" * 16,
        f"Avg likes: {metrics.get('avg_likes')}",
        f"Avg retweets: {metrics.get('avg_retweets')}",
        f"Avg replies: {metrics.get('avg_replies')}",
        f"Unique users: {metrics.get('unique_users')}",
        "",
        "Top hashtags: "
        + ", ".join(f"#{item['tag']}" for item in metrics.get("top_hashtags", []))
        if metrics.get("top_hashtags")
        else "Top hashtags: (none)",
        "Top cashtags: "
        + ", ".join(f"${item['tag']}" for item in metrics.get("top_cashtags", []))
        if metrics.get("top_cashtags")
        else "Top cashtags: (none)",
        "",
    ]

    if report.assessment:
        assessment = report.assessment
        lines += [
            "Gemini Assessment",
            "-" * 17,
            f"Rating: {assessment.rating} (confidence {assessment.confidence}%)",
            f"Sentiment summary: {assessment.sentiment_summary or 'N/A'}",
            f"Thesis: {assessment.thesis or 'N/A'}",
            "",
            "Risks:",
        ]
        if assessment.risks:
            lines += [f"- {risk}" for risk in assessment.risks]
        else:
            lines.append("- None provided.")
        lines += ["", "Red flags:"]
        if assessment.red_flags:
            lines += [f"- {flag}" for flag in assessment.red_flags]
        else:
            lines.append("- None provided.")
    else:
        lines += [
            "Gemini Assessment",
            "-" * 17,
            "Skipped. Provide GEMINI_API_KEY (or use --no-gemini).",
        ]

    lines += [
        "",
        "Disclaimer: This output is for informational purposes only and is not",
        "financial advice. Always do your own research.",
    ]
    return "\n".join(lines)


def format_report_json(report: Report) -> str:
    return json.dumps(report_to_dict(report), indent=2)
