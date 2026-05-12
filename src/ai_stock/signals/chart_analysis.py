"""Chart-based support/resistance signals — the building blocks of trade plans.

Every function takes a daily OHLCV DataFrame (close at minimum, plus
high/low/volume where used) and returns concrete price levels with a
confidence score. Multiple independent signals can then be clustered
(see trade_plan.py) to find confluence zones.

Design notes:
  - Higher-time-frame signals score higher than recent-only signals
    because trader consensus + self-fulfilling effect is stronger.
  - Every level includes a `weight` (0..1) and `label` so the UI and
    backtest can see *why* a price matters, not just that it does.
  - We never fabricate levels: insufficient data → empty list. The
    confluence engine downstream tolerates sparse inputs gracefully.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


# Single-source-of-truth weights per signal type. Tuned for swing-trader
# bias: HTF MAs and Volume Profile POC outrank short-term swing pivots.
SIGNAL_WEIGHTS: dict[str, float] = {
    "weekly_high": 1.0,
    "weekly_low": 1.0,
    "vp_poc": 0.9,
    "vp_vah": 0.7,
    "vp_val": 0.7,
    "ma_200_daily": 0.85,
    "ma_50_daily": 0.65,
    "ma_50_weekly": 0.95,
    "anchored_vwap": 0.75,
    "swing_high": 0.55,
    "swing_low": 0.55,
    "fib_0_618": 0.6,
    "fib_0_5": 0.45,
    "fib_0_382": 0.35,
    "round_number": 0.3,
}


@dataclass
class ChartLevel:
    """A single S/R candidate."""
    price: float
    kind: str        # see SIGNAL_WEIGHTS keys
    label: str       # human-readable, e.g. "일봉 200MA"
    weight: float    # from SIGNAL_WEIGHTS, 0..1
    age_days: int    # 0 if computed from latest bar; older = staler

    def to_dict(self) -> dict:
        return self.__dict__


# --- Volume Profile ----------------------------------------------------------


def volume_profile(
    prices: pd.DataFrame,
    bins: int = 50,
    lookback: int = 90,
) -> list[ChartLevel]:
    """Return POC, VAH, VAL price levels from the last `lookback` daily bars.

    Distributes each day's volume uniformly across its high-low range, bins it,
    then derives Point of Control (highest-volume bin) and Value Area bounds
    (70% volume around POC).
    """
    if prices is None or prices.empty or len(prices) < 30:
        return []
    needed = {"high", "low", "volume"}
    if not needed.issubset(prices.columns):
        return []

    df = prices.tail(lookback).copy()
    pmin = float(df["low"].min())
    pmax = float(df["high"].max())
    if pmax <= pmin:
        return []

    edges = np.linspace(pmin, pmax, bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    vol_at = np.zeros(bins)

    # Uniform-spread approximation: each day adds its volume across the bins
    # that overlap with that day's [low, high] range.
    for _, row in df.iterrows():
        lo, hi, vol = float(row["low"]), float(row["high"]), float(row["volume"])
        if not np.isfinite(vol) or vol <= 0 or hi <= lo:
            continue
        # Find affected bin indices
        i0 = int(np.searchsorted(edges, lo, side="right") - 1)
        i1 = int(np.searchsorted(edges, hi, side="right") - 1)
        i0 = max(0, min(bins - 1, i0))
        i1 = max(0, min(bins - 1, i1))
        span = i1 - i0 + 1
        if span <= 0:
            continue
        vol_at[i0:i1 + 1] += vol / span

    total = vol_at.sum()
    if total <= 0:
        return []

    poc_idx = int(vol_at.argmax())
    poc_price = float(centers[poc_idx])

    # Expand around POC until 70% volume captured -> VAH / VAL
    target = 0.70 * total
    captured = vol_at[poc_idx]
    lo_i, hi_i = poc_idx, poc_idx
    while captured < target and (lo_i > 0 or hi_i < bins - 1):
        below = vol_at[lo_i - 1] if lo_i > 0 else -1
        above = vol_at[hi_i + 1] if hi_i < bins - 1 else -1
        if above >= below:
            hi_i += 1
            captured += vol_at[hi_i]
        else:
            lo_i -= 1
            captured += vol_at[lo_i]

    return [
        ChartLevel(
            price=poc_price,
            kind="vp_poc",
            label=f"Volume POC ({lookback}일)",
            weight=SIGNAL_WEIGHTS["vp_poc"],
            age_days=0,
        ),
        ChartLevel(
            price=float(centers[hi_i]),
            kind="vp_vah",
            label="Value Area High",
            weight=SIGNAL_WEIGHTS["vp_vah"],
            age_days=0,
        ),
        ChartLevel(
            price=float(centers[lo_i]),
            kind="vp_val",
            label="Value Area Low",
            weight=SIGNAL_WEIGHTS["vp_val"],
            age_days=0,
        ),
    ]


# --- Swing pivots ------------------------------------------------------------


def swing_pivots(
    prices: pd.DataFrame,
    window: int = 10,
    min_atr_separation: float = 1.5,
    max_levels: int = 6,
) -> list[ChartLevel]:
    """Return recent swing-high / swing-low levels.

    A swing high is a bar whose high is the max within ±window bars; same idea
    for swing low. Levels within `min_atr_separation × ATR` of each other are
    merged so we don't return clusters of near-identical pivots.
    """
    if prices is None or prices.empty or len(prices) < window * 2 + 10:
        return []
    if "high" not in prices.columns or "low" not in prices.columns:
        return []

    high = prices["high"].values
    low = prices["low"].values
    n = len(prices)
    atr = _atr_value(prices, 14) or 0
    sep = atr * min_atr_separation if atr > 0 else 0

    raw: list[ChartLevel] = []
    for i in range(window, n - window):
        if high[i] == high[i - window: i + window + 1].max():
            raw.append(ChartLevel(
                price=float(high[i]),
                kind="swing_high",
                label="Swing High",
                weight=SIGNAL_WEIGHTS["swing_high"],
                age_days=int(n - 1 - i),
            ))
        if low[i] == low[i - window: i + window + 1].min():
            raw.append(ChartLevel(
                price=float(low[i]),
                kind="swing_low",
                label="Swing Low",
                weight=SIGNAL_WEIGHTS["swing_low"],
                age_days=int(n - 1 - i),
            ))

    if not raw:
        return []

    # Prefer recent pivots; dedupe near-duplicates.
    raw.sort(key=lambda lv: lv.age_days)
    deduped: list[ChartLevel] = []
    for lv in raw:
        if any(abs(lv.price - d.price) < sep for d in deduped):
            continue
        deduped.append(lv)
        if len(deduped) >= max_levels:
            break
    return deduped


# --- Anchored VWAP -----------------------------------------------------------


def anchored_vwap(prices: pd.DataFrame, lookback: int = 90) -> list[ChartLevel]:
    """Anchored VWAPs from the most-recent significant cycle high and low.

    The cycle high is the bar with the maximum close in the lookback window;
    similarly cycle low. We then compute the volume-weighted mean price from
    that anchor through the latest bar. These lines act as strong S/R for the
    rest of the move (well-known TradingView convention).
    """
    if prices is None or prices.empty or len(prices) < 30:
        return []
    needed = {"close", "volume"}
    if not needed.issubset(prices.columns):
        return []

    df = prices.tail(lookback).copy()
    close = df["close"].values
    vol = df["volume"].values
    if vol.sum() <= 0:
        return []

    out: list[ChartLevel] = []
    high_pos = int(np.argmax(close))
    low_pos = int(np.argmin(close))

    def _vwap_from(anchor_idx: int, label: str) -> ChartLevel | None:
        segment_close = close[anchor_idx:]
        segment_vol = vol[anchor_idx:]
        if segment_vol.sum() <= 0:
            return None
        vwap = float((segment_close * segment_vol).sum() / segment_vol.sum())
        age = int(len(close) - 1 - anchor_idx)
        return ChartLevel(
            price=vwap,
            kind="anchored_vwap",
            label=f"Anchored VWAP ({label})",
            weight=SIGNAL_WEIGHTS["anchored_vwap"],
            age_days=age,
        )

    for idx, lab in ((high_pos, "고점 기준"), (low_pos, "저점 기준")):
        v = _vwap_from(idx, lab)
        if v is not None and v.age_days >= 5:  # too-recent anchors are noisy
            out.append(v)
    return out


# --- HTF moving averages -----------------------------------------------------


def htf_moving_averages(prices: pd.DataFrame) -> list[ChartLevel]:
    """Return current daily 50MA, 200MA, and weekly 50MA (when computable)."""
    if prices is None or prices.empty or "close" not in prices.columns:
        return []
    close = prices["close"]
    out: list[ChartLevel] = []

    if len(close) >= 50:
        out.append(ChartLevel(
            price=float(close.rolling(50).mean().iloc[-1]),
            kind="ma_50_daily", label="일봉 50MA",
            weight=SIGNAL_WEIGHTS["ma_50_daily"], age_days=0,
        ))
    if len(close) >= 200:
        out.append(ChartLevel(
            price=float(close.rolling(200).mean().iloc[-1]),
            kind="ma_200_daily", label="일봉 200MA",
            weight=SIGNAL_WEIGHTS["ma_200_daily"], age_days=0,
        ))

    # Weekly 50MA: resample to Friday closes
    try:
        weekly = close.resample("W-FRI").last().dropna()
        if len(weekly) >= 50:
            out.append(ChartLevel(
                price=float(weekly.rolling(50).mean().iloc[-1]),
                kind="ma_50_weekly", label="주봉 50MA",
                weight=SIGNAL_WEIGHTS["ma_50_weekly"], age_days=0,
            ))
    except Exception:
        pass
    return out


# --- Fibonacci retracements --------------------------------------------------


def fib_levels(prices: pd.DataFrame, lookback: int = 180) -> list[ChartLevel]:
    """0.382 / 0.5 / 0.618 retracements of the most recent swing range."""
    if prices is None or prices.empty or len(prices) < 30:
        return []
    if "high" not in prices.columns or "low" not in prices.columns:
        return []
    seg = prices.tail(lookback)
    hi = float(seg["high"].max())
    lo = float(seg["low"].min())
    if hi <= lo:
        return []
    rng = hi - lo
    return [
        ChartLevel(price=hi - 0.382 * rng, kind="fib_0_382", label="Fib 0.382",
                   weight=SIGNAL_WEIGHTS["fib_0_382"], age_days=0),
        ChartLevel(price=hi - 0.5 * rng, kind="fib_0_5", label="Fib 0.5",
                   weight=SIGNAL_WEIGHTS["fib_0_5"], age_days=0),
        ChartLevel(price=hi - 0.618 * rng, kind="fib_0_618", label="Fib 0.618",
                   weight=SIGNAL_WEIGHTS["fib_0_618"], age_days=0),
    ]


# --- Round-number magnets ----------------------------------------------------


def round_numbers(current_price: float, count: int = 3) -> list[ChartLevel]:
    """Generate ±count round-number levels around the current price.

    The magnitude scales with price: e.g. BTC at $98k → $90k/$100k/$110k,
    ETH at $3,500 → $3,000/$3,500/$4,000, alt at $0.45 → $0.40/$0.50/$0.60.
    """
    if current_price <= 0:
        return []
    # Step size: ~10% of current price, rounded to the nearest 1-2-5 scale.
    rough = current_price * 0.1
    mag = 10 ** np.floor(np.log10(rough))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= rough:
            step = m * mag
            break
    else:
        step = 10 * mag

    base = round(current_price / step) * step
    out = []
    for k in range(-count, count + 1):
        p = base + k * step
        if p <= 0:
            continue
        out.append(ChartLevel(
            price=float(p),
            kind="round_number",
            label=f"라운드 ${p:,.0f}" if p >= 10 else f"라운드 ${p:.2f}",
            weight=SIGNAL_WEIGHTS["round_number"],
            age_days=0,
        ))
    return out


# --- Helpers -----------------------------------------------------------------


def _atr_value(prices: pd.DataFrame, window: int = 14) -> float | None:
    """ATR scalar — same formula as signals/sizing._atr_pct, but absolute value."""
    if prices is None or prices.empty or len(prices) < window + 1:
        return None
    if not {"high", "low", "close"}.issubset(prices.columns):
        return None
    h = prices["high"]; l = prices["low"]; c = prices["close"]
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return float(tr.rolling(window).mean().iloc[-1])


def collect_all_levels(prices: pd.DataFrame) -> list[ChartLevel]:
    """Convenience: run every signal and return the merged level list."""
    if prices is None or prices.empty:
        return []
    out: list[ChartLevel] = []
    out.extend(htf_moving_averages(prices))
    out.extend(volume_profile(prices))
    out.extend(swing_pivots(prices))
    out.extend(anchored_vwap(prices))
    out.extend(fib_levels(prices))
    if "close" in prices.columns and len(prices):
        out.extend(round_numbers(float(prices["close"].iloc[-1])))
    return out
