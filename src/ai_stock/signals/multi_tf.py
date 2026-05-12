"""Multi-timeframe trend alignment — weekly, daily, 4-hour summary.

Reads the same daily OHLCV (resampled to weekly) plus an optional 4-hour
series from Binance futures klines. Each TF returns:

  trend:   "up" | "down" | "neutral"     (price vs 50/200 MA + 50 vs 200)
  rsi:     RSI(14) current value
  note:    one-line Korean summary

A composite bias is then computed:

  +1 per up trend, −1 per down trend, 0 for neutral
  total ≥ 2  → "HTF aligned bullish, 진입 OK"
  total ≤ −2 → "HTF aligned bearish, 매수 비추천"
  else        → "mixed, conviction 낮음"

This is consumed by the trade plan UI to give a top-down regime read
that the single-TF chart can't.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from ai_stock.signals.indicators import rsi, sma

Trend = Literal["up", "down", "neutral"]


@dataclass
class TFSummary:
    timeframe: str        # "weekly" | "daily" | "4h"
    trend: Trend
    rsi: float | None
    last_close: float | None
    ma_50: float | None
    ma_200: float | None
    note: str

    def to_dict(self) -> dict:
        return self.__dict__


@dataclass
class MultiTFContext:
    timeframes: list[dict] = field(default_factory=list)
    bias_score: int = 0           # sum of up/down across TFs
    bias: str = "mixed"           # "bullish" | "bearish" | "mixed"
    note: str = ""                # composite explanation

    def to_dict(self) -> dict:
        return {
            "timeframes": self.timeframes,
            "bias_score": self.bias_score,
            "bias": self.bias,
            "note": self.note,
        }


def _classify_trend(close: pd.Series) -> tuple[Trend, float | None, float | None, str]:
    if len(close) < 50:
        return "neutral", None, None, "데이터 부족"
    ma50 = float(sma(close, 50).iloc[-1])
    ma200 = float(sma(close, 200).iloc[-1]) if len(close) >= 200 else None
    last = float(close.iloc[-1])

    above_50 = last > ma50
    above_200 = (ma200 is None) or (last > ma200)
    golden_cross = (ma200 is not None) and (ma50 > ma200)

    score = 0
    score += 1 if above_50 else -1
    if ma200 is not None:
        score += 1 if above_200 else -1
        score += 1 if golden_cross else -1

    if score >= 2:
        trend: Trend = "up"
        note = "가격이 50/200MA 위 + 골든 크로스"
    elif score <= -2:
        trend = "down"
        note = "가격이 50/200MA 아래 + 데드 크로스"
    else:
        trend = "neutral"
        note = "혼조"
    return trend, ma50, ma200, note


def _summarize(prices: pd.DataFrame, tf_label: str) -> TFSummary | None:
    """Build a TF summary from a price frame whose index represents that TF's bars."""
    if prices is None or prices.empty or "close" not in prices.columns:
        return None
    close = prices["close"]
    if len(close) < 30:
        return None

    trend, ma50, ma200, note = _classify_trend(close)
    rsi_v = float(rsi(close).iloc[-1]) if len(close) >= 15 else None
    if rsi_v is not None:
        if rsi_v >= 70:
            note += " · RSI 과매수"
        elif rsi_v <= 30:
            note += " · RSI 과매도"

    return TFSummary(
        timeframe=tf_label,
        trend=trend,
        rsi=rsi_v,
        last_close=float(close.iloc[-1]),
        ma_50=ma50,
        ma_200=ma200,
        note=note,
    )


def build_multi_tf(
    daily_prices: pd.DataFrame,
    h4_prices: pd.DataFrame | None = None,
) -> MultiTFContext | None:
    """Combine weekly (resampled from daily), daily, and optional 4-hour series.

    Returns None when even the daily TF is unusable.
    """
    if daily_prices is None or daily_prices.empty:
        return None

    summaries: list[TFSummary] = []

    # Weekly: resample daily closes to Friday-ending bars
    try:
        weekly = daily_prices["close"].resample("W-FRI").last().dropna().to_frame("close")
        s_w = _summarize(weekly, "weekly")
        if s_w is not None:
            summaries.append(s_w)
    except Exception:
        pass

    s_d = _summarize(daily_prices, "daily")
    if s_d is not None:
        summaries.append(s_d)

    if h4_prices is not None and not h4_prices.empty:
        s_h4 = _summarize(h4_prices, "4h")
        if s_h4 is not None:
            summaries.append(s_h4)

    if not summaries:
        return None

    score = sum(
        1 if s.trend == "up" else -1 if s.trend == "down" else 0
        for s in summaries
    )
    if score >= 2:
        bias = "bullish"
        note = "HTF aligned bullish — 롱 진입 우호적."
    elif score <= -2:
        bias = "bearish"
        note = "HTF aligned bearish — 롱 진입 비추천, 카운터 트렌드 시 손절 강하게."
    else:
        bias = "mixed"
        note = "TF가 align 안 됨 — conviction 낮음, 보수적 사이징."

    return MultiTFContext(
        timeframes=[s.to_dict() for s in summaries],
        bias_score=score,
        bias=bias,
        note=note,
    )
