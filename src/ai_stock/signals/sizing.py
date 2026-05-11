"""Position sizing + stop-loss guidance based on ATR (Average True Range).

The label answers "Is this a good stock?" and overheat answers "Is now the
right time?" — this module answers "OK, how much do I buy and where do I
cut my losses?"

Formula (volatility-aware "1% rule"):

  ATR%        = ATR(14) / current_price
  stop_pct    = 2 × ATR%               # 2-ATR stop, classic swing-trader rule
  base_pct    = 1% / stop_pct          # weight so a 1-ATR adverse move = 1% loss

  suggested_pct = base_pct × label_factor × overheat_factor × tier_factor
                  capped at 5% (3% for leveraged ETFs)
                  zeroed for HOLD/TRIM/AVOID

Factors:
  label:    STRONG_BUY 1.0 | ACCUMULATE 0.6 | HOLD/TRIM/AVOID 0
  overheat: normal 1.0 | mild 0.7 | high 0.4 | extreme 0.2
  tier:     leader 1.0 | momentum 0.8 | supporting 0.6

This is portfolio-percentage guidance — multiply by your total investable
capital to get a dollar amount. The stop_pct tells you where to cut. A 5%
suggested weight + 6% stop loss means a max round-trip loss of 0.3% of
the portfolio on this single trade.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass
class PositionGuidance:
    suggested_pct: float    # 0.0~0.05 — fraction of total portfolio
    stop_pct: float         # 0.02~0.30 — drop from current price to cut
    atr_pct: float          # ATR / price
    entry_price: float      # current price (most recent close)
    stop_price: float       # entry × (1 - stop_pct)
    basis: str              # short Korean rationale string


_LABEL_FACTOR = {
    "STRONG_BUY": 1.0,
    "ACCUMULATE": 0.6,
    "HOLD": 0.0,
    "TRIM": 0.0,
    "AVOID": 0.0,
}

_OVERHEAT_FACTOR = {
    "normal": 1.0,
    "mild": 0.7,
    "high": 0.4,
    "extreme": 0.2,
}

_TIER_FACTOR = {
    "leader": 1.0,
    "momentum": 0.8,
    "supporting": 0.6,
}

_MAX_PCT_STANDARD = 0.05      # 5% single-name cap
_MAX_PCT_LEVERAGED = 0.03     # 3% for 2x/3x ETFs
_RISK_PER_TRADE = 0.01        # 1% rule
_STOP_ATR_MULTIPLE = 2.0      # 2-ATR stop


def _atr_pct(prices: pd.DataFrame, window: int = 14) -> tuple[float, float] | None:
    """Return (atr_pct, last_close). None if there's not enough data."""
    if prices is None or prices.empty or len(prices) < window + 1:
        return None
    needed = {"high", "low", "close"}
    if not needed.issubset(prices.columns):
        return None
    high = prices["high"]
    low = prices["low"]
    close = prices["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(window).mean().iloc[-1]
    last = close.iloc[-1]
    if not (math.isfinite(atr) and math.isfinite(last)) or last <= 0:
        return None
    return float(atr) / float(last), float(last)


def position_guidance(
    prices: pd.DataFrame,
    label: str,
    overheat_level: str = "normal",
    tier: str = "supporting",
    is_leveraged: bool = False,
) -> PositionGuidance | None:
    """Return per-stock position guidance, or None when inputs are insufficient.

    Inputs are kept generic — same function works for stock + coin pipelines.
    """
    pa = _atr_pct(prices)
    if pa is None:
        return None
    atr_pct, last = pa
    stop_pct = max(_STOP_ATR_MULTIPLE * atr_pct, 0.02)  # floor at 2%
    # Volatility-aware base sizing: weight inversely with stop width.
    base_pct = _RISK_PER_TRADE / stop_pct

    factor = (
        _LABEL_FACTOR.get(label, 0.0)
        * _OVERHEAT_FACTOR.get(overheat_level, 1.0)
        * _TIER_FACTOR.get(tier, 0.6)
    )

    max_cap = _MAX_PCT_LEVERAGED if is_leveraged else _MAX_PCT_STANDARD
    suggested = min(base_pct * factor, max_cap)
    if suggested < 0.001:
        suggested = 0.0  # round trivially small allocations to "don't bother"

    stop_price = last * (1 - stop_pct)

    if suggested <= 0:
        basis = "라벨/과열도 기준 신규 진입 비추천"
    else:
        basis = (
            f"ATR(14) {atr_pct * 100:.1f}% → 2-ATR 손절폭 {stop_pct * 100:.1f}%. "
            "포트폴리오의 1%만 risk-on (1번 손절 = 자산 1% 손실)."
        )
        if is_leveraged:
            basis += " ⚠️ 레버리지 — 단기 베팅용, 자산의 3% 이하."

    return PositionGuidance(
        suggested_pct=round(suggested, 4),
        stop_pct=round(stop_pct, 4),
        atr_pct=round(atr_pct, 4),
        entry_price=round(last, 4),
        stop_price=round(stop_price, 4),
        basis=basis,
    )
