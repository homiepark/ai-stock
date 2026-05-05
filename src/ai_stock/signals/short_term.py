"""Short-term (1~12 weeks) signals → 0..100 score."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_stock.signals.indicators import (
    clamp_score, macd, momentum, rsi, sma, volume_zscore,
)


@dataclass
class ShortTermResult:
    score: float
    components: dict[str, float]
    rationale: list[str]


def _score_rsi(rsi_val: float) -> tuple[float, str]:
    """Below 30 = oversold = +. Above 70 = overbought = -. Neutral 50."""
    if rsi_val is None or pd.isna(rsi_val):
        return 50.0, "RSI N/A"
    if rsi_val < 30:
        return 85.0, f"RSI {rsi_val:.1f} 과매도(매수 우호)"
    if rsi_val < 45:
        return 65.0, f"RSI {rsi_val:.1f} 약세 후 반등 영역"
    if rsi_val < 55:
        return 55.0, f"RSI {rsi_val:.1f} 중립"
    if rsi_val < 70:
        return 45.0, f"RSI {rsi_val:.1f} 강세, 약간 과열"
    return 20.0, f"RSI {rsi_val:.1f} 과매수"


def _score_macd(hist: float) -> tuple[float, str]:
    if hist is None or pd.isna(hist):
        return 50.0, "MACD N/A"
    if hist > 0:
        return 70.0, f"MACD 히스토그램 {hist:.2f} 양전(추세 우호)"
    return 35.0, f"MACD 히스토그램 {hist:.2f} 음전"


def _score_ma50(close: float, ma50_val: float) -> tuple[float, str]:
    if not ma50_val or pd.isna(ma50_val):
        return 50.0, "50일 이평 N/A"
    diff = (close - ma50_val) / ma50_val * 100
    if -3 <= diff <= 5:
        return 75.0, f"50일선 대비 {diff:+.1f}% (우호적 진입 구간)"
    if 5 < diff <= 12:
        return 55.0, f"50일선 대비 {diff:+.1f}% (모멘텀 강함)"
    if diff > 12:
        return 30.0, f"50일선 대비 {diff:+.1f}% (단기 과열)"
    return 40.0, f"50일선 대비 {diff:+.1f}% (약세 흐름)"


def _score_volume(z: float) -> tuple[float, str]:
    if z is None or pd.isna(z):
        return 50.0, "거래량 N/A"
    if z > 2.0:
        return 75.0, f"거래량 Z={z:.2f} 폭증(관심도 급등)"
    if z > 1.0:
        return 65.0, f"거래량 Z={z:.2f} 증가"
    if z < -1.0:
        return 40.0, f"거래량 Z={z:.2f} 감소(관심 이탈)"
    return 55.0, f"거래량 Z={z:.2f} 평이"


def _score_momentum(m5: float, m20: float) -> tuple[float, str]:
    if pd.isna(m5) or pd.isna(m20):
        return 50.0, "모멘텀 N/A"
    # Both positive = strong; m5 > 0 and m20 < 0 = freshly turning up
    s = 50.0 + (m5 * 200) + (m20 * 100)  # rough scaling
    return clamp_score(s), f"5일 {m5*100:+.1f}% / 20일 {m20*100:+.1f}%"


def short_term_signal(prices: pd.DataFrame, weights: dict[str, float] | None = None,
                      rsi_period: int = 14, macd_fast: int = 12, macd_slow: int = 26,
                      macd_signal: int = 9) -> ShortTermResult:
    weights = weights or {"rsi": 0.20, "macd": 0.20, "ma50_distance": 0.20,
                          "volume_spike": 0.15, "momentum_5_20": 0.25}

    if prices is None or prices.empty or len(prices) < 60:
        return ShortTermResult(50.0, {}, ["가격 데이터 부족 — 중립 처리"])

    close = prices["close"]
    volume = prices["volume"]
    last_close = float(close.iloc[-1])

    rsi_val = float(rsi(close, rsi_period).iloc[-1])
    macd_hist = float(macd(close, macd_fast, macd_slow, macd_signal)["hist"].iloc[-1])
    ma50_val = float(sma(close, 50).iloc[-1])
    vol_z = float(volume_zscore(volume, 20).iloc[-1])
    m5 = float(momentum(close, 5).iloc[-1])
    m20 = float(momentum(close, 20).iloc[-1])

    components = {}
    rationale = []

    s, r = _score_rsi(rsi_val); components["rsi"] = s; rationale.append(r)
    s, r = _score_macd(macd_hist); components["macd"] = s; rationale.append(r)
    s, r = _score_ma50(last_close, ma50_val); components["ma50_distance"] = s; rationale.append(r)
    s, r = _score_volume(vol_z); components["volume_spike"] = s; rationale.append(r)
    s, r = _score_momentum(m5, m20); components["momentum_5_20"] = s; rationale.append(r)

    total = sum(components[k] * weights.get(k, 0) for k in components)
    return ShortTermResult(clamp_score(total), components, rationale)


def latest_metrics(prices: pd.DataFrame) -> dict[str, Any]:
    """Return latest indicator values for use elsewhere (verdict prompt, charts)."""
    if prices is None or prices.empty or len(prices) < 60:
        return {}
    close = prices["close"]
    return {
        "last_close": float(close.iloc[-1]),
        "rsi14": float(rsi(close).iloc[-1]),
        "ma50": float(sma(close, 50).iloc[-1]),
        "ma200": float(sma(close, 200).iloc[-1]) if len(close) >= 200 else None,
        "vol_z20": float(volume_zscore(prices["volume"]).iloc[-1]),
        "ret_5d": float(momentum(close, 5).iloc[-1]),
        "ret_20d": float(momentum(close, 20).iloc[-1]),
        "ret_60d": float(momentum(close, 60).iloc[-1]) if len(close) >= 60 else None,
    }
