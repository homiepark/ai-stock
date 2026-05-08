"""JSON export for the Next.js frontend.

Same pipeline data as Markdown/HTML, but written as structured JSON files
that the Next.js app reads at build time. Files written:

  web/data/
    index.json                       # Manifest of all reports (dates × types)
    latest-stock.json                # Today's stock context (alias)
    latest-coin.json                 # Today's coin context (alias)
    stock/YYYY-MM-DD.json            # Per-day stock snapshot
    coin/YYYY-MM-DD.json             # Per-day coin snapshot

The schema is stable — Next.js types in `web/lib/types.ts` mirror it.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_stock.config import REPO_ROOT

log = logging.getLogger(__name__)

WEB_DATA_DIR = REPO_ROOT / "web" / "data"


def _serialize(obj: Any) -> Any:
    """Recursively convert dataclasses, datetimes, etc. into JSON-safe values."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if is_dataclass(obj) and not isinstance(obj, type):
        return _serialize(asdict(obj))
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, (list, tuple, set)):
        return [_serialize(v) for v in obj]
    # numpy / pandas scalars
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    if hasattr(obj, "to_dict"):
        try:
            return _serialize(obj.to_dict())
        except Exception:
            pass
    return str(obj)


def _shape_context(context: dict[str, Any], asset_class: str) -> dict[str, Any]:
    """Convert a daily context dict into the wire shape consumed by Next.js.

    Strips internal keys (_today), normalizes nested dataclasses, and exposes
    each verdict's key fields at the top level for table consumption.
    """
    verdicts_out = []
    for v in context.get("verdicts", []):
        c = v.composite
        verdicts_out.append({
            "ticker": v.stock.ticker,
            "name": v.stock.name,
            "country": v.stock.country,
            "tier": v.stock.tier,
            "theme": v.stock.theme,
            "theme_short": v.theme_short,
            "note": v.stock.note,
            "coingecko_id": getattr(v.stock, "coingecko_id", "") or "",
            "scores": {
                "short": c.short_score,
                "mid": c.mid_score,
                "long": c.long_score,
                "composite": c.composite_score,
            },
            "label": v.narrative.label or c.label,
            "label_quant": c.label,
            "narrative": {
                "summary": v.narrative.summary,
                "entry_guide": v.narrative.entry_guide,
                "risks": v.narrative.risks,
                "next_trigger": v.narrative.next_trigger,
            },
            "metrics": v.metrics,
            "in_focus": False,
        })

    # Mark focus stocks for highlighting in UI
    focus_tickers = {f.stock.ticker for f in context.get("focus", [])}
    for v in verdicts_out:
        if v["ticker"] in focus_tickers:
            v["in_focus"] = True

    theme_rankings_out = []
    for r in context.get("theme_rankings", []):
        theme_rankings_out.append({
            "theme_key": r.theme_key,
            "theme_name": r.theme_name,
            "composite_return": r.composite_return,
            "avg_return_1w": r.avg_return_1w,
            "avg_return_1m": r.avg_return_1m,
            "avg_return_3m": r.avg_return_3m,
            "cap_leader": (
                {"ticker": r.cap_leader.ticker, "name": r.cap_leader.name}
                if r.cap_leader else None
            ),
            "momentum_leader": (
                {"ticker": r.momentum_leader.ticker, "name": r.momentum_leader.name}
                if r.momentum_leader else None
            ),
            "member_count": len(r.members),
        })

    label_changes_out = [
        {"ticker": c.stock.ticker, "name": c.stock.name,
         "old_label": c.old_label, "new_label": c.new_label}
        for c in context.get("label_changes", [])
    ]

    return _serialize({
        "asset_class": asset_class,
        "date": context["date"],
        "generated_at": context["generated_at"],
        "version": context["version"],
        "universe_size": context["universe_size"],
        "us_count": context.get("us_count", 0),
        "kr_count": context.get("kr_count", 0),
        "macro": context.get("macro", {}),
        "theme_rankings": theme_rankings_out,
        "verdicts": verdicts_out,
        "focus_tickers": list(focus_tickers),
        "top_news": context.get("top_news", []),
        "label_changes": label_changes_out,
        "social": context.get("social"),  # only set for coin context
    })


def _update_manifest(data_dir: Path, date: str, asset_class: str) -> None:
    """Update web/data/index.json with the latest dates per asset class."""
    manifest_path = data_dir / "index.json"
    manifest: dict[str, Any] = {"stock": [], "coin": []}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            pass

    # Re-scan filesystem so the manifest reflects ground truth (handles
    # historical files added out-of-band, deletions, etc.)
    for kind in ("stock", "coin"):
        kind_dir = data_dir / kind
        kind_dir.mkdir(parents=True, exist_ok=True)
        dates = []
        for p in kind_dir.glob("*.json"):
            stem = p.stem
            if len(stem) == 10 and stem.count("-") == 2 and stem.replace("-", "").isdigit():
                dates.append(stem)
        manifest[kind] = sorted(set(dates), reverse=True)

    # Make sure today's date is in the manifest even if filesystem scan
    # missed it due to ordering (the file was just written).
    if date not in manifest[asset_class]:
        manifest[asset_class].insert(0, date)
        manifest[asset_class].sort(reverse=True)

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def export_stock_json(context: dict[str, Any], data_dir: Path | None = None) -> Path:
    """Write today's stock context to web/data/stock/YYYY-MM-DD.json + latest-stock.json."""
    data_dir = data_dir or WEB_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "stock").mkdir(parents=True, exist_ok=True)

    payload = _shape_context(context, asset_class="stock")
    date = payload["date"]

    dated_path = data_dir / "stock" / f"{date}.json"
    dated_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    latest_path = data_dir / "latest-stock.json"
    latest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    _update_manifest(data_dir, date, "stock")
    log.info("Wrote stock JSON → %s + latest-stock.json", dated_path)
    return dated_path


def export_coin_json(context: dict[str, Any], data_dir: Path | None = None) -> Path:
    """Write today's coin context to web/data/coin/YYYY-MM-DD.json + latest-coin.json."""
    data_dir = data_dir or WEB_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "coin").mkdir(parents=True, exist_ok=True)

    payload = _shape_context(context, asset_class="coin")
    date = payload["date"]

    dated_path = data_dir / "coin" / f"{date}.json"
    dated_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    latest_path = data_dir / "latest-coin.json"
    latest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    _update_manifest(data_dir, date, "coin")
    log.info("Wrote coin JSON → %s + latest-coin.json", dated_path)
    return dated_path
