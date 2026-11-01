"""Market and order types. Orders are target weights, not share counts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Order:
    """Target fraction of equity to hold. 0 is flat, 1 is fully long. No shorts."""

    target_weight: float


@dataclass(frozen=True)
class Fill:
    date: str
    side: str
    qty: float
    price: float
    commission: float


@dataclass(frozen=True)
class ClosedTrade:
    entry_date: str
    exit_date: str
    qty: float
    entry_price: float
    exit_price: float
    pnl: float
