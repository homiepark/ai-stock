"""Backtest Stage 1 — daily label logging + forward-return scoring."""
from ai_stock.backtest.recorder import (
    LABELS_PATH,
    LabelRecord,
    append_labels,
    load_labels,
    record_from_context,
    write_labels,
)
from ai_stock.backtest.forward import fill_forward_returns, summarize, write_summary

__all__ = [
    "LABELS_PATH",
    "LabelRecord",
    "append_labels",
    "load_labels",
    "record_from_context",
    "write_labels",
    "fill_forward_returns",
    "summarize",
    "write_summary",
]
