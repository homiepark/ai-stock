import pandas as pd

from ai_stock.signals.long_term import long_term_signal
from ai_stock.signals.mid_term import mid_term_signal
from ai_stock.signals.short_term import latest_metrics, short_term_signal


def test_short_term_returns_score(synthetic_prices):
    res = short_term_signal(synthetic_prices())
    assert 0.0 <= res.score <= 100.0
    assert set(res.components) == {"rsi", "macd", "ma50_distance", "volume_spike", "momentum_5_20"}
    assert len(res.rationale) == 5


def test_short_term_handles_short_series():
    df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
    res = short_term_signal(df)
    assert res.score == 50.0


def test_mid_term_with_fundamentals(synthetic_prices, sample_fundamentals):
    res = mid_term_signal(synthetic_prices(), sample_fundamentals, benchmark_prices=synthetic_prices(seed=7))
    assert 0.0 <= res.score <= 100.0


def test_long_term_strong_growth(sample_fundamentals):
    res = long_term_signal(sample_fundamentals)
    # Synthetic fundamentals show >40% CAGR → revenue_cagr component should be >= 80
    assert res.components["revenue_cagr"] >= 80.0


def test_latest_metrics_keys(synthetic_prices):
    m = latest_metrics(synthetic_prices())
    assert "last_close" in m and "rsi14" in m and "ma50" in m
