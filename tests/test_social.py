"""Tests for social adapter — ApeWisdom + influencer wiring (no real network)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import ai_stock.data.social as social_module
from ai_stock.data.social import (
    assemble_social_pulse,
    fetch_apewisdom_trending,
    load_influencers,
)


def test_load_influencers_has_all_categories():
    cfg = load_influencers()
    cats = {i["category"] for i in cfg["influencers"]}
    assert {"memecoin_alpha", "trader", "analyst", "founder", "narrative"} <= cats
    # User asked specifically for memecoin trend creators — ensure we have them
    handles = {i["handle"] for i in cfg["influencers"]}
    assert "blknoiz06" in handles  # Ansem
    assert "MustStopMurad" in handles  # Murad
    assert "cobie" in handles  # Cobie

    # Every entry must have weight ∈ 1..10
    for inf in cfg["influencers"]:
        assert 1 <= int(inf["weight"]) <= 10


def test_apewisdom_parses_response(monkeypatch):
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json = MagicMock(return_value={
        "results": [
            {"rank": 1, "ticker": "BTC", "name": "Bitcoin",
             "mentions": 500, "rank_24h_ago": 1, "mentions_24h_ago": 480},
            {"rank": 2, "ticker": "HYPE", "name": "Hyperliquid",
             "mentions": 300, "rank_24h_ago": 8, "mentions_24h_ago": 100},  # rising
            {"rank": 3, "ticker": "OLD", "name": "Old Coin",
             "mentions": 50, "rank_24h_ago": 2, "mentions_24h_ago": 200},  # falling
        ]
    })
    monkeypatch.setattr(social_module.requests, "get", lambda *a, **k: fake_response)

    out = fetch_apewisdom_trending(top_n=10)
    assert len(out) == 3
    btc, hype, old = out
    assert btc["ticker"] == "BTC"
    assert hype["is_rising"] is True   # 200% delta > 100% threshold
    assert old["is_rising"] is False
    assert old["delta_pct"] < 0


def test_apewisdom_handles_failure(monkeypatch):
    def fail(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(social_module.requests, "get", fail)
    out = fetch_apewisdom_trending(top_n=10)
    assert out == []


def test_assemble_social_pulse_shape(monkeypatch):
    """Even when ApeWisdom returns nothing, pulse dict is well-formed."""
    monkeypatch.setattr(social_module, "fetch_apewisdom_trending", lambda **k: [])
    monkeypatch.setattr(social_module, "fetch_influencer_tweets", lambda *a, **k: [])

    pulse = assemble_social_pulse()
    assert pulse["influencer_count"] >= 25
    assert "memecoin_alpha" in pulse["influencer_categories"]
    assert pulse["source_status"]["apewisdom"] == "fail"
    # Categories sorted by weight (highest first)
    memecoin_list = pulse["influencer_categories"]["memecoin_alpha"]
    weights = [int(m["weight"]) for m in memecoin_list]
    assert weights == sorted(weights, reverse=True)


def test_pulse_renders_in_coin_site(monkeypatch, tmp_path: Path,
                                    synthetic_prices, sample_fundamentals):
    """End-to-end: coin pipeline + social pulse appears in HTML."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import ai_stock.report.coin_daily as coin_daily_module
    import ai_stock.data.prices as prices_module

    monkeypatch.setattr(prices_module, "fetch_prices",
                        lambda s, *a, **k: synthetic_prices(seed=sum(ord(c) for c in s.ticker) % 1000, days=400))
    monkeypatch.setattr(coin_daily_module, "fetch_prices",
                        lambda s, *a, **k: synthetic_prices(seed=sum(ord(c) for c in s.ticker) % 1000, days=400))
    monkeypatch.setattr(coin_daily_module, "fetch_coin_market_caps",
                        lambda ids, *a, **k: {i: 1e10 for i in ids})
    monkeypatch.setattr(coin_daily_module, "fetch_global_snapshot",
                        lambda *a, **k: {"BTC_DOMINANCE": {"name": "BTC 도미넌스 (%)", "value": 56.2, "change": 0.0}})
    monkeypatch.setattr(coin_daily_module, "fetch_news", lambda *a, **k: [])
    monkeypatch.setattr(coin_daily_module, "assemble_social_pulse", lambda **k: {
        "trending": [
            {"ticker": "HYPE", "name": "Hyperliquid", "rank": 1, "rank_24h_ago": 5,
             "mentions": 500, "mentions_24h_ago": 100, "delta_pct": 400.0, "is_rising": True},
        ],
        "influencer_count": 30,
        "influencer_categories": {"memecoin_alpha": [
            {"handle": "blknoiz06", "name": "Ansem", "weight": 10, "note": "솔라나 밈코인 대장"}
        ]},
        "tweet_samples": [],
        "source_status": {"apewisdom": "ok", "twitter_rss": "disabled"},
    })

    ctx = coin_daily_module.assemble_coin_context(output_dir=tmp_path)
    from ai_stock.report.web import build_coin_site
    site = build_coin_site(ctx, site_dir=tmp_path / "site")
    html = (site / "coin.html").read_text(encoding="utf-8")

    assert "트위터 펄스" in html
    assert "RISING" in html
    assert "Ansem" in html
    assert "blknoiz06" in html
    assert "ApeWisdom" in html
