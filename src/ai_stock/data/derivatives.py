"""Binance USDT-M futures derivatives — funding rate, OI, long/short ratio.

All endpoints are public (no API key) and free. Used to add a "leverage
crowding" context to coin trade plans:

  + funding 높음 → 롱 사이드 squeeze risk
  − funding 낮음 → 숏 squeeze risk
  OI 상승 + 가격 하락 → 새 숏 진입 (약세 확인)
  OI 상승 + 가격 상승 → 새 롱 진입 (강세 확인)
  long/short ratio > 1.5 → 리테일 롱 과열 (역지표)

Coins not listed on Binance USDT-M (or those with thin OI like very new
alts) return None — the trade-plan UI then hides the derivatives card.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)

BINANCE_FUTURES_BASE = "https://fapi.binance.com"

# Tickers that need explicit mapping when ticker + "USDT" doesn't work.
# Most majors auto-resolve, so this is just exceptions.
_TICKER_OVERRIDES: dict[str, str] = {
    # Add here if needed, e.g. "FET": "FETUSDT" but FET already works
    # Some renamed pairs may need overrides; left empty for now.
}


@dataclass
class DerivativesContext:
    symbol: str
    funding_rate_8h: float          # current 8-hour funding (decimal, 0.0001 = 0.01%)
    funding_rate_annual: float      # rate × 3 × 365 (rough annualized)
    long_short_ratio: float | None  # global account long/short, None if unavailable
    oi_change_24h_pct: float | None # 24h open-interest change
    bias: str                       # "long_crowded" | "short_crowded" | "neutral"
    bias_note: str                  # short Korean explanation
    source: str = "binance"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


def _symbol_for(ticker: str) -> str:
    """Convert a watchlist ticker to a Binance USDT-M symbol."""
    if ticker in _TICKER_OVERRIDES:
        return _TICKER_OVERRIDES[ticker]
    return ticker.upper() + "USDT"


def _get(url: str, params: dict | None = None, timeout: int = 8) -> Any | None:
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": "ai-stock/0.1"})
        if r.status_code == 400:
            return None  # symbol not on Binance
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.debug("binance %s failed: %s", url, e)
        return None


def _funding_rate(symbol: str) -> float | None:
    data = _get(f"{BINANCE_FUTURES_BASE}/fapi/v1/premiumIndex",
                params={"symbol": symbol})
    if not data or "lastFundingRate" not in data:
        return None
    try:
        return float(data["lastFundingRate"])
    except (ValueError, TypeError):
        return None


def _long_short_ratio(symbol: str) -> float | None:
    # 5m intervals, take the most recent. Returns the last 30 buckets.
    data = _get(
        f"{BINANCE_FUTURES_BASE}/futures/data/globalLongShortAccountRatio",
        params={"symbol": symbol, "period": "4h", "limit": 1},
    )
    if not data or not isinstance(data, list) or not data:
        return None
    try:
        return float(data[0]["longShortRatio"])
    except (KeyError, ValueError, TypeError):
        return None


def _oi_change_24h(symbol: str) -> float | None:
    """Compare current OI to OI ~24h ago using the 4h history endpoint."""
    data = _get(
        f"{BINANCE_FUTURES_BASE}/futures/data/openInterestHist",
        params={"symbol": symbol, "period": "4h", "limit": 7},
    )
    if not data or not isinstance(data, list) or len(data) < 2:
        return None
    try:
        latest = float(data[-1]["sumOpenInterest"])
        oldest = float(data[0]["sumOpenInterest"])
        if oldest <= 0:
            return None
        return (latest - oldest) / oldest
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        return None


def _classify_bias(funding_8h: float | None, ls_ratio: float | None) -> tuple[str, str]:
    """Heuristic crowding classification with one-line Korean explanation."""
    notes: list[str] = []
    bias = "neutral"

    if funding_8h is not None:
        if funding_8h > 0.0005:
            bias = "long_crowded"
            notes.append(f"funding +{funding_8h * 100:.3f}%/8h (롱 과밀)")
        elif funding_8h < -0.0003:
            bias = "short_crowded"
            notes.append(f"funding {funding_8h * 100:.3f}%/8h (숏 과밀)")

    if ls_ratio is not None:
        if ls_ratio > 1.6:
            notes.append(f"L/S {ls_ratio:.2f} (롱 과열)")
            if bias == "neutral":
                bias = "long_crowded"
        elif ls_ratio < 0.6:
            notes.append(f"L/S {ls_ratio:.2f} (숏 과열)")
            if bias == "neutral":
                bias = "short_crowded"

    if not notes:
        note = "포지셔닝 균형. 단기 squeeze 압력 낮음."
    elif bias == "long_crowded":
        note = " · ".join(notes) + " — 단기 롱 squeeze 위험, 익절 보수적."
    elif bias == "short_crowded":
        note = " · ".join(notes) + " — 숏 squeeze 가능, 롱 진입엔 유리."
    else:
        note = " · ".join(notes)

    return bias, note


def fetch_4h_klines(ticker: str, limit: int = 180, cache: DiskCache | None = None):
    """Fetch ~30 days of 4-hour candles from Binance futures. Returns a
    pandas DataFrame indexed by datetime, or None when the symbol is missing.
    """
    import pandas as pd
    symbol = _symbol_for(ticker)
    cache_key = f"klines_4h_{symbol}_{limit}"
    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached
    data = _get(
        f"{BINANCE_FUTURES_BASE}/fapi/v1/klines",
        params={"symbol": symbol, "interval": "4h", "limit": limit},
        timeout=10,
    )
    if not data or not isinstance(data, list):
        return None
    rows = []
    for k in data:
        try:
            rows.append({
                "ts": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })
        except (ValueError, TypeError, IndexError):
            continue
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df["ts"], unit="ms")
    df = df.drop(columns=["ts"])
    if cache is not None:
        cache.set_pickle(cache_key, df)
    return df


def fetch_derivatives(
    ticker: str,
    cache: DiskCache | None = None,
) -> DerivativesContext | None:
    """One-shot derivatives snapshot for a coin ticker. Returns None when
    the coin isn't on Binance futures or every API call fails."""
    symbol = _symbol_for(ticker)
    cache_key = f"deriv_{symbol}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            try:
                return DerivativesContext(**cached)
            except Exception:
                pass

    funding = _funding_rate(symbol)
    if funding is None:
        # Symbol not on Binance futures → silently bail
        return None

    # Stagger calls slightly so Binance doesn't rate-limit on a tight loop
    time.sleep(0.1)
    ls = _long_short_ratio(symbol)
    time.sleep(0.1)
    oi_chg = _oi_change_24h(symbol)

    bias, note = _classify_bias(funding, ls)
    ctx = DerivativesContext(
        symbol=symbol,
        funding_rate_8h=funding,
        funding_rate_annual=funding * 3 * 365,
        long_short_ratio=ls,
        oi_change_24h_pct=oi_chg,
        bias=bias,
        bias_note=note,
    )
    if cache is not None:
        cache.set_json(cache_key, ctx.to_dict())
    return ctx
