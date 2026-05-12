"""Confluence clustering + LONG trade plan generation.

Pipeline:

  collect_all_levels()  ──►  cluster_levels()  ──►  generate_plan()

Cluster output ("ConfluenceZone"):
  - center price + low/high band
  - aggregate weight (sum of signal weights, decayed for stale pivots)
  - per-signal labels for tooltip transparency
  - confluence count (independent signals merged into this zone)

Plan output ("TradePlan"):
  - entry zone (nearest strong zone below current price)
  - stop loss (zone low - 1 × ATR, false-breakout buffer)
  - 3 take-profit targets (next strong zones above, with R:R)
  - confidence score, invalidation note, applicability flag
  - We don't generate SHORT plans yet — the watchlist is structurally
    long-biased and short plans need separate risk handling.

Conservative defaults so plans don't fire on weak setups:
  - Minimum confluence count for entry/target zones: 2
  - Plan is "actionable" only when T1's R:R ≥ 1.5 and entry zone weight ≥ 1.2
  - Sub-2% gaps between entry and SL are clamped to 2% (avoid tight noise stops)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from ai_stock.signals.chart_analysis import (
    ChartLevel,
    _atr_value,
    collect_all_levels,
)


@dataclass
class ConfluenceZone:
    center: float
    low: float
    high: float
    weight: float            # aggregate
    count: int               # distinct signal types in this cluster
    signals: list[dict] = field(default_factory=list)  # per-signal labels

    def to_dict(self) -> dict:
        return {
            "center": self.center,
            "low": self.low,
            "high": self.high,
            "weight": round(self.weight, 3),
            "count": self.count,
            "signals": self.signals,
        }


@dataclass
class TradePlan:
    side: Literal["LONG"]
    entry_low: float
    entry_high: float
    entry: float                       # mid of entry zone
    stop_loss: float
    stop_pct: float                    # (entry - SL) / entry
    targets: list[dict]                # [{price, rr, label}], up to 3
    confidence: int                    # 0..100 from confluence + alignment
    rationale: str
    invalidation: str
    actionable: bool                   # False = "현재 setup 약함, 관망"
    atr_pct: float
    zones: list[dict] = field(default_factory=list)  # all confluence zones for UI

    def to_dict(self) -> dict:
        return self.__dict__


# --- Confluence clustering ---------------------------------------------------


def _decayed_weight(lv: ChartLevel) -> float:
    """Older swing pivots lose weight (half-life ~120 days)."""
    if lv.age_days <= 0:
        return lv.weight
    half_life = 120
    return lv.weight * (0.5 ** (lv.age_days / half_life))


def cluster_levels(
    levels: list[ChartLevel],
    eps_pct: float = 0.012,
) -> list[ConfluenceZone]:
    """Group levels within `eps_pct` of each other into confluence zones.

    Greedy clustering by price proximity. Two passes:
      1. Sort by price, sweep merging neighbors within eps_pct.
      2. Drop singleton zones with weight < 0.5 (noise floor).
    """
    if not levels:
        return []
    sorted_lv = sorted(levels, key=lambda x: x.price)

    clusters: list[list[ChartLevel]] = []
    for lv in sorted_lv:
        if not clusters:
            clusters.append([lv])
            continue
        ref_price = sum(x.price for x in clusters[-1]) / len(clusters[-1])
        if ref_price > 0 and abs(lv.price - ref_price) / ref_price <= eps_pct:
            clusters[-1].append(lv)
        else:
            clusters.append([lv])

    zones: list[ConfluenceZone] = []
    for c in clusters:
        # Aggregate weight: distinct kinds count once each (avoid double-weighting
        # multiple swing-highs at the same price), use the strongest of each kind.
        by_kind: dict[str, ChartLevel] = {}
        for lv in c:
            existing = by_kind.get(lv.kind)
            if existing is None or _decayed_weight(lv) > _decayed_weight(existing):
                by_kind[lv.kind] = lv

        weight = sum(_decayed_weight(lv) for lv in by_kind.values())
        if len(by_kind) < 2 and weight < 0.8:
            continue  # singleton, low-weight → noise

        prices = [lv.price for lv in by_kind.values()]
        zone = ConfluenceZone(
            center=float(sum(prices) / len(prices)),
            low=float(min(prices)),
            high=float(max(prices)),
            weight=float(weight),
            count=len(by_kind),
            signals=[{
                "kind": lv.kind,
                "label": lv.label,
                "price": round(lv.price, 6),
                "weight": round(_decayed_weight(lv), 3),
                "age_days": lv.age_days,
            } for lv in sorted(by_kind.values(), key=lambda x: -_decayed_weight(x))],
        )
        zones.append(zone)

    # Strongest zones first
    zones.sort(key=lambda z: z.weight, reverse=True)
    return zones


# --- Plan generation ---------------------------------------------------------


_MIN_PLAN_RR = 1.5      # minimum R:R for plan to be "actionable"
_MIN_ENTRY_WEIGHT = 1.2  # minimum aggregate weight for entry zone


def generate_plan(
    prices: pd.DataFrame,
    name: str = "",
) -> TradePlan | None:
    """Build a LONG trade plan from the price history.

    Returns None when there isn't enough data to form even a non-actionable
    suggestion. Otherwise always returns a plan — `actionable` flag tells the
    UI whether the setup is strong enough to act on.
    """
    if prices is None or prices.empty or "close" not in prices.columns or len(prices) < 60:
        return None

    current_price = float(prices["close"].iloc[-1])
    if current_price <= 0:
        return None

    atr = _atr_value(prices, 14) or (current_price * 0.02)
    atr_pct = atr / current_price

    levels = collect_all_levels(prices)
    zones = cluster_levels(levels)

    # Below = potential entry / support, Above = potential resistance / target.
    below = sorted(
        [z for z in zones if z.center < current_price * 0.995],
        key=lambda z: -z.center,  # closest below first
    )
    above = sorted(
        [z for z in zones if z.center > current_price * 1.005],
        key=lambda z: z.center,   # closest above first
    )

    # Pick the strongest among the 3 closest below as the entry zone.
    entry_zone = None
    if below:
        entry_zone = max(below[:3], key=lambda z: z.weight)

    # Targets: take up to 3 strongest above, but keep them in ascending order.
    targets_raw = sorted(above[:6], key=lambda z: -z.weight)[:3]
    targets_raw.sort(key=lambda z: z.center)

    if entry_zone is None:
        # No support below — plan is just "above us is X / Y / Z" advisory.
        plan = _build_plan(
            current_price=current_price,
            atr=atr, atr_pct=atr_pct,
            entry_zone=None, target_zones=targets_raw,
            zones=zones, name=name,
            rationale="현재가 아래에 신뢰성 있는 지지 zone 없음 — setup 미완성.",
        )
        return plan

    entry = entry_zone.center
    # 1.5 × ATR below the entry-zone low — buffer against false breakouts.
    stop_loss = entry_zone.low - 1.5 * atr
    stop_pct = (entry - stop_loss) / entry
    # Floor stop at 2% so we don't get insanely tight stops on calm assets.
    if stop_pct < 0.02:
        stop_loss = entry * (1 - 0.02)
        stop_pct = 0.02

    targets = []
    for i, z in enumerate(targets_raw, start=1):
        rr = (z.center - entry) / max(entry - stop_loss, 1e-9)
        if rr <= 0:
            continue
        targets.append({
            "price": round(z.center, 6),
            "rr": round(rr, 2),
            "label": f"T{i}",
            "weight": round(z.weight, 3),
            "count": z.count,
        })

    # Confidence: blend entry zone strength + target count + alignment.
    base = min(1.0, entry_zone.weight / 3.0)
    target_bonus = 0.15 * len(targets)
    align_bonus = 0.0
    if "close" in prices.columns and len(prices) >= 200:
        ma200 = float(prices["close"].rolling(200).mean().iloc[-1])
        if current_price > ma200:                    # bull regime
            align_bonus += 0.1
    confidence = int(round((base + target_bonus + align_bonus) * 100))
    confidence = max(0, min(100, confidence))

    rr1 = targets[0]["rr"] if targets else 0
    actionable = (
        entry_zone.weight >= _MIN_ENTRY_WEIGHT
        and rr1 >= _MIN_PLAN_RR
        and entry_zone.count >= 2
    )

    rationale = _build_rationale(entry_zone, targets, current_price, entry)
    invalidation = (
        f"진입가 ${entry:,.4g} 아래 손절가 ${stop_loss:,.4g} "
        "일봉 종가 마감 시 plan 폐기."
    )

    return _build_plan(
        current_price=current_price,
        atr=atr, atr_pct=atr_pct,
        entry_zone=entry_zone, target_zones=targets_raw,
        zones=zones, name=name,
        entry=entry, stop_loss=stop_loss, stop_pct=stop_pct,
        targets=targets, confidence=confidence,
        rationale=rationale, invalidation=invalidation,
        actionable=actionable,
    )


def _build_plan(
    current_price: float,
    atr: float,
    atr_pct: float,
    entry_zone: ConfluenceZone | None,
    target_zones: list[ConfluenceZone],
    zones: list[ConfluenceZone],
    name: str = "",
    entry: float = 0.0,
    stop_loss: float = 0.0,
    stop_pct: float = 0.0,
    targets: list[dict] | None = None,
    confidence: int = 0,
    rationale: str = "",
    invalidation: str = "",
    actionable: bool = False,
) -> TradePlan:
    return TradePlan(
        side="LONG",
        entry_low=entry_zone.low if entry_zone else 0.0,
        entry_high=entry_zone.high if entry_zone else 0.0,
        entry=entry,
        stop_loss=stop_loss,
        stop_pct=stop_pct,
        targets=targets or [],
        confidence=confidence,
        rationale=rationale or "신뢰성 있는 confluence 부족 — 관망.",
        invalidation=invalidation or "setup 미완성, 관망",
        actionable=actionable,
        atr_pct=atr_pct,
        zones=[z.to_dict() for z in zones],
    )


def _build_rationale(
    entry_zone: ConfluenceZone,
    targets: list[dict],
    current_price: float,
    entry: float,
) -> str:
    n_sig = entry_zone.count
    sig_names = ", ".join(s["label"] for s in entry_zone.signals[:3])
    distance = (current_price - entry) / current_price * 100
    tgt_part = ""
    if targets:
        rr1 = targets[0]["rr"]
        tgt_part = f" T1 ${targets[0]['price']:,.4g} (R:R {rr1:.1f})"
        if len(targets) >= 2:
            tgt_part += f", T2 ${targets[1]['price']:,.4g} (R:R {targets[1]['rr']:.1f})"
    return (
        f"진입 zone에 {n_sig}개 시그널 합류 — {sig_names}. "
        f"현재가 대비 {distance:+.1f}% 위치.{tgt_part}"
    )
