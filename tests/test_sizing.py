"""Position-sizing tests — formula correctness + safety paths."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ai_stock.signals.sizing import position_guidance


def _synthetic_prices(n: int = 60, seed: int = 0, vol: float = 0.02) -> pd.DataFrame:
    """Build a synthetic OHLC frame with a given daily-return volatility."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(0, vol, n)
    close = 100 * (1 + pd.Series(rets)).cumprod()
    high = close * (1 + rng.uniform(0, vol, n))
    low = close * (1 - rng.uniform(0, vol, n))
    return pd.DataFrame({"high": high, "low": low, "close": close})


def test_returns_none_when_data_insufficient():
    df = _synthetic_prices(n=10)
    assert position_guidance(df, "STRONG_BUY", "normal", "leader") is None


def test_strong_buy_leader_normal_gives_positive_pct():
    df = _synthetic_prices(n=60, vol=0.02)
    g = position_guidance(df, "STRONG_BUY", "normal", "leader")
    assert g is not None
    assert g.suggested_pct > 0
    assert g.suggested_pct <= 0.05  # never above the 5% cap
    assert g.stop_pct >= 0.02       # respects the 2% floor
    assert g.entry_price > 0
    assert g.stop_price < g.entry_price
    assert "ATR" in g.basis


def test_hold_label_zeros_position():
    df = _synthetic_prices(n=60, vol=0.02)
    g = position_guidance(df, "HOLD", "normal", "leader")
    assert g is not None
    assert g.suggested_pct == 0.0
    assert "비추천" in g.basis


def test_overheat_reduces_position():
    df = _synthetic_prices(n=60, vol=0.02, seed=42)
    g_normal = position_guidance(df, "STRONG_BUY", "normal", "leader")
    g_extreme = position_guidance(df, "STRONG_BUY", "extreme", "leader")
    assert g_normal and g_extreme
    assert g_extreme.suggested_pct < g_normal.suggested_pct


def test_leveraged_capped_at_3_pct():
    """A low-vol leader would otherwise hit the 5% cap; leverage flag drops it to 3%."""
    df = _synthetic_prices(n=60, vol=0.005, seed=7)  # very calm
    g = position_guidance(df, "STRONG_BUY", "normal", "leader", is_leveraged=True)
    assert g is not None
    assert g.suggested_pct <= 0.03
    assert "레버리지" in g.basis


def test_higher_volatility_yields_smaller_position():
    """When both inputs sit below the cap, more volatile name → smaller sizing.

    Use ACCUMULATE+supporting (factor 0.36) so the cap doesn't mask the
    volatility-based component for either input.
    """
    calm = _synthetic_prices(n=60, vol=0.025, seed=1)   # ATR ~3%
    wild = _synthetic_prices(n=60, vol=0.06, seed=1)    # ATR ~7%
    g_calm = position_guidance(calm, "ACCUMULATE", "normal", "supporting")
    g_wild = position_guidance(wild, "ACCUMULATE", "normal", "supporting")
    assert g_calm and g_wild
    assert g_wild.stop_pct > g_calm.stop_pct
    assert g_wild.suggested_pct < g_calm.suggested_pct
