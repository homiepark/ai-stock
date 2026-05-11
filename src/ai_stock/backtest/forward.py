"""Forward-return back-fill + label summary.

Runs after each daily pipeline. For each historical label record whose
forward window is now complete (we have prices 5/20/60 trading days after
the label date), compute (close[T+N] / close[T]) - 1 and write it back
into labels.jsonl. Then summarize into the dashboard's JSON.

Bias-free: we only fill forward returns from data that genuinely exists
in the present. Records younger than 5 trading days never get a return_5d.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from ai_stock.backtest.recorder import LABELS_PATH, LabelRecord, load_labels, write_labels
from ai_stock.config import Stock, load_coin_universe, load_universe
from ai_stock.data.cache import DiskCache
from ai_stock.data.prices import fetch_prices

log = logging.getLogger(__name__)

WINDOWS = (5, 20, 60)


def _all_watchlist_stocks() -> dict[str, Stock]:
    out: dict[str, Stock] = {}
    try:
        for s in load_universe().all_stocks():
            out[s.ticker] = s
    except Exception as e:
        log.warning("could not load stock universe: %s", e)
    try:
        for c in load_coin_universe().all_stocks():
            # use symbol as the key to match LabelRecord.ticker
            out[c.ticker] = c
    except Exception as e:
        log.warning("could not load coin universe: %s", e)
    return out


def _ticker_prices(
    ticker: str,
    stocks_by_ticker: dict[str, Stock],
    cache: DiskCache | None,
    price_cache: dict[str, pd.Series],
) -> pd.Series | None:
    """Return tz-naive daily close series for a ticker. Cached per process."""
    if ticker in price_cache:
        return price_cache[ticker]
    stock = stocks_by_ticker.get(ticker)
    if stock is None:
        return None
    try:
        df = fetch_prices(stock, cache=cache)
    except Exception as e:
        log.debug("price fetch failed for %s: %s", ticker, e)
        return None
    if df is None or df.empty or "close" not in df.columns:
        return None
    s = df["close"].copy()
    # Normalize index to date-only for clean alignment with label dates
    try:
        s.index = pd.to_datetime(s.index).normalize()
    except Exception:
        pass
    price_cache[ticker] = s
    return s


def _forward_return(
    close_series: pd.Series,
    label_date: str,
    n: int,
) -> float | None:
    """Return (close[T+N trading days] / close[T]) - 1, or None when unfillable."""
    try:
        target = pd.Timestamp(label_date).normalize()
    except Exception:
        return None
    idx = close_series.index
    # Find the row at-or-after the label date (handle weekend label dates)
    pos_arr = idx.searchsorted(target)
    if pos_arr >= len(idx):
        return None
    pos = int(pos_arr)
    future_pos = pos + n
    if future_pos >= len(close_series):
        return None
    entry = float(close_series.iloc[pos])
    future = float(close_series.iloc[future_pos])
    if entry <= 0:
        return None
    return future / entry - 1


def fill_forward_returns(
    path: Path | None = None,
    cache: DiskCache | None = None,
) -> int:
    """Fill any newly-fillable forward-return columns. Returns rows updated."""
    p = path or LABELS_PATH
    records = load_labels(p)
    if not records:
        return 0

    stocks_by_ticker = _all_watchlist_stocks()
    price_cache: dict[str, pd.Series] = {}

    updated = 0
    for r in records:
        # Skip if already complete
        if r.return_5d is not None and r.return_20d is not None and r.return_60d is not None:
            continue
        series = _ticker_prices(r.ticker, stocks_by_ticker, cache, price_cache)
        if series is None or series.empty:
            continue
        for n in WINDOWS:
            current = getattr(r, f"return_{n}d")
            if current is not None:
                continue
            ret = _forward_return(series, r.date, n)
            if ret is not None:
                setattr(r, f"return_{n}d", round(ret, 6))
                updated += 1

    write_labels(records, path=p)
    return updated


# --- Summary -----------------------------------------------------------------


def _mean(xs: Iterable[float]) -> float | None:
    xs = list(xs)
    return statistics.fmean(xs) if xs else None


def _rank_ic(pairs: list[tuple[float, float]]) -> float | None:
    """Spearman rank correlation between (score, forward_return) pairs.

    Implemented as Pearson on ranks so we don't pull in scipy just for this.
    Returns None when sample is too small for a meaningful estimate.
    """
    if len(pairs) < 10:
        return None
    scores = pd.Series([p[0] for p in pairs]).rank()
    rets = pd.Series([p[1] for p in pairs]).rank()
    val = scores.corr(rets)  # Pearson on ranks == Spearman
    return None if pd.isna(val) else float(val)


def summarize(records: list[LabelRecord]) -> dict:
    """Aggregate forward returns by label, overheat, and overall signal IC."""
    # Per-label means
    by_label: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_overheat: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    score_pairs: dict[str, list[tuple[float, float]]] = defaultdict(list)

    for r in records:
        for n in WINDOWS:
            ret = getattr(r, f"return_{n}d", None)
            if ret is None:
                continue
            by_label[r.label][f"return_{n}d"].append(ret)
            if r.overheat_level:
                by_overheat[r.overheat_level][f"return_{n}d"].append(ret)
            score_pairs[f"return_{n}d"].append((r.composite_score, ret))

    def _summarize_bucket(bucket: dict[str, dict[str, list[float]]]) -> dict:
        out = {}
        for key, by_window in bucket.items():
            entry = {}
            for window, vals in by_window.items():
                entry[window] = {
                    "n": len(vals),
                    "mean": round(_mean(vals) or 0.0, 5) if vals else None,
                }
            out[key] = entry
        return out

    ic = {w: _rank_ic(score_pairs.get(w, [])) for w in (f"return_{n}d" for n in WINDOWS)}

    return {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "n_records": len(records),
        "n_with_5d": sum(1 for r in records if r.return_5d is not None),
        "n_with_20d": sum(1 for r in records if r.return_20d is not None),
        "n_with_60d": sum(1 for r in records if r.return_60d is not None),
        "by_label": _summarize_bucket(by_label),
        "by_overheat": _summarize_bucket(by_overheat),
        "signal_ic": {k: (round(v, 4) if v is not None else None) for k, v in ic.items()},
    }


def write_summary(path: Path) -> dict:
    """Build a summary from the current labels.jsonl and write JSON for the UI."""
    records = load_labels()
    summary = summarize(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    import json
    path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    return summary
