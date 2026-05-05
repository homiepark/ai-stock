"""Price data adapter: yfinance for US, pykrx for KR. Returns pandas DataFrames.

Schema: index = trading day (DatetimeIndex, tz-naive), columns = open, high, low, close, volume.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd

from ai_stock.config import Stock
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)


def _fetch_us(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    import yfinance as yf

    df = yf.download(
        ticker, start=start, end=end, progress=False, auto_adjust=True, threads=False
    )
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df[["open", "high", "low", "close", "volume"]]


def _fetch_kr(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    from pykrx import stock as krx

    df = krx.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.rename(columns={"시가": "open", "고가": "high", "저가": "low", "종가": "close", "거래량": "volume"})
    df.index = pd.to_datetime(df.index)
    return df[["open", "high", "low", "close", "volume"]]


def fetch_prices(stock: Stock, days: int = 800, cache: DiskCache | None = None) -> pd.DataFrame:
    """Fetch ~3 years of daily OHLCV. Returns empty DataFrame on failure (caller decides)."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    cache_key = f"prices_{stock.country}_{stock.ticker}_{days}d"

    if cache is not None:
        cached = cache.get_pickle(cache_key)
        if cached is not None:
            return cached

    try:
        df = _fetch_us(stock.ticker, start, end) if stock.country == "US" else _fetch_kr(stock.ticker, start, end)
    except Exception as e:
        log.warning("price fetch failed for %s: %s", stock.ticker, e)
        df = pd.DataFrame()

    if cache is not None and not df.empty:
        cache.set_pickle(cache_key, df)
    return df


def fetch_market_cap(stock: Stock, cache: DiskCache | None = None) -> float | None:
    """Best-effort market cap lookup. Returns USD-denominated value or None."""
    cache_key = f"mcap_{stock.country}_{stock.ticker}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached.get("market_cap")

    cap: float | None = None
    try:
        if stock.country == "US":
            import yfinance as yf
            info = yf.Ticker(stock.ticker).fast_info
            cap = float(info.get("market_cap", 0)) or None
        else:
            from pykrx import stock as krx
            today = datetime.utcnow().strftime("%Y%m%d")
            cap_df = krx.get_market_cap(today, today, stock.ticker)
            if cap_df is not None and not cap_df.empty:
                cap = float(cap_df.iloc[0]["시가총액"])
    except Exception as e:
        log.warning("market cap fetch failed for %s: %s", stock.ticker, e)

    if cache is not None and cap is not None:
        cache.set_json(cache_key, {"market_cap": cap})
    return cap
