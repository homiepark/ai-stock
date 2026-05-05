"""End-to-end report generation with all network calls mocked.

This is the spot-check for `ai-stock daily` — proves the wiring from
data → signals → judge → render works without any external dependencies.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import ai_stock.report.daily as daily_module


@pytest.fixture
def patched_pipeline(monkeypatch, synthetic_prices, sample_fundamentals):
    """Stub every network-touching adapter."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_fetch_prices(stock, *args, **kwargs):
        # Vary seed by ticker so theme momentum differentiates stocks
        seed = sum(ord(c) for c in stock.ticker) % 1000
        return synthetic_prices(seed=seed)

    def fake_fetch_fundamentals(stock, *args, **kwargs):
        return sample_fundamentals

    def fake_fetch_market_cap(stock, *args, **kwargs):
        # Larger seed → larger cap, deterministic
        return float(sum(ord(c) for c in stock.ticker)) * 1e9

    def fake_fetch_macro(*args, **kwargs):
        return {
            "DGS10": {"name": "US 10Y Yield", "value": 4.25, "change": 0.005},
            "VIXCLS": {"name": "VIX", "value": 14.2, "change": -0.02},
            "USDKRW": {"name": "USD/KRW", "value": 1380.0, "change": 0.001},
        }

    def fake_fetch_news(*args, **kwargs):
        return []

    monkeypatch.setattr(daily_module, "fetch_prices", fake_fetch_prices)
    monkeypatch.setattr(daily_module, "fetch_fundamentals", fake_fetch_fundamentals)
    monkeypatch.setattr(daily_module, "fetch_market_cap", fake_fetch_market_cap)
    monkeypatch.setattr(daily_module, "fetch_macro", fake_fetch_macro)
    monkeypatch.setattr(daily_module, "fetch_news", fake_fetch_news)


def test_daily_report_generates(patched_pipeline, tmp_path: Path):
    out = daily_module.build_daily_report(output_dir=tmp_path)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    # Spot-check structure
    assert "AI 투자 일일 리포트" in text
    assert "매크로 스냅샷" in text
    assert "테마 랭킹" in text
    assert "종합 판정 매트릭스" in text
    assert "오늘의 주목 종목" in text
    # Some watchlist stock made it into the matrix
    assert "NVIDIA" in text or "한미반도체" in text
    # 5-stage label emoji should appear at least once
    assert any(e in text for e in ("🟢", "🟡", "⚪", "🟠", "🔴"))


def test_daily_report_writes_dated_filename(patched_pipeline, tmp_path: Path):
    out = daily_module.build_daily_report(output_dir=tmp_path)
    assert out.parent == tmp_path
    assert out.suffix == ".md"
    # YYYY-MM-DD.md
    assert len(out.stem) == 10 and out.stem.count("-") == 2
