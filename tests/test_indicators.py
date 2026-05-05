import pandas as pd
import pytest

from ai_stock.signals.indicators import clamp_score, macd, momentum, rsi, sma, volume_zscore


def test_rsi_bounds(synthetic_prices):
    df = synthetic_prices()
    r = rsi(df["close"]).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_macd_columns(synthetic_prices):
    df = synthetic_prices()
    m = macd(df["close"])
    assert {"macd", "signal", "hist"} <= set(m.columns)
    assert len(m) == len(df)


def test_sma_length(synthetic_prices):
    df = synthetic_prices()
    s = sma(df["close"], 50)
    assert s.notna().sum() == len(df) - 49


def test_volume_zscore_zero_variance():
    v = pd.Series([1_000_000] * 50)
    z = volume_zscore(v, 20)
    # constant series → undefined std → NaN, not crash
    assert z.iloc[-1] != z.iloc[-1] or z.iloc[-1] == 0  # nan-tolerant


def test_momentum_5_period(synthetic_prices):
    df = synthetic_prices()
    m = momentum(df["close"], 5)
    expected = (df["close"].iloc[5] - df["close"].iloc[0]) / df["close"].iloc[0]
    assert m.iloc[5] == pytest.approx(expected, rel=1e-9)


def test_clamp_score():
    assert clamp_score(150) == 100
    assert clamp_score(-10) == 0
    assert clamp_score(50) == 50
    assert clamp_score(float("nan")) == 50.0
