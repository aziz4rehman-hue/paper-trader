"""Cash and a single long position. Fills include commission and slippage."""

from __future__ import annotations

from papertrader.models import ClosedTrade, Fill


class Portfolio:
    def __init__(self, cash: float) -> None:
        if cash <= 0:
            raise ValueError("cash must be positive")
        self.cash = float(cash)
        self.qty = 0.0
        self.avg_price = 0.0
        self.entry_date: str | None = None
        self.closed: list[ClosedTrade] = []
        self.fills: list[Fill] = []

    def equity(self, price: float) -> float:
        return self.cash + self.qty * price

    def rebalance(
        self,
        date: str,
        raw_price: float,
        target_weight: float,
        commission_bps: float,
        slippage_bps: float,
    ) -> Fill | None:
        if not 0 <= target_weight <= 1:
            raise ValueError("target_weight must be between 0 and 1")
        if raw_price <= 0:
            raise ValueError("price must be positive")
        if commission_bps < 0 or slippage_bps < 0:
            raise ValueError("costs cannot be negative")

        equity = self.equity(raw_price)
        delta = target_weight * equity - self.qty * raw_price
        if abs(delta) < 1e-6:
            return None

        if delta > 0:
            price = raw_price * (1 + slippage_bps / 10_000)
            unit = price * (1 + commission_bps / 10_000)
            qty = min(delta / price, self.cash / unit)
            if qty <= 1e-10:
                return None
            commission = qty * price * commission_bps / 10_000
            if self.qty <= 1e-12:
                self.entry_date = date
                self.avg_price = price
            else:
                self.avg_price = (self.avg_price * self.qty + price * qty) / (self.qty + qty)
            self.qty += qty
            self.cash -= qty * price + commission
            fill = Fill(date, "buy", qty, price, commission)
        else:
            price = raw_price * (1 - slippage_bps / 10_000)
            qty = min(self.qty, (-delta) / price)
            if qty <= 1e-10:
                return None
            commission = qty * price * commission_bps / 10_000
            pnl = (price - self.avg_price) * qty - commission
            self.closed.append(
                ClosedTrade(
                    entry_date=self.entry_date or date,
                    exit_date=date,
                    qty=qty,
                    entry_price=self.avg_price,
                    exit_price=price,
                    pnl=pnl,
                )
            )
            self.qty -= qty
            self.cash += qty * price - commission
            if self.qty <= 1e-8:
                self.qty = 0.0
                self.avg_price = 0.0
                self.entry_date = None
            fill = Fill(date, "sell", qty, price, commission)

        if self.cash < -1e-6:
            raise RuntimeError("cash went negative")
        self.fills.append(fill)
        return fill
