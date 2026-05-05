"""Macro snapshot via yfinance for indices and FRED (optional) for rates."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)

# Use yfinance index/proxy tickers for resilience when FRED key is absent
_YF_PROXIES = {
    "DGS10": "^TNX",       # 10Y yield (×10 scale on yfinance)
    "DTWEXBGS": "DX-Y.NYB", # DXY
    "VIXCLS": "^VIX",
    "NASDAQCOM": "^IXIC",
    "KOSPI": "^KS11",
    "USDKRW": "KRW=X",
}


def _yf_latest(ticker: str) -> tuple[float, float] | None:
    """Returns (latest_close, pct_change_1d) or None."""
    try:
        import yfinance as yf
        end = datetime.utcnow()
        start = end - timedelta(days=10)
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False, threads=False)
        if df is None or df.empty or len(df) < 2:
            return None
        if hasattr(df.columns, "get_level_values"):
            close = df["Close"].iloc[:, 0] if hasattr(df["Close"], "iloc") and df["Close"].ndim > 1 else df["Close"]
        else:
            close = df["Close"]
        latest = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        return latest, (latest - prev) / prev if prev else 0.0
    except Exception as e:
        log.warning("macro yf %s failed: %s", ticker, e)
        return None


def fetch_macro(series_ids: list[dict[str, str]] | None = None, cache: DiskCache | None = None) -> dict[str, Any]:
    series_ids = series_ids or []
    cache_key = "macro_snapshot"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

    out: dict[str, Any] = {}
    items = list(series_ids) + [
        {"id": "KOSPI", "name": "KOSPI"},
        {"id": "USDKRW", "name": "USD/KRW"},
    ]
    for s in items:
        sid = s["id"]
        proxy = _YF_PROXIES.get(sid, sid)
        result = _yf_latest(proxy)
        if result is None:
            continue
        latest, change = result
        # Adjust 10Y yield: yfinance ^TNX is in basis-point-like units (e.g. 42.5 = 4.25%)
        if sid == "DGS10":
            latest = latest / 10.0
        out[sid] = {"name": s.get("name", sid), "value": latest, "change": change}

    if cache is not None and out:
        cache.set_json(cache_key, out)
    return out
