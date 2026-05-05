"""News collector — RSS feeds + simple ticker matching.

Returns a list of dicts: {title, link, summary, published, source, matched_tickers, matched_names}.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from ai_stock.config import Stock
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)


@dataclass
class NewsItem:
    title: str
    link: str
    summary: str
    published: str
    source: str
    matched_tickers: list[str] = field(default_factory=list)
    matched_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__


def _build_match_patterns(stocks: Iterable[Stock]) -> list[tuple[Stock, re.Pattern]]:
    pats = []
    for s in stocks:
        # Match ticker as standalone word, plus the company name (case-insensitive, partial OK)
        ticker_re = re.compile(rf"\b{re.escape(s.ticker)}\b")
        # Use first word of name for matching to reduce false negatives
        first_word = s.name.split()[0]
        name_re = re.compile(re.escape(first_word), re.IGNORECASE)
        pats.append((s, ticker_re, name_re))
    return pats


def fetch_news(
    rss_feeds: list[str],
    stocks: list[Stock],
    max_articles: int = 200,
    cache: DiskCache | None = None,
) -> list[NewsItem]:
    cache_key = f"news_{datetime.utcnow().strftime('%Y%m%d_%H')}"
    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached

    import feedparser

    items: list[NewsItem] = []
    pats = _build_match_patterns(stocks)
    for url in rss_feeds:
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[: max_articles // max(len(rss_feeds), 1) + 1]:
                title = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                link = getattr(entry, "link", "")
                published = getattr(entry, "published", "") or getattr(entry, "updated", "")
                source = parsed.feed.get("title", url) if hasattr(parsed, "feed") else url

                blob = f"{title} {summary}"
                matched_t, matched_n = [], []
                for s, ticker_re, name_re in pats:
                    if ticker_re.search(blob) or name_re.search(blob):
                        matched_t.append(s.ticker)
                        matched_n.append(s.name)

                items.append(NewsItem(
                    title=title, link=link, summary=summary[:500], published=published,
                    source=source, matched_tickers=matched_t, matched_names=matched_n,
                ))
                if len(items) >= max_articles:
                    break
        except Exception as e:
            log.warning("rss fetch failed for %s: %s", url, e)
        if len(items) >= max_articles:
            break

    if cache is not None and items:
        cache.set_pickle(cache_key, items)
    return items
