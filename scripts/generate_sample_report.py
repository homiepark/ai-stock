"""Generate a deterministic sample report (no network) for documentation/preview.

Run from repo root:
    uv run python scripts/generate_sample_report.py
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

import ai_stock.report.daily as daily_module
from ai_stock.config import REPO_ROOT, Stock


def synthetic_prices(seed: int = 42, days: int = 800, start: float = 100.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0008, 0.018, days)
    close = start * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.005, days)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, days)))
    open_ = close * (1 + rng.normal(0, 0.003, days))
    volume = rng.integers(1_000_000, 10_000_000, days).astype(float)
    idx = pd.date_range(end=pd.Timestamp.now("UTC").tz_localize(None).normalize(), periods=days, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


_FUND = {
    "revenue_history": [
        ("2026-04-30", 35e9), ("2026-01-31", 26e9), ("2025-10-31", 22e9), ("2025-07-31", 18e9),
        ("2025-04-30", 15e9), ("2025-01-31", 13e9), ("2024-10-31", 10e9), ("2024-07-31", 8e9),
        ("2024-04-30", 7e9), ("2024-01-31", 6e9), ("2023-10-31", 5.5e9), ("2023-07-31", 5e9),
    ],
    "eps_history": [("TTM", 3.5)],
    "margin_history": [("2026-04-30", 0.75, 0.65, None), ("2025-04-30", 0.70, 0.55, None)],
    "ev_to_sales": 18.5, "pe": 35.0, "peg": 1.2,
    "consensus_eps_revision_30d": 0.04, "consensus_eps_revision_90d": 0.10,
}


def _patch():
    daily_module.fetch_prices = lambda stock, *a, **kw: synthetic_prices(
        seed=sum(ord(c) for c in stock.ticker) % 1000)
    daily_module.fetch_fundamentals = lambda stock, *a, **kw: _FUND
    daily_module.fetch_market_cap = lambda stock, *a, **kw: float(sum(ord(c) for c in stock.ticker)) * 1e9
    daily_module.fetch_macro = lambda *a, **kw: {
        "DGS10": {"name": "US 10Y Yield", "value": 4.25, "change": 0.005},
        "VIXCLS": {"name": "VIX", "value": 14.2, "change": -0.02},
        "USDKRW": {"name": "USD/KRW", "value": 1380.0, "change": 0.001},
    }
    daily_module.fetch_news = lambda *a, **kw: []


def main() -> None:
    os.environ.pop("ANTHROPIC_API_KEY", None)
    _patch()
    out_dir = REPO_ROOT / "reports" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = daily_module.build_daily_report(output_dir=out_dir)
    print(f"Sample report: {path}")


if __name__ == "__main__":
    main()
