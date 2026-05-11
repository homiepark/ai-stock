"""Overheat detection — separate from the composite score.

Even a STRONG_BUY stock can be "too late to chase right now". Overheat
flags help users distinguish:

  - 🟢 정상     — 진입 OK
  - 🟡 약과열   — 분할매수만 (1/3 ~ 1/2씩)
  - 🟠 과열     — 조정 대기, 본격 진입 자제
  - 🔴 극과열   — 회피 / 차익실현

Score 0~100 (높을수록 과열). Signals combined:
  - RSI > 70: overbought
  - Price > 50d MA by significant margin (>10% 약과열, >25% 극과열)
  - Price > 200d MA by extreme margin (>40% 극과열)
  - Volume spike (Z-score > 2): blow-off top warning
  - 5d return > 15%: parabolic move
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_stock.signals.indicators import momentum, rsi, sma, volume_zscore


@dataclass
class OverheatResult:
    score: float            # 0~100, higher = more overheated
    level: str              # "normal" | "mild" | "high" | "extreme"
    emoji: str              # 🟢 🟡 🟠 🔴
    label: str              # "정상" | "약과열" | "과열" | "극과열"
    guidance: str           # plain-Korean buying guidance
    flags: list[str]        # which signals triggered, for transparency


def _level_for_score(score: float) -> tuple[str, str, str, str]:
    if score >= 75:
        return ("extreme", "🔴", "극과열", "회피하거나 차익실현. 지금 진입은 단기 손실 위험 매우 큼.")
    if score >= 55:
        return ("high", "🟠", "과열", "조정(10~15% 하락) 기다리는 게 안전. 지금은 관망.")
    if score >= 30:
        return ("mild", "🟡", "약과열", "분할매수만. 한 번에 들어가지 말고 1/3~1/2씩 나눠서.")
    return ("normal", "🟢", "정상", "진입 OK. 종합 점수가 좋다면 매수 검토.")


def overheat_signal(prices: pd.DataFrame) -> OverheatResult:
    """Compute overheat 0~100 from price action only.

    Independent of fundamentals — purely about 'has the stock run too far
    too fast?'. Returns a result that the UI can render distinctly from the
    composite STRONG_BUY/AVOID label.
    """
    if prices is None or prices.empty or len(prices) < 50:
        return OverheatResult(
            score=0.0, level="normal", emoji="🟢", label="정상",
            guidance="데이터 부족 — 판단 보류.", flags=[],
        )

    close = prices["close"]
    last = float(close.iloc[-1])
    rsi14 = float(rsi(close, 14).iloc[-1])
    ma50_val = float(sma(close, 50).iloc[-1])
    ma200_val = (
        float(sma(close, 200).iloc[-1])
        if len(close) >= 200 else float(sma(close, len(close) - 1).iloc[-1])
    )
    vol_z = float(volume_zscore(prices["volume"], 20).iloc[-1])
    ret_5d = float(momentum(close, 5).iloc[-1])
    ret_20d = float(momentum(close, 20).iloc[-1])

    pct_ma50 = (last - ma50_val) / ma50_val if ma50_val else 0.0
    pct_ma200 = (last - ma200_val) / ma200_val if ma200_val else 0.0

    score = 0.0
    flags: list[str] = []

    # RSI overbought
    if rsi14 >= 80:
        score += 30
        flags.append(f"RSI {rsi14:.0f} 극과열")
    elif rsi14 >= 70:
        score += 20
        flags.append(f"RSI {rsi14:.0f} 과매수")
    elif rsi14 >= 65:
        score += 10

    # Distance from 50-day MA
    if pct_ma50 > 0.25:
        score += 30
        flags.append(f"50일선 +{pct_ma50*100:.0f}% 극이격")
    elif pct_ma50 > 0.15:
        score += 18
        flags.append(f"50일선 +{pct_ma50*100:.0f}% 과이격")
    elif pct_ma50 > 0.08:
        score += 8

    # Distance from 200-day MA — long-term overextension
    if pct_ma200 > 0.50:
        score += 20
        flags.append(f"200일선 +{pct_ma200*100:.0f}% 장기 과열")
    elif pct_ma200 > 0.30:
        score += 10

    # Volume spike — blow-off top
    if vol_z >= 3:
        score += 15
        flags.append(f"거래량 Z={vol_z:.1f} 폭증")
    elif vol_z >= 2:
        score += 8

    # Parabolic short-term move
    if ret_5d > 0.20:
        score += 15
        flags.append(f"5일 {ret_5d*100:+.0f}% 급등")
    elif ret_5d > 0.10:
        score += 7

    if ret_20d > 0.50:
        score += 10
        flags.append(f"20일 {ret_20d*100:+.0f}% 폭등")

    score = min(score, 100.0)
    level, emoji, label, guidance = _level_for_score(score)

    return OverheatResult(score=score, level=level, emoji=emoji,
                          label=label, guidance=guidance, flags=flags)
