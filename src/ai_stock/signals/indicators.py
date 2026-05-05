"""Pure technical indicators on a closing-price series. No I/O, easily testable."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def volume_zscore(volume: pd.Series, window: int = 20) -> pd.Series:
    mean = volume.rolling(window).mean()
    std = volume.rolling(window).std()
    return (volume - mean) / std.replace(0, np.nan)


def momentum(close: pd.Series, periods: int) -> pd.Series:
    """Pct change over N periods."""
    return close.pct_change(periods)


def clamp_score(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if x is None or np.isnan(x):
        return 50.0  # neutral when missing
    return float(max(lo, min(hi, x)))
