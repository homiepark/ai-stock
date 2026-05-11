"""Unit tests for the CoinGecko price-history parser.

Regression coverage for the `.normalize()` bug — pandas 2.x's Series.dt
chain returns a Series, and `.normalize()` only exists on DatetimeIndex /
the `.dt` accessor. The pipeline used to call `.dt.tz_localize(None).normalize()`
which crashed on every coin fetch, taking down the whole coin run before any
per-coin try/except could fire.
"""
from __future__ import annotations

import pandas as pd
import pytest

import ai_stock.data.coin_prices as cp


class _Stock:
    """Minimal Stock stand-in for fetch_coin_prices."""
    ticker = "BTC"
    coingecko_id = "bitcoin"


def test_fetch_coin_prices_builds_datetime_index(monkeypatch):
    """The returned DataFrame must have a normalized DatetimeIndex
    (date-only, no tz) and the expected OHLCV columns."""
    base_ms = 1_700_000_000_000  # 2023-11-14 UTC
    one_day = 86_400_000
    fake_response = {
        "prices": [[base_ms + i * one_day, 100.0 + i] for i in range(5)],
        "total_volumes": [[base_ms + i * one_day, 1_000.0 + i] for i in range(5)],
    }
    monkeypatch.setattr(cp, "_request", lambda *a, **kw: fake_response)
    monkeypatch.setattr(cp, "_sleep_for_rate_limit", lambda: None)

    df = cp.fetch_coin_prices(_Stock(), days=30, cache=None)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is None
    # normalized → midnight times
    assert all(ts.hour == 0 and ts.minute == 0 for ts in df.index)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 5
    assert df["close"].iloc[0] == 100.0
    assert df["volume"].iloc[0] == 1000.0


def test_fetch_coin_prices_empty_on_request_failure(monkeypatch):
    monkeypatch.setattr(cp, "_request", lambda *a, **kw: None)
    monkeypatch.setattr(cp, "_sleep_for_rate_limit", lambda: None)
    df = cp.fetch_coin_prices(_Stock(), days=30, cache=None)
    assert df.empty
