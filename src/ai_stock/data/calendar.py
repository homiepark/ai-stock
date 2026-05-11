"""Upcoming-events calendar — macro (yaml) + earnings (yfinance).

Two sources merged into one chronological list so the dashboard can show
"next 7~14 days" of market-moving dates next to the daily verdict.

Macro events live in config/macro_calendar.yaml (manually curated each year
from BLS/BEA/Fed schedules). Earnings come from yfinance per-ticker calendar.

This module is offline-safe: yfinance failures and missing yaml all fall
through to empty lists.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import yaml

from ai_stock.config import CONFIG_DIR, Stock
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)


@dataclass
class UpcomingEvent:
    date: str           # YYYY-MM-DD
    name: str
    kind: str           # "macro" | "earnings"
    impact: str = "med"  # "high" | "med"
    ticker: str = ""    # set only for earnings
    note: str = ""

    def to_dict(self) -> dict:
        return self.__dict__


def _parse_iso(d: str) -> date | None:
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def load_macro_events(path: Path | None = None) -> list[UpcomingEvent]:
    p = path or (CONFIG_DIR / "macro_calendar.yaml")
    if not p.exists():
        return []
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception as e:
        log.warning("macro_calendar.yaml parse failed: %s", e)
        return []
    out: list[UpcomingEvent] = []
    for e in raw.get("events", []):
        if _parse_iso(e.get("date", "")) is None:
            continue
        out.append(UpcomingEvent(
            date=e["date"],
            name=e.get("name", ""),
            kind="macro",
            impact=e.get("impact", "med"),
            note=e.get("note", ""),
        ))
    return out


def _earnings_date_from_yf(ticker: str) -> date | None:
    """Return next earnings date for a yfinance ticker, or None on any failure."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        t = yf.Ticker(ticker)
        # `.calendar` returns a dict like {'Earnings Date': [datetime(...), datetime(...)]}
        cal = t.calendar
        if not cal:
            return None
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date") or cal.get("earningsDate")
            if isinstance(ed, list) and ed:
                first = ed[0]
            else:
                first = ed
        else:
            # DataFrame fallback — older yfinance returns a 2-row DataFrame
            try:
                first = cal.loc["Earnings Date"].iloc[0]
            except Exception:
                return None
        if hasattr(first, "date"):
            return first.date()
        if isinstance(first, date):
            return first
    except Exception as e:
        log.debug("earnings fetch failed for %s: %s", ticker, e)
    return None


def fetch_earnings_events(
    stocks: Iterable[Stock],
    today: date | None = None,
    days_ahead: int = 14,
    cache: DiskCache | None = None,
) -> list[UpcomingEvent]:
    """Pull upcoming earnings for US-listed watchlist stocks (yfinance only).

    KR tickers (pykrx 6-digit) and CRYPTO are skipped because yfinance doesn't
    carry reliable earnings dates for them.
    """
    today = today or date.today()
    cutoff = today + timedelta(days=days_ahead)
    out: list[UpcomingEvent] = []
    for s in stocks:
        if s.country != "US":
            continue
        cache_key = f"earnings_{s.ticker}_{today.isoformat()}"
        cached_iso = cache.get_json(cache_key) if cache is not None else None
        if cached_iso is not None:
            ed = _parse_iso(cached_iso) if isinstance(cached_iso, str) else None
        else:
            ed = _earnings_date_from_yf(s.ticker)
            # cache the result either way so failed lookups don't keep retrying
            if cache is not None:
                cache.set_json(cache_key, ed.isoformat() if ed else "")
        if ed is None or ed < today or ed > cutoff:
            continue
        out.append(UpcomingEvent(
            date=ed.isoformat(),
            name=f"{s.name} 실적",
            kind="earnings",
            impact="high" if s.tier == "leader" else "med",
            ticker=s.ticker,
            note=s.theme,
        ))
    return out


def upcoming_events(
    stocks: Iterable[Stock] | None = None,
    today: date | None = None,
    days_ahead: int = 14,
    include_earnings: bool = True,
    cache: DiskCache | None = None,
    macro_path: Path | None = None,
) -> list[UpcomingEvent]:
    """Return macro + earnings events in the next `days_ahead` days, sorted by date.

    Skips earnings when `stocks` is None or include_earnings is False (the coin
    pipeline only wants macro events).
    """
    today = today or date.today()
    cutoff = today + timedelta(days=days_ahead)

    all_events: list[UpcomingEvent] = []
    for e in load_macro_events(macro_path):
        d = _parse_iso(e.date)
        if d is None or d < today or d > cutoff:
            continue
        all_events.append(e)

    if include_earnings and stocks is not None:
        all_events.extend(fetch_earnings_events(
            stocks, today=today, days_ahead=days_ahead, cache=cache,
        ))

    all_events.sort(key=lambda e: (e.date, 0 if e.impact == "high" else 1))
    return all_events
