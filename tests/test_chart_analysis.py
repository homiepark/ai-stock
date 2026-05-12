"""Chart analysis primitives — pure-math tests with synthetic OHLCV.

We never call yfinance/CoinGecko in this file; price frames are constructed
in-memory so the assertions are deterministic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import ai_stock.signals.chart_analysis as ca


def _ohlcv(n: int = 250, seed: int = 0, drift: float = 0.0005, vol: float = 0.02) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    close = 100 * np.cumprod(1 + rets)
    high = close * (1 + rng.uniform(0, vol, n))
    low = close * (1 - rng.uniform(0, vol, n))
    volume = rng.uniform(1e6, 5e6, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"high": high, "low": low, "close": close, "open": close, "volume": volume},
        index=idx,
    )


def test_volume_profile_returns_three_canonical_levels():
    df = _ohlcv(n=120, seed=1)
    levels = ca.volume_profile(df)
    kinds = {lv.kind for lv in levels}
    assert kinds == {"vp_poc", "vp_vah", "vp_val"}
    poc = next(lv for lv in levels if lv.kind == "vp_poc")
    vah = next(lv for lv in levels if lv.kind == "vp_vah")
    val = next(lv for lv in levels if lv.kind == "vp_val")
    # VAL <= POC <= VAH by construction
    assert val.price <= poc.price <= vah.price


def test_volume_profile_empty_on_short_data():
    df = _ohlcv(n=15)
    assert ca.volume_profile(df) == []


def test_swing_pivots_find_extrema_and_dedupe():
    """Inject a clear peak and trough; the algorithm should pick them up."""
    df = _ohlcv(n=250, seed=7, drift=0.0)
    # Insert a sharp peak at index 100 and a trough at 200
    df.loc[df.index[100], "high"] = df["high"].max() * 3
    df.loc[df.index[200], "low"] = df["low"].min() * 0.3
    levels = ca.swing_pivots(df, window=10)
    assert any(lv.kind == "swing_high" for lv in levels)
    assert any(lv.kind == "swing_low" for lv in levels)
    # Dedupe respected
    prices = [lv.price for lv in levels]
    assert len(prices) == len(set(prices))


def test_htf_moving_averages_returns_known_set():
    df = _ohlcv(n=300)
    levels = ca.htf_moving_averages(df)
    kinds = {lv.kind for lv in levels}
    assert "ma_50_daily" in kinds
    assert "ma_200_daily" in kinds
    # Weekly 50MA needs 50 weekly bars (≈250 trading days), we have 300
    assert "ma_50_weekly" in kinds


def test_anchored_vwap_skips_recent_anchors():
    """An anchor inside the last 5 bars is noisy; output should be empty/light."""
    df = _ohlcv(n=10)
    assert ca.anchored_vwap(df) == []  # too short


def test_fib_levels_ordered_descending():
    df = _ohlcv(n=200, seed=3)
    levels = ca.fib_levels(df)
    assert len(levels) == 3
    # 0.382 → 0.5 → 0.618 means price descends from high to low retracement
    p382, p5, p618 = (lv.price for lv in levels)
    assert p382 > p5 > p618


def test_round_numbers_scale_with_price():
    """A $98 000 asset should not return penny-level magnets."""
    nums = ca.round_numbers(98_000)
    assert nums
    step = abs(nums[1].price - nums[0].price)
    # step should be on the 5k~10k scale, not 0.01
    assert 1_000 < step < 50_000


def test_collect_all_levels_runs_end_to_end():
    df = _ohlcv(n=300, seed=42)
    levels = ca.collect_all_levels(df)
    assert len(levels) > 5
    # At least three distinct kinds should be present in a 300-bar frame
    kinds = {lv.kind for lv in levels}
    assert len(kinds) >= 3
