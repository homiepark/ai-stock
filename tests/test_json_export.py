"""JSON serialization safety — NaN/Inf must become null, not bare tokens.

JavaScript's JSON.parse rejects `NaN`/`Infinity`, so any leak into the
exported context would break the Next.js dashboard at build time.
"""
from __future__ import annotations

import json
import math

from ai_stock.report.json_export import _serialize


def test_serialize_converts_nan_to_none():
    assert _serialize(float("nan")) is None
    assert _serialize(float("inf")) is None
    assert _serialize(float("-inf")) is None


def test_serialize_preserves_normal_floats():
    assert _serialize(1.5) == 1.5
    assert _serialize(0.0) == 0.0
    assert _serialize(-3.14) == -3.14


def test_serialize_nested_nan():
    payload = {
        "macro": {"KOSPI": {"value": float("nan"), "change": float("nan")}},
        "verdicts": [{"score": 0.7, "metric": float("inf")}],
    }
    out = _serialize(payload)
    encoded = json.dumps(out, allow_nan=False)
    parsed = json.loads(encoded)
    assert parsed["macro"]["KOSPI"]["value"] is None
    assert parsed["macro"]["KOSPI"]["change"] is None
    assert parsed["verdicts"][0]["metric"] is None
    assert parsed["verdicts"][0]["score"] == 0.7


def test_serialize_numpy_nan():
    """numpy scalars expose .item(); ensure that path also catches NaN."""
    try:
        import numpy as np
    except ImportError:
        return
    assert _serialize(np.float64("nan")) is None
    assert _serialize(np.float64(2.5)) == 2.5
    # sanity: built-in math agrees
    assert math.isnan(np.float64("nan").item())
