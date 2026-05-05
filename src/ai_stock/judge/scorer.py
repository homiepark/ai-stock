"""Combine short/mid/long quantitative scores → composite + label."""
from __future__ import annotations

from dataclasses import dataclass

from ai_stock.signals.indicators import clamp_score
from ai_stock.signals.long_term import LongTermResult
from ai_stock.signals.mid_term import MidTermResult
from ai_stock.signals.short_term import ShortTermResult


LABELS = ("STRONG_BUY", "ACCUMULATE", "HOLD", "TRIM", "AVOID")
LABEL_EMOJI = {
    "STRONG_BUY": "🟢",
    "ACCUMULATE": "🟡",
    "HOLD": "⚪",
    "TRIM": "🟠",
    "AVOID": "🔴",
}


@dataclass
class CompositeVerdict:
    composite_score: float
    label: str
    short_score: float
    mid_score: float
    long_score: float


def compose(
    short: ShortTermResult,
    mid: MidTermResult,
    long: LongTermResult,
    weights: dict[str, float] | None = None,
    thresholds: dict[str, float] | None = None,
) -> CompositeVerdict:
    weights = weights or {"short": 0.25, "mid": 0.35, "long": 0.40}
    thresholds = thresholds or {"strong_buy": 75, "accumulate": 60, "hold": 45, "trim": 30}

    composite = (
        short.score * weights.get("short", 0.25)
        + mid.score * weights.get("mid", 0.35)
        + long.score * weights.get("long", 0.40)
    )
    composite = clamp_score(composite)

    if composite >= thresholds["strong_buy"]:
        label = "STRONG_BUY"
    elif composite >= thresholds["accumulate"]:
        label = "ACCUMULATE"
    elif composite >= thresholds["hold"]:
        label = "HOLD"
    elif composite >= thresholds["trim"]:
        label = "TRIM"
    else:
        label = "AVOID"

    return CompositeVerdict(composite, label, short.score, mid.score, long.score)
