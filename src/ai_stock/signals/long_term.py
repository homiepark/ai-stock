"""Long-term (1~5y, ten-bagger eligibility) signals → 0..100 score."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_stock.signals.indicators import clamp_score


@dataclass
class LongTermResult:
    score: float
    components: dict[str, float]
    rationale: list[str]


def _score_revenue_cagr(rev_history: list) -> tuple[float, str]:
    """Approximate from quarterly revenue: compare TTM vs ~3y prior TTM."""
    revs = [r[1] for r in (rev_history or []) if r[1] is not None and r[1] > 0]
    if len(revs) < 12:
        # Not enough quarters — score with what we have via YoY of latest
        if len(revs) >= 5:
            yoy = (revs[0] - revs[4]) / revs[4]
            score = clamp_score(50 + yoy * 100)
            return score, f"YoY {yoy*100:+.0f}% (장기 데이터 부족, YoY로 대체)"
        return 50.0, "장기 매출 데이터 부족"
    ttm_now = sum(revs[0:4])
    ttm_3y = sum(revs[8:12])
    if ttm_3y <= 0:
        return 50.0, "장기 매출 비교 불가"
    cagr = (ttm_now / ttm_3y) ** (1 / 3) - 1
    if cagr > 0.40:
        return 95.0, f"3년 매출 CAGR +{cagr*100:.0f}% (텐베거 등급)"
    if cagr > 0.25:
        return 80.0, f"3년 매출 CAGR +{cagr*100:.0f}% (강한 성장)"
    if cagr > 0.15:
        return 65.0, f"3년 매출 CAGR +{cagr*100:.0f}% (양호)"
    if cagr > 0.05:
        return 45.0, f"3년 매출 CAGR +{cagr*100:.0f}% (보통)"
    return 25.0, f"3년 매출 CAGR {cagr*100:+.0f}% (성장성 부족)"


def _score_margin_trend(margin_history: list) -> tuple[float, str]:
    """margin_history: list of (period, gross, op, fcf). Compare latest vs 4 quarters back."""
    margins = [m for m in (margin_history or []) if m[2] is not None]
    if len(margins) < 5:
        return 50.0, "마진 추이 데이터 부족"
    op_now = margins[0][2]
    op_prev = margins[4][2]
    delta = (op_now - op_prev) * 100  # in pp
    if delta > 5:
        return 85.0, f"영업마진 YoY +{delta:.1f}%p (영업레버리지 발현)"
    if delta > 2:
        return 70.0, f"영업마진 YoY +{delta:.1f}%p (개선)"
    if delta > -1:
        return 55.0, f"영업마진 YoY {delta:+.1f}%p (안정)"
    if delta > -5:
        return 35.0, f"영업마진 YoY {delta:+.1f}%p (악화)"
    return 20.0, f"영업마진 YoY {delta:+.1f}%p (심한 악화)"


def _score_ev_sales(ev_to_sales: float | None) -> tuple[float, str]:
    """Without 5y history, use heuristic bands. EV/Sales < 5 cheap-ish, > 25 expensive."""
    if ev_to_sales is None:
        return 50.0, "EV/Sales N/A"
    if ev_to_sales < 3:
        return 70.0, f"EV/Sales {ev_to_sales:.1f} (저평가 영역)"
    if ev_to_sales < 8:
        return 60.0, f"EV/Sales {ev_to_sales:.1f} (적정)"
    if ev_to_sales < 15:
        return 45.0, f"EV/Sales {ev_to_sales:.1f} (성장주 정상)"
    if ev_to_sales < 25:
        return 30.0, f"EV/Sales {ev_to_sales:.1f} (높음)"
    return 15.0, f"EV/Sales {ev_to_sales:.1f} (매우 비쌈)"


def _score_peg(peg: float | None) -> tuple[float, str]:
    if peg is None or peg <= 0:
        return 50.0, "PEG N/A"
    if peg < 1.0:
        return 80.0, f"PEG {peg:.2f} (성장 대비 저평가)"
    if peg < 1.5:
        return 65.0, f"PEG {peg:.2f} (적정)"
    if peg < 2.5:
        return 45.0, f"PEG {peg:.2f} (다소 비쌈)"
    return 25.0, f"PEG {peg:.2f} (고평가)"


def _score_capital_allocation(_fundamentals: dict) -> tuple[float, str]:
    # Placeholder: free data sources don't reliably expose buyback yield. Default neutral.
    return 50.0, "자본배분: 무료 데이터로는 정량 평가 제한 (LLM 서술에서 보완)"


def long_term_signal(fundamentals: dict[str, Any], weights: dict[str, float] | None = None) -> LongTermResult:
    weights = weights or {"revenue_cagr": 0.30, "margin_trend": 0.20,
                          "ev_sales_percentile": 0.20, "peg": 0.15,
                          "capital_allocation": 0.15}

    components: dict[str, float] = {}
    rationale: list[str] = []

    s, r = _score_revenue_cagr(fundamentals.get("revenue_history", [])); components["revenue_cagr"] = s; rationale.append(r)
    s, r = _score_margin_trend(fundamentals.get("margin_history", [])); components["margin_trend"] = s; rationale.append(r)
    s, r = _score_ev_sales(fundamentals.get("ev_to_sales")); components["ev_sales_percentile"] = s; rationale.append(r)
    s, r = _score_peg(fundamentals.get("peg")); components["peg"] = s; rationale.append(r)
    s, r = _score_capital_allocation(fundamentals); components["capital_allocation"] = s; rationale.append(r)

    total = sum(components[k] * weights.get(k, 0) for k in components)
    return LongTermResult(clamp_score(total), components, rationale)
