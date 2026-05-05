"""Theme momentum + leader identification."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai_stock.config import Stock, Theme
from ai_stock.signals.indicators import momentum


@dataclass
class StockMomentum:
    stock: Stock
    return_1w: float
    return_1m: float
    return_3m: float
    avg_dollar_volume_60d: float
    market_cap: float | None


@dataclass
class ThemeRanking:
    theme_key: str
    theme_name: str
    composite_return: float       # weighted by settings.theme.weights
    avg_return_1w: float
    avg_return_1m: float
    avg_return_3m: float
    cap_leader: Stock | None
    momentum_leader: Stock | None
    members: list[StockMomentum]


def stock_momentum(stock: Stock, prices: pd.DataFrame, market_cap: float | None) -> StockMomentum | None:
    if prices is None or prices.empty or len(prices) < 65:
        return None
    close = prices["close"]
    ret_1w = float(momentum(close, 5).iloc[-1]) if len(close) >= 5 else 0.0
    ret_1m = float(momentum(close, 20).iloc[-1]) if len(close) >= 20 else 0.0
    ret_3m = float(momentum(close, 60).iloc[-1]) if len(close) >= 60 else 0.0
    dollar_vol = float((close * prices["volume"]).tail(60).mean())
    return StockMomentum(stock, ret_1w, ret_1m, ret_3m, dollar_vol, market_cap)


def rank_theme(theme: Theme, members: list[StockMomentum],
               theme_weights: dict[str, float], leader_weights: dict[str, float]) -> ThemeRanking:
    if not members:
        return ThemeRanking(theme.key, theme.name, 0.0, 0.0, 0.0, 0.0, None, None, [])

    n = len(members)
    avg_1w = sum(m.return_1w for m in members) / n
    avg_1m = sum(m.return_1m for m in members) / n
    avg_3m = sum(m.return_3m for m in members) / n
    composite = (
        avg_1w * theme_weights.get("return_1w", 0.30)
        + avg_1m * theme_weights.get("return_1m", 0.40)
        + avg_3m * theme_weights.get("return_3m", 0.30)
    )

    # Leader scoring
    caps = [m.market_cap or 0 for m in members]
    vols = [m.avg_dollar_volume_60d for m in members]
    moms = [m.return_3m for m in members]
    max_cap = max(caps) or 1
    max_vol = max(vols) or 1
    max_mom = max(abs(min(moms, default=0)), abs(max(moms, default=0))) or 1

    cap_leader = max(members, key=lambda m: m.market_cap or 0).stock
    leader_scored = [
        (
            m.stock,
            (m.market_cap or 0) / max_cap * leader_weights.get("market_cap", 0.40)
            + m.avg_dollar_volume_60d / max_vol * leader_weights.get("avg_dollar_volume_60d", 0.30)
            + (m.return_3m / max_mom) * leader_weights.get("momentum_3m", 0.30),
        )
        for m in members
    ]
    momentum_leader = max(leader_scored, key=lambda x: x[1])[0]

    return ThemeRanking(
        theme_key=theme.key,
        theme_name=theme.name,
        composite_return=composite,
        avg_return_1w=avg_1w,
        avg_return_1m=avg_1m,
        avg_return_3m=avg_3m,
        cap_leader=cap_leader,
        momentum_leader=momentum_leader,
        members=members,
    )
