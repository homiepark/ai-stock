"""Calendar — macro events filter + earnings safety paths.

We never hit yfinance in tests (the network call is monkeypatched out),
and the macro yaml is replaced with a tiny inline fixture so the test
isn't tied to the calendar year.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import ai_stock.data.calendar as cal


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "macro_calendar.yaml"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_macro_filters_invalid_dates(tmp_path):
    yaml_path = _write_yaml(tmp_path, """
events:
  - { date: "2026-08-12", name: "CPI (7월)", impact: high }
  - { date: "not-a-date", name: "broken" }
  - { date: "2026-09-16", name: "FOMC", impact: high }
""")
    events = cal.load_macro_events(yaml_path)
    assert len(events) == 2
    names = [e.name for e in events]
    assert "CPI (7월)" in names
    assert "FOMC" in names


def test_upcoming_events_windows_correctly(monkeypatch, tmp_path):
    yaml_path = _write_yaml(tmp_path, """
events:
  - { date: "2026-08-01", name: "before window", impact: med }
  - { date: "2026-08-10", name: "in window early", impact: high }
  - { date: "2026-08-13", name: "in window late", impact: med }
  - { date: "2026-08-25", name: "after window", impact: med }
""")
    today = date(2026, 8, 5)
    events = cal.upcoming_events(
        stocks=None, today=today, days_ahead=10,
        include_earnings=False, macro_path=yaml_path,
    )
    names = [e.name for e in events]
    assert names == ["in window early", "in window late"]
    # high impact ranked before med on same date — sanity check sort key
    assert events[0].impact == "high"


def test_earnings_skips_non_us_and_missing_yf(monkeypatch):
    """Coin / KR tickers must not call yfinance; yfinance errors are swallowed."""
    calls = []
    def fake_lookup(ticker):
        calls.append(ticker)
        return None  # simulate a fetch miss
    monkeypatch.setattr(cal, "_earnings_date_from_yf", fake_lookup)

    class _S:
        def __init__(self, ticker, country, tier="leader", name="x", theme="t"):
            self.ticker, self.country, self.tier, self.name, self.theme = (
                ticker, country, tier, name, theme,
            )

    stocks = [
        _S("NVDA", "US"),
        _S("005930", "KR"),         # must be skipped
        _S("BTC", "CRYPTO"),         # must be skipped
    ]
    events = cal.fetch_earnings_events(stocks, today=date(2026, 8, 1), cache=None)
    assert events == []
    # Only the US ticker should hit the lookup
    assert calls == ["NVDA"]
