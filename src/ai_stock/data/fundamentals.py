"""Fundamentals adapter. Best-effort across yfinance for US and a minimal stub for KR.

Returns a normalized dict with keys:
  revenue_history: list of (period_label, revenue) descending by recency
  eps_history: list of (period_label, eps)
  margin_history: list of (period_label, gross_margin, op_margin, fcf_margin)
  ev_to_sales: float | None
  pe: float | None
  peg: float | None
  consensus_eps_revision_30d: float | None  (fraction, e.g. 0.05 = +5%)
  consensus_eps_revision_90d: float | None
"""
from __future__ import annotations

import logging
from typing import Any

from ai_stock.config import Stock
from ai_stock.data.cache import DiskCache

log = logging.getLogger(__name__)


def _empty() -> dict[str, Any]:
    return {
        "revenue_history": [],
        "eps_history": [],
        "margin_history": [],
        "ev_to_sales": None,
        "pe": None,
        "peg": None,
        "consensus_eps_revision_30d": None,
        "consensus_eps_revision_90d": None,
    }


def _fetch_us(ticker: str) -> dict[str, Any]:
    import yfinance as yf

    t = yf.Ticker(ticker)
    out = _empty()
    try:
        fi = getattr(t, "fast_info", {}) or {}
        info = t.info if hasattr(t, "info") else {}
        # Quarterly income statement
        qis = t.quarterly_income_stmt if hasattr(t, "quarterly_income_stmt") else None
        if qis is not None and not qis.empty:
            rev_row = qis.loc["Total Revenue"] if "Total Revenue" in qis.index else None
            if rev_row is not None:
                out["revenue_history"] = [
                    (str(c.date()), float(v)) for c, v in rev_row.dropna().items()
                ]
            gp_row = qis.loc["Gross Profit"] if "Gross Profit" in qis.index else None
            op_row = qis.loc["Operating Income"] if "Operating Income" in qis.index else None
            if rev_row is not None and gp_row is not None and op_row is not None:
                margins = []
                for c in rev_row.index:
                    rev = float(rev_row.get(c, 0) or 0)
                    if rev <= 0:
                        continue
                    gm = float(gp_row.get(c, 0) or 0) / rev
                    om = float(op_row.get(c, 0) or 0) / rev
                    margins.append((str(c.date()), gm, om, None))
                out["margin_history"] = margins

        # Annual EPS
        if info:
            out["pe"] = info.get("trailingPE")
            out["peg"] = info.get("pegRatio")
            ev = info.get("enterpriseValue")
            rev = info.get("totalRevenue")
            if ev and rev:
                out["ev_to_sales"] = float(ev) / float(rev)
            # Forward / trailing EPS
            te = info.get("trailingEps")
            fe = info.get("forwardEps")
            if te is not None:
                out["eps_history"].append(("TTM", float(te)))
            if fe is not None:
                out["eps_history"].append(("FWD", float(fe)))
    except Exception as e:
        log.warning("us fundamentals failed for %s: %s", ticker, e)
    return out


def _fetch_kr(ticker: str) -> dict[str, Any]:
    """KR fundamentals via pykrx + best-effort. yfinance also works for many KR tickers as TICKER.KS."""
    out = _empty()
    try:
        import yfinance as yf
        # KOSPI = .KS, KOSDAQ = .KQ — try both
        for suffix in (".KS", ".KQ"):
            t = yf.Ticker(ticker + suffix)
            info = getattr(t, "info", {}) or {}
            if info.get("totalRevenue"):
                out["pe"] = info.get("trailingPE")
                out["peg"] = info.get("pegRatio")
                ev = info.get("enterpriseValue")
                rev = info.get("totalRevenue")
                if ev and rev:
                    out["ev_to_sales"] = float(ev) / float(rev)
                te = info.get("trailingEps")
                if te is not None:
                    out["eps_history"].append(("TTM", float(te)))
                break
    except Exception as e:
        log.warning("kr fundamentals failed for %s: %s", ticker, e)
    return out


def _fetch_crypto(coin: Stock, cache: DiskCache | None = None) -> dict[str, Any]:
    """For crypto we don't have traditional fundamentals (PER, EV/Sales, etc).

    Synthesize 'revenue history' from price history so the long-term scorer
    captures momentum. The signal interpretation: a coin whose price is up
    big over 1y still has positive long-term momentum even if there's no
    "revenue" in the equity sense. For coins with real fees (HYPE, AAVE, UNI)
    this is a crude proxy; future work could plug in DefiLlama fee data.
    """
    from ai_stock.data.prices import fetch_prices
    out = _empty()
    prices = fetch_prices(coin, cache=cache)
    if prices is None or prices.empty:
        return out
    closes = prices["close"]
    n = len(closes)
    if n < 60:
        return out

    # Synthesize 12 quarterly buckets from daily close (used by long_term scorer)
    bucket_size = max(1, n // 12)
    revenue_history = []
    for i in range(12):
        start_idx = max(0, n - (i + 1) * bucket_size)
        end_idx = max(0, n - i * bucket_size)
        if end_idx <= start_idx:
            continue
        window = closes.iloc[start_idx:end_idx]
        # 가격 평균을 "분기 매출" 프록시로 — 절대값 무의미, 추세만 의미
        revenue_history.append((str(closes.index[end_idx - 1].date()), float(window.mean())))
    out["revenue_history"] = revenue_history
    return out


def fetch_fundamentals(stock: Stock, cache: DiskCache | None = None) -> dict[str, Any]:
    cache_key = f"fund_{stock.country}_{stock.ticker}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached
    if stock.country == "CRYPTO":
        data = _fetch_crypto(stock, cache=cache)
    elif stock.country == "US":
        data = _fetch_us(stock.ticker)
    else:
        data = _fetch_kr(stock.ticker)
    if cache is not None:
        cache.set_json(cache_key, data)
    return data
