"""Social signal aggregator — multi-source 'Twitter pulse' for the coin tab.

Strategy:

1. **ApeWisdom API** (free, reliable) — gives mention rankings + 24h deltas
   for crypto symbols across reddit/twitter/discord. This is the workhorse
   of the system; it works without auth and surfaces 'rising trend' signals
   that would otherwise require expensive Twitter API access.

2. **Twitter RSS** (best-effort, often broken) — Nitter / RSSHub bridges.
   Most public Nitter instances are dead in 2026; RSSHub public instance
   is rate-limited. Anything we get is a bonus; failure is silent.

3. **Curated influencer weighting** — even without per-tweet data, we
   document who matters so the user can manually cross-reference, and
   future paid integrations (X API Pro $200/mo) can plug in cleanly.

Returns shape (consumed by coin_daily.py and rendered by site_report.html.j2):
    {
      "trending": [{"ticker", "name", "rank", "rank_24h_ago", "mentions",
                    "mentions_24h_ago", "delta_pct", "is_rising"}],
      "influencer_count": int,
      "influencer_categories": {"memecoin_alpha": [...], ...},
      "tweet_samples": [{"handle", "text", "ts"}],   # may be empty
      "source_status": {"apewisdom": "ok", "twitter_rss": "skipped"},
    }
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests
import yaml

from ai_stock.config import CONFIG_DIR
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)


def load_influencers(path: Path | None = None) -> dict[str, Any]:
    p = path or (CONFIG_DIR / "influencers.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def fetch_apewisdom_trending(top_n: int = 15, rising_threshold_pct: int = 100,
                              cache: DiskCache | None = None) -> list[dict[str, Any]]:
    """Fetch crypto social mentions ranked by ApeWisdom.

    Each row includes 24h-prior rank and mentions, so we can compute a
    `delta_pct` and flag fast-rising coins.
    """
    cache_key = f"apewisdom_trending_{top_n}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

    try:
        r = requests.get("https://apewisdom.io/api/v1.0/filter/all-crypto/page/1",
                         timeout=15, headers={"User-Agent": "ai-stock/0.1"})
        r.raise_for_status()
        results = (r.json() or {}).get("results", [])
    except Exception as e:
        log.warning("ApeWisdom fetch failed: %s", e)
        return []

    out: list[dict[str, Any]] = []
    for row in results[:top_n]:
        try:
            mentions = int(row.get("mentions", 0))
            mentions_24h_ago = int(row.get("mentions_24h_ago", 0) or 0)
            rank = int(row.get("rank", 0))
            rank_24h_ago = int(row.get("rank_24h_ago", 0) or 0)
        except (ValueError, TypeError):
            continue

        if mentions_24h_ago > 0:
            delta_pct = (mentions - mentions_24h_ago) / mentions_24h_ago * 100
        else:
            delta_pct = 100.0 if mentions > 0 else 0.0

        is_rising = delta_pct >= rising_threshold_pct or (
            rank_24h_ago > 0 and rank_24h_ago - rank >= 5
        )

        out.append({
            "ticker": row.get("ticker", ""),
            "name": row.get("name", ""),
            "rank": rank,
            "rank_24h_ago": rank_24h_ago,
            "mentions": mentions,
            "mentions_24h_ago": mentions_24h_ago,
            "delta_pct": delta_pct,
            "is_rising": is_rising,
        })

    if cache is not None and out:
        cache.set_json(cache_key, out)
    return out


def _try_rsshub_handle(handle: str, instance: str, timeout: int = 8) -> list[dict[str, Any]]:
    """Best-effort fetch of a single Twitter handle's recent tweets via RSSHub.

    Returns empty list on any failure. This intentionally fails silent —
    public RSSHub instances are heavily rate-limited and frequently down.
    """
    try:
        import feedparser
    except ImportError:
        return []
    url = f"{instance.rstrip('/')}/twitter/user/{handle}"
    try:
        parsed = feedparser.parse(url)
        if not parsed.entries:
            return []
        out = []
        for e in parsed.entries[:5]:
            out.append({
                "handle": handle,
                "text": getattr(e, "title", "")[:280],
                "ts": getattr(e, "published", "") or getattr(e, "updated", ""),
                "link": getattr(e, "link", ""),
            })
        return out
    except Exception:
        return []


def fetch_influencer_tweets(influencers: list[dict[str, Any]],
                            twitter_rss_cfg: dict[str, Any] | None = None,
                            max_per_source: int = 30,
                            cache: DiskCache | None = None) -> list[dict[str, Any]]:
    """Best-effort tweet sample collection. Returns empty list if no source works."""
    if not twitter_rss_cfg or not twitter_rss_cfg.get("enabled"):
        return []

    cache_key = f"influencer_tweets_{len(influencers)}"
    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached

    rsshub = twitter_rss_cfg.get("rsshub_instance")
    if not rsshub:
        return []

    samples: list[dict[str, Any]] = []
    # Limit to highest-weight influencers to respect rate limits
    top = sorted(influencers, key=lambda i: -int(i.get("weight", 0)))[:10]
    for inf in top:
        if len(samples) >= max_per_source:
            break
        tweets = _try_rsshub_handle(inf["handle"], rsshub)
        samples.extend(tweets)

    if cache is not None and samples:
        cache.set_pickle(cache_key, samples)
    return samples


def assemble_social_pulse(cache: DiskCache | None = None) -> dict[str, Any]:
    """One-shot social signal assembly for the coin context."""
    cfg = load_influencers()
    influencers = cfg.get("influencers", [])

    apewisdom_cfg = cfg.get("apewisdom", {})
    trending = []
    if apewisdom_cfg.get("enabled", True):
        trending = fetch_apewisdom_trending(
            top_n=apewisdom_cfg.get("top_n", 15),
            rising_threshold_pct=apewisdom_cfg.get("rising_threshold_pct", 100),
            cache=cache,
        )

    tweet_samples = fetch_influencer_tweets(
        influencers,
        twitter_rss_cfg=cfg.get("twitter_rss", {}),
        cache=cache,
    )

    # Group influencers by category for the doc-style display
    categories: dict[str, list[dict[str, Any]]] = {}
    for inf in influencers:
        cat = inf.get("category", "other")
        categories.setdefault(cat, []).append(inf)
    for cat in categories:
        categories[cat].sort(key=lambda i: -int(i.get("weight", 0)))

    source_status = {
        "apewisdom": "ok" if trending else "fail",
        "twitter_rss": "ok" if tweet_samples else
            ("disabled" if not cfg.get("twitter_rss", {}).get("enabled") else "fail"),
    }

    return {
        "trending": trending,
        "influencer_count": len(influencers),
        "influencer_categories": categories,
        "tweet_samples": tweet_samples,
        "source_status": source_status,
    }
