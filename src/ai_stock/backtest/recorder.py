"""Stage-1 backtest infra — log every daily verdict, score forward returns later.

Design:
  reports/backtest/labels.jsonl
      append-only, one JSON record per (date, ticker)
      written by the daily workflow right after JSON export

This file accumulates the bias-free truth: at date T we made verdict X,
no future knowledge baked in. Forward-return columns are filled in over
time as new price data arrives (see forward.py).

JSONL was picked over parquet because:
  - one line per row → diff-friendly in git
  - append doesn't need rewrite of the whole file
  - no extra dependency (pyarrow optional)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path
from typing import Any, Iterable

from ai_stock.config import REPO_ROOT

LABELS_PATH = REPO_ROOT / "reports" / "backtest" / "labels.jsonl"


@dataclass
class LabelRecord:
    """One verdict snapshot for a (date, ticker)."""
    date: str
    ticker: str
    asset_class: str        # "stock" | "coin"
    name: str
    theme: str
    tier: str
    label: str
    overheat_level: str     # "normal" | "mild" | "high" | "extreme" | "" if missing
    composite_score: float
    short_score: float
    mid_score: float
    long_score: float
    close: float            # entry price the day the label was issued
    # Forward returns get filled in on later runs:
    return_5d: float | None = None
    return_20d: float | None = None
    return_60d: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


def load_labels(path: Path | None = None) -> list[LabelRecord]:
    p = path or LABELS_PATH
    if not p.exists():
        return []
    out: list[LabelRecord] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.append(LabelRecord(**{k: d.get(k) for k in LabelRecord.__dataclass_fields__}))
    return out


def append_labels(records: Iterable[LabelRecord], path: Path | None = None) -> Path:
    """Append new records. De-dupes within (date, ticker) — newest wins."""
    p = path or LABELS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = load_labels(p)
    by_key: dict[tuple[str, str], LabelRecord] = {(r.date, r.ticker): r for r in existing}
    for r in records:
        by_key[(r.date, r.ticker)] = r
    # Sort by date then ticker for stable diffs
    rows = sorted(by_key.values(), key=lambda r: (r.date, r.ticker))
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    return p


def write_labels(records: list[LabelRecord], path: Path | None = None) -> Path:
    """Same as append_labels but replaces the file (used by forward-return updater)."""
    p = path or LABELS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(records, key=lambda r: (r.date, r.ticker))
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    return p


def _extract_close(verdict: Any) -> float | None:
    """Best-effort latest close pull from a verdict's stored metrics."""
    metrics = getattr(verdict, "metrics", None) or {}
    for key in ("close", "price", "last_close"):
        v = metrics.get(key) if isinstance(metrics, dict) else None
        if isinstance(v, (int, float)):
            return float(v)
    # Fall back to guidance.entry_price if sizing ran
    g = getattr(verdict, "guidance", None)
    ep = getattr(g, "entry_price", None) if g else None
    if isinstance(ep, (int, float)):
        return float(ep)
    return None


def record_from_context(
    context: dict[str, Any],
    asset_class: str,
    path: Path | None = None,
) -> int:
    """Pull verdicts out of a daily context and append them to the log.

    Skips verdicts that have no usable close price (mid-pipeline failures).
    Returns the number of new rows actually written.
    """
    date_str = context.get("date")
    if not date_str:
        return 0
    if isinstance(date_str, _date):
        date_str = date_str.isoformat()

    records: list[LabelRecord] = []
    for v in context.get("verdicts", []):
        stock = getattr(v, "stock", None)
        composite = getattr(v, "composite", None)
        if stock is None or composite is None:
            continue
        close = _extract_close(v)
        if close is None or close <= 0:
            continue
        narrative = getattr(v, "narrative", None)
        label = (
            getattr(narrative, "label", None)
            or getattr(composite, "label", "")
        )
        oh = getattr(v, "overheat", None)
        records.append(LabelRecord(
            date=date_str,
            ticker=stock.ticker,
            asset_class=asset_class,
            name=stock.name,
            theme=stock.theme,
            tier=stock.tier,
            label=label,
            overheat_level=getattr(oh, "level", "") if oh else "",
            composite_score=float(composite.composite_score),
            short_score=float(composite.short_score),
            mid_score=float(composite.mid_score),
            long_score=float(composite.long_score),
            close=close,
        ))
    if not records:
        return 0
    append_labels(records, path=path)
    return len(records)
