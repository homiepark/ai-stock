"""End-to-end tests for the coin pipeline with all CoinGecko calls mocked."""
from __future__ import annotations

from pathlib import Path

import pytest

import ai_stock.report.coin_daily as coin_daily_module
import ai_stock.report.daily as daily_module
import ai_stock.data.prices as prices_module
import ai_stock.data.fundamentals as fund_module
from ai_stock.config import load_coin_universe
from ai_stock.report.coin_daily import assemble_coin_context, build_coin_report
from ai_stock.report.web import build_coin_site, build_site


def test_coin_universe_loads():
    u = load_coin_universe()
    assert len(u.themes) >= 6
    assert "ai" in u.themes
    assert "rwa" in u.themes
    assert "defi_revenue" in u.themes
    assert "depin" in u.themes  # added after Messari Theses 2026 research
    coins = u.all_stocks()
    assert all(c.country == "CRYPTO" for c in coins)
    assert all(c.coingecko_id for c in coins), "every coin must have coingecko_id"
    btc = u.find("BTC")
    assert btc is not None and btc.coingecko_id == "bitcoin"


@pytest.fixture
def patched_coin_pipeline(monkeypatch, synthetic_prices):
    """Stub every CoinGecko call so tests run offline + deterministic."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_fetch_prices(stock, *args, **kwargs):
        # 365-day window for coins (matches CoinGecko free tier limit)
        seed = sum(ord(c) for c in stock.ticker) % 1000
        return synthetic_prices(seed=seed, days=400)

    def fake_market_caps(coingecko_ids, *args, **kwargs):
        return {cg: float(sum(ord(c) for c in cg)) * 1e9 for cg in coingecko_ids}

    def fake_global(*args, **kwargs):
        return {
            "BTC_DOMINANCE": {"name": "BTC 도미넌스 (%)", "value": 56.2, "change": 0.0},
            "TOTAL_MCAP": {"name": "전체 시총 ($T)", "value": 3.45, "change": 0.012},
            "ETH_BTC": {"name": "ETH/BTC", "value": 0.0512, "change": -0.008},
        }

    monkeypatch.setattr(prices_module, "fetch_prices", fake_fetch_prices)
    monkeypatch.setattr(daily_module, "fetch_prices", fake_fetch_prices)
    monkeypatch.setattr(coin_daily_module, "fetch_prices", fake_fetch_prices)
    monkeypatch.setattr(coin_daily_module, "fetch_coin_market_caps", fake_market_caps)
    monkeypatch.setattr(coin_daily_module, "fetch_global_snapshot", fake_global)
    # fundamentals._fetch_crypto reads prices, which is now mocked. Fine to leave as-is.
    monkeypatch.setattr(coin_daily_module, "fetch_news", lambda *a, **k: [])


def test_assemble_coin_context_returns_expected_keys(patched_coin_pipeline, tmp_path: Path):
    ctx = assemble_coin_context(output_dir=tmp_path)
    assert ctx["asset_class"] == "coin"
    assert ctx["universe_size"] >= 25
    assert "BTC_DOMINANCE" in ctx["macro"]
    assert len(ctx["theme_rankings"]) >= 6
    assert len(ctx["verdicts"]) == ctx["universe_size"]
    assert len(ctx["focus"]) == 5  # default top_n_focus_stocks


def test_build_coin_report_writes_markdown(patched_coin_pipeline, tmp_path: Path):
    ctx = assemble_coin_context(output_dir=tmp_path)
    out = build_coin_report(output_dir=tmp_path, context=ctx)
    assert out.exists()
    assert out.name.startswith("coins-")
    text = out.read_text(encoding="utf-8")
    assert "AI 코인 일일 리포트" in text
    assert "글로벌 스냅샷" in text
    assert "BTC 도미넌스" in text
    # At least one of the watchlist coins shows up
    assert any(name in text for name in ("Bitcoin", "Hyperliquid", "Ondo", "Solana"))


def test_build_coin_site_writes_html(patched_coin_pipeline, tmp_path: Path):
    site = tmp_path / "site"
    ctx = assemble_coin_context(output_dir=tmp_path)
    build_coin_site(ctx, site_dir=site)
    coin_html = site / "coin.html"
    assert coin_html.exists()
    text = coin_html.read_text(encoding="utf-8")
    assert "AI 코인 일일 리포트" in text
    assert 'active_tab' not in text  # the variable name should be replaced, not leak
    # Coin tab should be highlighted, stock tab not
    assert 'href="./coin.html"' in text
    # Sortable verdict matrix preserved
    assert 'class="sortable' in text


def test_archive_combines_stock_and_coin_entries(patched_coin_pipeline, tmp_path: Path,
                                                  sample_fundamentals):
    """Both pipelines run on same site dir → archive lists both."""
    site = tmp_path / "site"

    # Stock side: re-use the patched stock pipeline shape from test_report_e2e
    # We need to mock those too for build_site
    import ai_stock.report.daily as d
    d.fetch_fundamentals = lambda s, *a, **k: sample_fundamentals
    d.fetch_market_cap = lambda s, *a, **k: float(sum(ord(c) for c in s.ticker)) * 1e9
    d.fetch_macro = lambda *a, **k: {"DGS10": {"name": "10Y", "value": 4.25, "change": 0.005}}
    d.fetch_news = lambda *a, **k: []

    stock_ctx = d.assemble_daily_context(output_dir=tmp_path)
    build_site(stock_ctx, site_dir=site)

    coin_ctx = assemble_coin_context(output_dir=tmp_path)
    build_coin_site(coin_ctx, site_dir=site)

    archive = (site / "archive.html").read_text(encoding="utf-8")
    assert "📈 주식" in archive
    assert "🪙 코인" in archive
