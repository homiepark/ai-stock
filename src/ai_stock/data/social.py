"""Social signal aggregator — multi-source 'Twitter pulse' for the coin tab.

Strategy (in order of preference when configured):

1. **Sorsa API** (formerly TweetScout, paid $49~199/mo) — crypto-specific
   Twitter data. 50x cheaper + 20x higher rate limit than official X API,
   plus crypto-aware scoring (Sorsa Score) and bot detection. Activated
   when `sorsa.enabled: true` in config and `SORSA_API_KEY` env var set.

2. **ApeWisdom API** (free) — coin mention rankings + 24h deltas across
   reddit/twitter/discord. Always on by default.

3. **Twitter RSS** (free, best-effort) — Nitter / RSSHub bridges. Mostly
   broken in 2026; falls through silently.

4. **Curated influencer weighting** — manual list rendered as a clickable
   contact sheet so users can spot-check signals on X directly.

Returns shape (consumed by coin_daily.py and rendered by site_report.html.j2):
    {
      "trending": [...ApeWisdom rows with delta_pct + is_rising...],
      "influencer_count": int,
      "influencer_categories": {"memecoin_alpha": [...], ...},
      "tweet_samples": [{"handle", "name", "text", "ts", "link", "score"}],
      "source_status": {"sorsa": "ok|disabled|fail", "apewisdom": ..., "twitter_rss": ...},
    }
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
import yaml

from ai_stock.config import CONFIG_DIR
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)

SORSA_BASE = "https://api.tweetscout.io/v2"


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


def fetch_sorsa_user_info(handle: str, api_key: str,
                           cache: DiskCache | None = None) -> dict[str, Any] | None:
    """Get Sorsa profile + crypto score for a single handle.

    Sorsa endpoint: GET /v2/info/{handle}
    Auth header: ApiKey: <key>
    Returns parsed dict or None on failure.
    """
    cache_key = f"sorsa_user_{handle}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

    try:
        r = requests.get(f"{SORSA_BASE}/info/{handle}",
                         headers={"ApiKey": api_key, "User-Agent": "ai-stock/0.1"},
                         timeout=15)
        if r.status_code == 401:
            log.warning("Sorsa auth failed (check SORSA_API_KEY)")
            return None
        if r.status_code != 200:
            log.warning("Sorsa /info/%s returned %d", handle, r.status_code)
            return None
        data = r.json()
    except Exception as e:
        log.warning("Sorsa user info failed for %s: %s", handle, e)
        return None

    if cache is not None:
        cache.set_json(cache_key, data)
    return data


def fetch_sorsa_user_tweets(handle: str, api_key: str, count: int = 5,
                             cache: DiskCache | None = None) -> list[dict[str, Any]]:
    """Get recent tweets for a handle via Sorsa.

    Sorsa endpoint: GET /v2/user-tweets/{handle}?count={N}
    Returns list of {handle, name, text, ts, link, retweets, likes}.
    """
    cache_key = f"sorsa_tweets_{handle}_{count}"
    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached

    try:
        r = requests.get(f"{SORSA_BASE}/user-tweets/{handle}",
                         params={"count": count},
                         headers={"ApiKey": api_key, "User-Agent": "ai-stock/0.1"},
                         timeout=15)
        if r.status_code != 200:
            log.warning("Sorsa /user-tweets/%s returned %d", handle, r.status_code)
            return []
        raw = r.json()
    except Exception as e:
        log.warning("Sorsa tweets failed for %s: %s", handle, e)
        return []

    # Sorsa response shape varies; handle the common patterns
    tweets_arr = raw if isinstance(raw, list) else (raw.get("tweets") or raw.get("data") or [])
    out: list[dict[str, Any]] = []
    for t in tweets_arr[:count]:
        if not isinstance(t, dict):
            continue
        text = t.get("full_text") or t.get("text") or ""
        ts = t.get("created_at") or t.get("ts") or ""
        tid = t.get("id_str") or t.get("id") or ""
        out.append({
            "handle": handle,
            "text": text[:280],
            "ts": ts,
            "link": f"https://x.com/{handle}/status/{tid}" if tid else f"https://x.com/{handle}",
            "retweets": int(t.get("retweet_count", 0) or 0),
            "likes": int(t.get("favorite_count", 0) or t.get("likes", 0) or 0),
        })

    if cache is not None and out:
        cache.set_pickle(cache_key, out)
    return out


def fetch_sorsa_pulse(influencers: list[dict[str, Any]], sorsa_cfg: dict[str, Any],
                      cache: DiskCache | None = None) -> tuple[list[dict[str, Any]], str]:
    """Pull recent tweets from top-weighted influencers via Sorsa API.

    Returns (samples, status) where status is 'ok'|'disabled'|'no_key'|'fail'.
    """
    if not sorsa_cfg or not sorsa_cfg.get("enabled"):
        return [], "disabled"
    api_key = os.getenv("SORSA_API_KEY")
    if not api_key:
        return [], "no_key"

    tweets_per = int(sorsa_cfg.get("tweets_per_influencer", 5))
    min_score = float(sorsa_cfg.get("min_score", 0))

    # Highest-weight first; cap at 30 to bound monthly request cost
    top = sorted(influencers, key=lambda i: -int(i.get("weight", 0)))[:30]

    samples: list[dict[str, Any]] = []
    for inf in top:
        handle = inf["handle"]
        if min_score > 0:
            info = fetch_sorsa_user_info(handle, api_key, cache=cache)
            score = float((info or {}).get("score", 0) or 0)
            if score and score < min_score:
                continue  # skip low-trust accounts (likely paid bots)
        else:
            score = None

        tweets = fetch_sorsa_user_tweets(handle, api_key, count=tweets_per, cache=cache)
        for tw in tweets:
            samples.append({**tw, "name": inf.get("name", handle), "score": score,
                            "weight": inf.get("weight", 0)})

    # Sort by recency-ish proxy: weight × engagement
    def _sort_key(t: dict[str, Any]) -> float:
        return float(t.get("weight", 0)) * (1 + t.get("likes", 0) / 100 + t.get("retweets", 0) / 50)
    samples.sort(key=_sort_key, reverse=True)

    return samples, ("ok" if samples else "fail")


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

    # Sorsa first (paid, highest quality), fall through to RSS otherwise
    sorsa_cfg = cfg.get("sorsa", {})
    sorsa_samples, sorsa_status = fetch_sorsa_pulse(influencers, sorsa_cfg, cache=cache)

    rss_samples: list[dict[str, Any]] = []
    rss_status = "skipped"
    if not sorsa_samples:
        rss_samples = fetch_influencer_tweets(
            influencers,
            twitter_rss_cfg=cfg.get("twitter_rss", {}),
            cache=cache,
        )
        rss_cfg = cfg.get("twitter_rss", {})
        if not rss_cfg.get("enabled"):
            rss_status = "disabled"
        elif rss_samples:
            rss_status = "ok"
        else:
            rss_status = "fail"

    tweet_samples = sorsa_samples or rss_samples

    # Group influencers by category for display
    categories: dict[str, list[dict[str, Any]]] = {}
    for inf in influencers:
        cat = inf.get("category", "other")
        categories.setdefault(cat, []).append(inf)
    for cat in categories:
        categories[cat].sort(key=lambda i: -int(i.get("weight", 0)))

    source_status = {
        "sorsa": sorsa_status,
        "apewisdom": "ok" if trending else "fail",
        "twitter_rss": rss_status,
    }

    return {
        "trending": trending,
        "influencer_count": len(influencers),
        "influencer_categories": categories,
        "tweet_samples": tweet_samples,
        "source_status": source_status,
    }
