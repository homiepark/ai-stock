"""End-to-end test for HTML site generation."""
from __future__ import annotations

from pathlib import Path

import ai_stock.report.daily as daily_module
from ai_stock.report.web import build_site


def _patched_pipeline(monkeypatch, synthetic_prices, sample_fundamentals):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fake_fetch_prices(stock, *args, **kwargs):
        seed = sum(ord(c) for c in stock.ticker) % 1000
        return synthetic_prices(seed=seed)

    monkeypatch.setattr(daily_module, "fetch_prices", fake_fetch_prices)
    monkeypatch.setattr(daily_module, "fetch_fundamentals", lambda s, *a, **k: sample_fundamentals)
    monkeypatch.setattr(daily_module, "fetch_market_cap",
                        lambda s, *a, **k: float(sum(ord(c) for c in s.ticker)) * 1e9)
    monkeypatch.setattr(daily_module, "fetch_macro", lambda *a, **k: {
        "DGS10": {"name": "US 10Y Yield", "value": 4.25, "change": 0.005},
        "VIXCLS": {"name": "VIX", "value": 14.2, "change": -0.02},
    })
    monkeypatch.setattr(daily_module, "fetch_news", lambda *a, **k: [])


def test_build_site_creates_index_archive_and_dated(monkeypatch, tmp_path: Path,
                                                     synthetic_prices, sample_fundamentals):
    _patched_pipeline(monkeypatch, synthetic_prices, sample_fundamentals)
    context = daily_module.assemble_daily_context(output_dir=tmp_path / "reports")
    site_dir = build_site(context, site_dir=tmp_path / "site")

    assert (site_dir / "index.html").exists()
    assert (site_dir / "archive.html").exists()
    assert (site_dir / f"{context['date']}.html").exists()
    assert (site_dir / ".nojekyll").exists()

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    # Spot check key UI elements
    assert "AI 투자 일일 리포트" in index_html
    assert "테마 랭킹" in index_html
    assert "종합 판정 매트릭스" in index_html
    assert "tailwindcss" in index_html.lower()  # CDN included
    # Mobile-first viewport
    assert 'name="viewport"' in index_html
    # Sortable table marker
    assert 'class="sortable' in index_html
    # At least one stock made it into the matrix
    assert "NVIDIA" in index_html or "한미반도체" in index_html


def test_archive_lists_multiple_dates(monkeypatch, tmp_path: Path,
                                      synthetic_prices, sample_fundamentals):
    """Run the build twice with different 'today' values; archive should list both."""
    _patched_pipeline(monkeypatch, synthetic_prices, sample_fundamentals)
    from datetime import datetime as dt
    site = tmp_path / "site"

    ctx_a = daily_module.assemble_daily_context(today=dt(2026, 5, 1), output_dir=tmp_path / "reports")
    build_site(ctx_a, site_dir=site)
    ctx_b = daily_module.assemble_daily_context(today=dt(2026, 5, 5), output_dir=tmp_path / "reports")
    build_site(ctx_b, site_dir=site)

    archive_html = (site / "archive.html").read_text(encoding="utf-8")
    assert "2026-05-01" in archive_html
    assert "2026-05-05" in archive_html
    # index.html shows the most recent
    index_html = (site / "index.html").read_text(encoding="utf-8")
    assert "2026-05-05" in index_html
    # 2026-05-01.html still around (archive page accumulates)
    assert (site / "2026-05-01.html").exists()
