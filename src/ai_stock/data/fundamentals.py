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


def fetch_fundamentals(stock: Stock, cache: DiskCache | None = None) -> dict[str, Any]:
    cache_key = f"fund_{stock.country}_{stock.ticker}"
    if cache is not None:
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached
    data = _fetch_us(stock.ticker) if stock.country == "US" else _fetch_kr(stock.ticker)
    if cache is not None:
        cache.set_json(cache_key, data)
    return data
