from pathlib import Path

import pytest

import ai_stock.report.adhoc as adhoc_module
from ai_stock.report.adhoc import _infer_stock


def test_infer_stock_us():
    s = _infer_stock("NVDA")
    assert s.country == "US" and s.ticker == "NVDA"


def test_infer_stock_kr():
    s = _infer_stock("005930")
    assert s.country == "KR" and s.ticker == "005930"


def test_analyze_arbitrary_ticker(monkeypatch, tmp_path: Path, synthetic_prices, sample_fundamentals):
    """End-to-end: arbitrary ticker → adhoc report file written."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    monkeypatch.setattr(adhoc_module, "fetch_prices", lambda stock, *a, **kw: synthetic_prices(seed=11))
    monkeypatch.setattr(adhoc_module, "fetch_fundamentals", lambda stock, *a, **kw: sample_fundamentals)
    monkeypatch.setattr(adhoc_module, "fetch_market_cap", lambda stock, *a, **kw: 1.5e12)
    monkeypatch.setattr(adhoc_module, "fetch_news", lambda *a, **kw: [])

    out = adhoc_module.analyze_ticker("AAPL", name="Apple", output_dir=tmp_path)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Apple" in text and "AAPL" in text
    assert "종합 판정" in text
    assert "기술적 스냅샷" in text


def test_analyze_raises_on_empty_prices(monkeypatch, tmp_path: Path):
    import pandas as pd
    monkeypatch.setattr(adhoc_module, "fetch_prices", lambda stock, *a, **kw: pd.DataFrame())
    with pytest.raises(RuntimeError, match="가격 데이터를 가져올 수 없습니다"):
        adhoc_module.analyze_ticker("BOGUS", output_dir=tmp_path)
