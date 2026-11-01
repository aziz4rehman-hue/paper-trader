"""Event loop. Orders signal on today's close and fill on the next open."""

from __future__ import annotations

from dataclasses import dataclass, field

from papertrader.metrics import cagr, max_drawdown, profit_factor, sharpe, win_rate
from papertrader.models import Bar, ClosedTrade, Fill, Order
from papertrader.portfolio import Portfolio


@dataclass
class BacktestResult:
    strategy: str
    equity_curve: list[tuple[str, float]]
    fills: list[Fill] = field(default_factory=list)
    closed: list[ClosedTrade] = field(default_factory=list)
    start_equity: float = 0.0
    end_equity: float = 0.0

    def metrics(self) -> dict:
        equity = [value for _, value in self.equity_curve]
        total_return = (self.end_equity / self.start_equity - 1) if self.start_equity else 0.0
        return {
            "start_equity": self.start_equity,
            "end_equity": self.end_equity,
            "total_return": total_return,
            "cagr": cagr(equity),
            "max_drawdown": max_drawdown(equity),
            "sharpe": sharpe(equity),
            "trades": len(self.closed),
            "win_rate": win_rate(self.closed),
            "profit_factor": profit_factor(self.closed),
        }


def run_backtest(
    bars: list[Bar],
    strategy,
    cash: float = 10_000,
    commission_bps: float = 5,
    slippage_bps: float = 5,
) -> BacktestResult:
    if len(bars) < 2:
        raise ValueError("need at least 2 bars")
    portfolio = Portfolio(cash)
    pending: Order | None = None
    curve: list[tuple[str, float]] = []
    for i, bar in enumerate(bars):
        if pending is not None:
            portfolio.rebalance(
                bar.date,
                bar.open,
                pending.target_weight,
                commission_bps,
                slippage_bps,
            )
            pending = None
        curve.append((bar.date, portfolio.equity(bar.close)))
        order = strategy.on_bar(bars[: i + 1], portfolio)
        if order is not None and i < len(bars) - 1:
            pending = order
    return BacktestResult(
        strategy=getattr(strategy, "name", "strategy"),
        equity_curve=curve,
        fills=list(portfolio.fills),
        closed=list(portfolio.closed),
        start_equity=cash,
        end_equity=curve[-1][1],
    )
