import numpy as np
import pandas as pd
import pytest

from ai_stock.config import Stock


def _synthetic_prices(days: int = 800, start: float = 100.0, drift: float = 0.0008,
                      vol: float = 0.018, seed: int = 42) -> pd.DataFrame:
    """Geometric Brownian motion-ish series, deterministic for tests."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, days)
    close = start * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.005, days)))
    low = close * (1 - np.abs(rng.normal(0, 0.005, days)))
    open_ = close * (1 + rng.normal(0, 0.003, days))
    volume = rng.integers(1_000_000, 10_000_000, days).astype(float)
    idx = pd.date_range(end=pd.Timestamp.now("UTC").tz_localize(None).normalize(), periods=days, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


@pytest.fixture
def synthetic_prices():
    return _synthetic_prices


@pytest.fixture
def sample_stock():
    return Stock(ticker="NVDA", country="US", tier="leader", name="NVIDIA",
                 note="AI 가속기 압도적 점유", theme="semiconductors")


@pytest.fixture
def sample_fundamentals():
    return {
        "revenue_history": [
            ("2026-04-30", 35_000_000_000),
            ("2026-01-31", 26_000_000_000),
            ("2025-10-31", 22_000_000_000),
            ("2025-07-31", 18_000_000_000),
            ("2025-04-30", 15_000_000_000),
            ("2025-01-31", 13_000_000_000),
            ("2024-10-31", 10_000_000_000),
            ("2024-07-31", 8_000_000_000),
            ("2024-04-30", 7_000_000_000),
            ("2024-01-31", 6_000_000_000),
            ("2023-10-31", 5_500_000_000),
            ("2023-07-31", 5_000_000_000),
        ],
        "eps_history": [("TTM", 3.5)],
        "margin_history": [
            ("2026-04-30", 0.75, 0.65, None),
            ("2025-04-30", 0.70, 0.55, None),
        ],
        "ev_to_sales": 18.5,
        "pe": 35.0,
        "peg": 1.2,
        "consensus_eps_revision_30d": 0.04,
        "consensus_eps_revision_90d": 0.10,
    }
