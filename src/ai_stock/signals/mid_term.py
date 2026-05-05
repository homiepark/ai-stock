"""Mid-term (3~12 months) signals → 0..100 score."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_stock.signals.indicators import clamp_score, momentum, sma


@dataclass
class MidTermResult:
    score: float
    components: dict[str, float]
    rationale: list[str]


def _score_ma200(last_close: float, ma200_val: float) -> tuple[float, str]:
    if not ma200_val or pd.isna(ma200_val):
        return 50.0, "200일선 N/A"
    diff = (last_close - ma200_val) / ma200_val * 100
    if -2 <= diff <= 8:
        return 75.0, f"200일선 대비 {diff:+.1f}% (안정 상승 추세 진입가)"
    if 8 < diff <= 25:
        return 60.0, f"200일선 대비 {diff:+.1f}% (강한 추세, 추가 진입 신중)"
    if diff > 25:
        return 35.0, f"200일선 대비 {diff:+.1f}% (이격 과대)"
    return 30.0, f"200일선 대비 {diff:+.1f}% (장기 추세 약함)"


def _score_earnings(rev_history: list) -> tuple[float, str]:
    """rev_history: list of (period_str, revenue) descending. Compute YoY trend."""
    if not rev_history or len(rev_history) < 5:
        return 50.0, "분기 매출 데이터 부족"
    revs = [r[1] for r in rev_history if r[1] is not None and r[1] > 0]
    if len(revs) < 5:
        return 50.0, "분기 매출 데이터 부족"
    yoy = (revs[0] - revs[4]) / revs[4]
    if yoy > 0.50:
        return 90.0, f"매출 YoY +{yoy*100:.0f}% (폭발적 성장)"
    if yoy > 0.25:
        return 75.0, f"매출 YoY +{yoy*100:.0f}% (강한 성장)"
    if yoy > 0.10:
        return 60.0, f"매출 YoY +{yoy*100:.0f}% (견조)"
    if yoy > 0:
        return 50.0, f"매출 YoY +{yoy*100:.0f}% (저성장)"
    return 30.0, f"매출 YoY {yoy*100:.0f}% (역성장)"


def _score_consensus(rev30: float | None, rev90: float | None) -> tuple[float, str]:
    if rev30 is None and rev90 is None:
        return 50.0, "컨센서스 리비전 N/A"
    parts = []
    score = 50.0
    if rev30 is not None:
        score += rev30 * 500  # 5% revision = +25
        parts.append(f"30일 {rev30*100:+.1f}%")
    if rev90 is not None:
        score += rev90 * 250
        parts.append(f"90일 {rev90*100:+.1f}%")
    return clamp_score(score), "EPS 컨센 리비전 " + " / ".join(parts)


def _score_relative_strength(prices: pd.DataFrame, benchmark_prices: pd.DataFrame | None) -> tuple[float, str]:
    if benchmark_prices is None or benchmark_prices.empty or len(benchmark_prices) < 60:
        return 50.0, "벤치마크 데이터 없음"
    if prices is None or prices.empty or len(prices) < 60:
        return 50.0, "가격 데이터 부족"
    stock_60 = float(momentum(prices["close"], 60).iloc[-1])
    bench_60 = float(momentum(benchmark_prices["close"], 60).iloc[-1])
    diff = (stock_60 - bench_60) * 100
    score = clamp_score(50 + diff * 2.5)
    return score, f"60일 상대강도 {diff:+.1f}%p"


def mid_term_signal(prices: pd.DataFrame, fundamentals: dict[str, Any],
                    benchmark_prices: pd.DataFrame | None = None,
                    weights: dict[str, float] | None = None) -> MidTermResult:
    weights = weights or {"ma200_position": 0.25, "earnings_trend": 0.30,
                          "consensus_revision": 0.25, "relative_strength": 0.20}

    if prices is None or prices.empty or len(prices) < 60:
        return MidTermResult(50.0, {}, ["가격 데이터 부족 — 중립 처리"])

    close = prices["close"]
    last_close = float(close.iloc[-1])
    ma200_val = float(sma(close, 200).iloc[-1]) if len(close) >= 200 else float(sma(close, len(close) - 1).iloc[-1])

    components: dict[str, float] = {}
    rationale: list[str] = []

    s, r = _score_ma200(last_close, ma200_val); components["ma200_position"] = s; rationale.append(r)
    s, r = _score_earnings(fundamentals.get("revenue_history", [])); components["earnings_trend"] = s; rationale.append(r)
    s, r = _score_consensus(
        fundamentals.get("consensus_eps_revision_30d"),
        fundamentals.get("consensus_eps_revision_90d"),
    ); components["consensus_revision"] = s; rationale.append(r)
    s, r = _score_relative_strength(prices, benchmark_prices); components["relative_strength"] = s; rationale.append(r)

    total = sum(components[k] * weights.get(k, 0) for k in components)
    return MidTermResult(clamp_score(total), components, rationale)
