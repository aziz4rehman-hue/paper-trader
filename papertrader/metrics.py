"""Performance stats from an equity curve and closed trades."""

from __future__ import annotations

import math

from papertrader.models import ClosedTrade


def max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return worst


def sharpe(equity: list[float], periods_per_year: float = 252) -> float:
    returns = [(b - a) / a for a, b in zip(equity, equity[1:]) if a > 0]
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((item - mean) ** 2 for item in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean / std) * math.sqrt(periods_per_year)


def cagr(equity: list[float], periods_per_year: float = 252) -> float:
    if len(equity) < 2 or equity[0] <= 0 or equity[-1] <= 0:
        return 0.0
    years = (len(equity) - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return (equity[-1] / equity[0]) ** (1 / years) - 1


def profit_factor(trades: list[ClosedTrade]) -> float | None:
    gains = sum(trade.pnl for trade in trades if trade.pnl > 0)
    losses = -sum(trade.pnl for trade in trades if trade.pnl < 0)
    if losses == 0:
        return None if gains == 0 else math.inf
    return gains / losses


def win_rate(trades: list[ClosedTrade]) -> float | None:
    if not trades:
        return None
    wins = sum(1 for trade in trades if trade.pnl > 0)
    return wins / len(trades)
