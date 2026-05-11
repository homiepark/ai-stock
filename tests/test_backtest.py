"""Backtest Stage-1 — recorder + forward-return scoring + summary.

No network: we feed synthetic price series in directly.
"""
from __future__ import annotations

import json
import pandas as pd

from ai_stock.backtest.recorder import (
    LabelRecord, append_labels, load_labels, write_labels,
)
from ai_stock.backtest import forward


def test_append_and_load_round_trip(tmp_path):
    p = tmp_path / "labels.jsonl"
    rows = [
        LabelRecord(
            date="2026-05-01", ticker="NVDA", asset_class="stock", name="NVIDIA",
            theme="semiconductors", tier="leader", label="STRONG_BUY",
            overheat_level="normal", composite_score=82.0,
            short_score=70, mid_score=75, long_score=80, close=140.0,
        ),
        LabelRecord(
            date="2026-05-01", ticker="MSFT", asset_class="stock", name="Microsoft",
            theme="hyperscalers", tier="leader", label="ACCUMULATE",
            overheat_level="mild", composite_score=64.0,
            short_score=55, mid_score=70, long_score=68, close=410.0,
        ),
    ]
    append_labels(rows, path=p)
    loaded = load_labels(p)
    assert len(loaded) == 2
    assert {r.ticker for r in loaded} == {"NVDA", "MSFT"}


def test_append_dedupes_same_day_same_ticker(tmp_path):
    """Re-recording NVDA on the same date replaces, not duplicates."""
    p = tmp_path / "labels.jsonl"
    first = LabelRecord(
        date="2026-05-01", ticker="NVDA", asset_class="stock", name="NVIDIA",
        theme="semiconductors", tier="leader", label="ACCUMULATE",
        overheat_level="mild", composite_score=64,
        short_score=60, mid_score=65, long_score=66, close=140.0,
    )
    second = LabelRecord(
        date="2026-05-01", ticker="NVDA", asset_class="stock", name="NVIDIA",
        theme="semiconductors", tier="leader", label="STRONG_BUY",
        overheat_level="normal", composite_score=82,
        short_score=80, mid_score=82, long_score=84, close=141.0,
    )
    append_labels([first], path=p)
    append_labels([second], path=p)
    loaded = load_labels(p)
    assert len(loaded) == 1
    assert loaded[0].label == "STRONG_BUY"
    assert loaded[0].composite_score == 82


def test_forward_return_aligns_on_weekday_label():
    """Label issued on 2026-05-01 (Fri). Series indexed by trading days."""
    idx = pd.date_range("2026-04-20", "2026-08-01", freq="B").normalize()
    closes = pd.Series([100.0 + i for i in range(len(idx))], index=idx)

    ret_5 = forward._forward_return(closes, "2026-05-01", 5)
    ret_20 = forward._forward_return(closes, "2026-05-01", 20)
    assert ret_5 is not None and ret_20 is not None
    # synthetic series strictly increasing → returns are positive
    assert ret_5 > 0 and ret_20 > ret_5


def test_forward_return_none_when_window_not_yet_complete():
    idx = pd.date_range("2026-04-20", "2026-05-04", freq="B").normalize()  # too short
    closes = pd.Series([100.0 + i for i in range(len(idx))], index=idx)
    # 60d after 2026-05-01 doesn't exist in the series → None
    assert forward._forward_return(closes, "2026-05-01", 60) is None


def test_fill_forward_returns_uses_cached_prices(tmp_path, monkeypatch):
    """Patch the price fetcher with a synthetic series and confirm rows fill."""
    p = tmp_path / "labels.jsonl"
    rows = [LabelRecord(
        date="2026-05-01", ticker="NVDA", asset_class="stock", name="NVIDIA",
        theme="semiconductors", tier="leader", label="STRONG_BUY",
        overheat_level="normal", composite_score=82,
        short_score=80, mid_score=82, long_score=84, close=100.0,
    )]
    append_labels(rows, path=p)

    idx = pd.date_range("2026-04-20", "2026-08-01", freq="B").normalize()
    closes = pd.Series([100.0 * (1.001 ** i) for i in range(len(idx))], index=idx)

    class FakeStock:
        ticker = "NVDA"; country = "US"; tier = "leader"; name = "NVIDIA"
        theme = "semiconductors"; note = ""; coingecko_id = ""

    monkeypatch.setattr(forward, "_all_watchlist_stocks", lambda: {"NVDA": FakeStock()})
    monkeypatch.setattr(
        forward, "fetch_prices",
        lambda stock, cache=None: pd.DataFrame({"close": closes}),
    )

    n_filled = forward.fill_forward_returns(path=p)
    assert n_filled > 0
    loaded = load_labels(p)
    r = loaded[0]
    assert r.return_5d is not None
    assert r.return_20d is not None
    assert r.return_60d is not None
    assert r.return_60d > r.return_5d  # series grows over time


def test_summarize_buckets_by_label_and_computes_ic():
    rows = []
    for i in range(20):
        score = 50 + i  # 50..69 — higher score means higher score in synthetic data
        # tie return to score so IC should be positive
        rows.append(LabelRecord(
            date=f"2026-0{1 + i // 10}-15", ticker=f"T{i}", asset_class="stock",
            name=f"T{i}", theme="semiconductors", tier="leader",
            label="STRONG_BUY" if score > 65 else "HOLD",
            overheat_level="normal", composite_score=score,
            short_score=score, mid_score=score, long_score=score, close=100.0,
            return_5d=(score - 50) * 0.002,
            return_20d=(score - 50) * 0.005,
            return_60d=(score - 50) * 0.01,
        ))
    s = forward.summarize(rows)
    assert s["n_records"] == 20
    assert s["n_with_5d"] == 20
    assert "STRONG_BUY" in s["by_label"]
    # IC over a monotone score↔return relationship should be strongly positive
    ic_5 = s["signal_ic"]["return_5d"]
    assert ic_5 is not None and ic_5 > 0.5
