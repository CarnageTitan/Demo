from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List

import snscrape.modules.twitter as sntwitter


@dataclass(frozen=True)
class TweetItem:
    id: int
    date: str
    username: str
    content: str
    like_count: int
    retweet_count: int
    reply_count: int
    url: str


@dataclass(frozen=True)
class ScrapeConfig:
    query: str
    limit: int
    days: int
    lang: str = "en"
    exclude_retweets: bool = True


def build_search_query(term: str, days: int, lang: str, exclude_retweets: bool) -> str:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    parts = [term, f"lang:{lang}", f"since:{since}"]
    if exclude_retweets:
        parts.append("-filter:retweets")
    return " ".join(parts)


def _iter_tweets(query: str) -> Iterable[TweetItem]:
    scraper = sntwitter.TwitterSearchScraper(query)
    for tweet in scraper.get_items():
        content = tweet.rawContent.replace("\n", " ").strip()
        yield TweetItem(
            id=tweet.id,
            date=tweet.date.isoformat(),
            username=tweet.user.username if tweet.user else "unknown",
            content=content,
            like_count=tweet.likeCount or 0,
            retweet_count=tweet.retweetCount or 0,
            reply_count=tweet.replyCount or 0,
            url=tweet.url,
        )


def scrape_tweets(config: ScrapeConfig) -> List[TweetItem]:
    if config.limit <= 0:
        return []
    query = build_search_query(
        config.query, config.days, config.lang, config.exclude_retweets
    )
    tweets: List[TweetItem] = []
    for tweet in _iter_tweets(query):
        tweets.append(tweet)
        if len(tweets) >= config.limit:
            break
    return tweets
