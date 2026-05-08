"""CoinGecko adapter — free public API.

Returns the same DataFrame schema as stock prices (open/high/low/close/volume,
DatetimeIndex, tz-naive). For crypto OHL we don't have direct access on the
free tier, so we synthesize open=high=low=close. The signals only consume
close + volume, so this is fine.

Free tier rate limits: ~30 calls/minute. We aggressively cache and sleep
between live calls.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests

from ai_stock.config import Stock
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
RATE_LIMIT_SLEEP_SECONDS = 2.5


def _sleep_for_rate_limit() -> None:
    """Conservative sleep between live calls to stay under 30/min."""
    time.sleep(RATE_LIMIT_SLEEP_SECONDS)


def _request(url: str, params: dict[str, Any] | None = None, timeout: int = 30) -> Any | None:
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": "ai-stock/0.1"})
        if r.status_code == 429:
            log.warning("CoinGecko 429 rate limit; backing off 30s")
            time.sleep(30)
            r = requests.get(url, params=params, timeout=timeout,
                             headers={"User-Agent": "ai-stock/0.1"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("CoinGecko request failed (%s): %s", url, e)
        return None


def fetch_coin_prices(coin: Stock, days: int = 365,
                      cache: DiskCache | None = None) -> pd.DataFrame:
    """Daily prices + volumes for the past N days. Returns empty DF on failure."""
    cgid = coin.coingecko_id
    if not cgid:
        log.warning("No coingecko_id for %s; skipping", coin.ticker)
        return pd.DataFrame()

    cache_key = f"coin_prices_{cgid}_{days}d"
    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached

    _sleep_for_rate_limit()
    data = _request(f"{COINGECKO_BASE}/coins/{cgid}/market_chart",
                    params={"vs_currency": "usd", "days": days})
    if not data:
        return pd.DataFrame()

    prices = data.get("prices") or []
    volumes = data.get("total_volumes") or []
    if not prices:
        return pd.DataFrame()

    # Align by timestamp; CoinGecko sometimes returns mismatched lengths
    vol_lookup = {int(v[0]): float(v[1]) for v in volumes}
    rows = []
    for p in prices:
        ts_ms = int(p[0])
        close = float(p[1])
        rows.append({
            "ts": ts_ms,
            "close": close,
            "volume": vol_lookup.get(ts_ms, 0.0),
        })
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["ts"], unit="ms").dt.tz_localize(None).normalize()
    df = df.drop(columns=["ts"])
    # CoinGecko free tier doesn't expose OHL on this endpoint — fill with close
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]
    df = df[["open", "high", "low", "close", "volume"]]
    # Drop duplicate-day rows (free tier sometimes returns intraday near "now")
    df = df[~df.index.duplicated(keep="last")]

    if cache is not None and not df.empty:
        cache.set_pickle(cache_key, df)
    return df


def fetch_coin_market_caps(coingecko_ids: list[str],
                           cache: DiskCache | None = None) -> dict[str, float]:
    """One bulk call for market caps + 24h price change. Returns {id: market_cap_usd}.

    Also caches per-id via prefixed keys so the verdict prompt can find them.
    """
    if not coingecko_ids:
        return {}
    cache_key = "coin_marketcaps_" + "_".join(sorted(coingecko_ids))[:100]
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return {k: float(v) for k, v in cached.items()}

    _sleep_for_rate_limit()
    # CoinGecko caps `ids` query param length; chunk into 50 at a time
    out: dict[str, float] = {}
    for i in range(0, len(coingecko_ids), 50):
        chunk = coingecko_ids[i:i + 50]
        data = _request(f"{COINGECKO_BASE}/coins/markets", params={
            "vs_currency": "usd",
            "ids": ",".join(chunk),
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1,
        })
        if not data:
            continue
        for row in data:
            mcap = row.get("market_cap")
            if mcap:
                out[row["id"]] = float(mcap)
        if i + 50 < len(coingecko_ids):
            _sleep_for_rate_limit()

    if cache is not None and out:
        cache.set_json(cache_key, out)
    return out


def fetch_global_snapshot(cache: DiskCache | None = None) -> dict[str, Any]:
    """Market-wide context: BTC dominance, total market cap, ETH/BTC ratio.

    Returns {macro_id: {name, value, change}} in the same shape as stock macro.
    """
    cache_key = "coin_global_snapshot"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

    out: dict[str, Any] = {}

    # 1. Global metrics (BTC dominance, total mcap)
    _sleep_for_rate_limit()
    g = _request(f"{COINGECKO_BASE}/global")
    if g and "data" in g:
        d = g["data"]
        try:
            btc_dom = float(d["market_cap_percentage"]["btc"])
            total_mcap = float(d["total_market_cap"]["usd"])
            mcap_change_24h = float(d.get("market_cap_change_percentage_24h_usd", 0)) / 100
            out["BTC_DOMINANCE"] = {"name": "BTC 도미넌스 (%)", "value": btc_dom, "change": 0.0}
            out["TOTAL_MCAP"] = {"name": "전체 시총 ($T)", "value": total_mcap / 1e12, "change": mcap_change_24h}
        except (KeyError, TypeError, ValueError) as e:
            log.warning("parsing /global response failed: %s", e)

    # 2. ETH/BTC ratio — alt-season indicator
    _sleep_for_rate_limit()
    s = _request(f"{COINGECKO_BASE}/simple/price",
                 params={"ids": "bitcoin,ethereum", "vs_currencies": "usd",
                         "include_24hr_change": "true"})
    if s and "bitcoin" in s and "ethereum" in s:
        try:
            btc = float(s["bitcoin"]["usd"])
            eth = float(s["ethereum"]["usd"])
            ratio = eth / btc
            btc_chg = float(s["bitcoin"].get("usd_24h_change", 0)) / 100
            eth_chg = float(s["ethereum"].get("usd_24h_change", 0)) / 100
            out["ETH_BTC"] = {"name": "ETH/BTC", "value": ratio, "change": eth_chg - btc_chg}
        except (KeyError, TypeError, ValueError):
            pass

    if cache is not None and out:
        cache.set_json(cache_key, out)
    return out
