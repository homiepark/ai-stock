"""Phase B/D unit tests — Binance derivatives + multi-TF synthesizer.

No network: every HTTP call is monkey-patched, and price series are
constructed inline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import ai_stock.data.derivatives as deriv
import ai_stock.signals.multi_tf as mtf


# --- derivatives -------------------------------------------------------------


def test_symbol_for_appends_usdt():
    assert deriv._symbol_for("BTC") == "BTCUSDT"
    assert deriv._symbol_for("eth") == "ETHUSDT"


def test_classify_bias_long_crowded():
    bias, note = deriv._classify_bias(0.0008, 1.8)
    assert bias == "long_crowded"
    assert "롱" in note


def test_classify_bias_short_crowded():
    bias, note = deriv._classify_bias(-0.0005, 0.45)
    assert bias == "short_crowded"
    assert "숏" in note


def test_classify_bias_neutral_when_both_in_normal_range():
    bias, note = deriv._classify_bias(0.0001, 1.0)
    assert bias == "neutral"
    assert "균형" in note


def test_fetch_derivatives_returns_none_when_symbol_missing(monkeypatch):
    """When Binance returns no funding rate, fetch_derivatives bails."""
    monkeypatch.setattr(deriv, "_funding_rate", lambda s: None)
    assert deriv.fetch_derivatives("UNKNOWNCOIN") is None


def test_fetch_derivatives_happy_path(monkeypatch):
    monkeypatch.setattr(deriv, "_funding_rate", lambda s: 0.0003)
    monkeypatch.setattr(deriv, "_long_short_ratio", lambda s: 1.2)
    monkeypatch.setattr(deriv, "_oi_change_24h", lambda s: 0.05)
    monkeypatch.setattr(deriv.time, "sleep", lambda *a, **kw: None)
    ctx = deriv.fetch_derivatives("BTC")
    assert ctx is not None
    assert ctx.symbol == "BTCUSDT"
    assert ctx.bias in ("neutral", "long_crowded", "short_crowded")
    assert abs(ctx.funding_rate_annual - 0.0003 * 3 * 365) < 1e-9


# --- multi_tf ---------------------------------------------------------------


def _series(n: int, start: float, daily_drift: float, seed: int = 0,
            vol: float = 0.005) -> pd.DataFrame:
    """Build a price series whose drift dominates the volatility, so the
    direction is unambiguous for trend classification."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(daily_drift, vol, n)
    close = start * np.cumprod(1 + rets)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame({"close": close}, index=idx)


def test_multi_tf_returns_none_on_empty():
    assert mtf.build_multi_tf(pd.DataFrame()) is None


def test_multi_tf_bullish_when_uptrend():
    # Strong drift, low noise — close ends ~3x start
    daily = _series(260, 100, +0.005, seed=1, vol=0.003)
    ctx = mtf.build_multi_tf(daily)
    assert ctx is not None
    assert ctx.bias_score >= 1
    # Each emitted TF has a trend label
    for tf in ctx.timeframes:
        assert tf["trend"] in ("up", "down", "neutral")


def test_multi_tf_bearish_when_downtrend():
    daily = _series(260, 100, -0.004, seed=2, vol=0.003)
    ctx = mtf.build_multi_tf(daily)
    assert ctx is not None
    assert ctx.bias_score <= -1


def test_multi_tf_uses_4h_when_given():
    daily = _series(260, 100, +0.001, seed=3)
    # 4h bars: 30 days × 6 bars/day = 180
    rng = np.random.default_rng(11)
    rets = rng.normal(0.0005, 0.01, 180)
    close4h = 100 * np.cumprod(1 + rets)
    idx4h = pd.date_range("2026-05-01", periods=180, freq="4h")
    h4 = pd.DataFrame({"close": close4h}, index=idx4h)
    ctx = mtf.build_multi_tf(daily, h4)
    assert ctx is not None
    tf_labels = {tf["timeframe"] for tf in ctx.timeframes}
    assert "4h" in tf_labels
