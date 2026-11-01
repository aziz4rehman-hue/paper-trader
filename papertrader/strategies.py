"""Long-only strategies. Signals use only the history passed in."""

from __future__ import annotations

from papertrader.models import Bar, Order
from papertrader.portfolio import Portfolio


def sma(values: list[float], window: int) -> float | None:
    if window < 1 or len(values) < window:
        return None
    return sum(values[-window:]) / window


def rsi(closes: list[float], period: int = 14) -> float | None:
    """Simple RSI (average gain/loss over the last `period` changes)."""
    if period < 2 or len(closes) < period + 1:
        return None
    window = closes[-(period + 1) :]
    gains = 0.0
    losses = 0.0
    for prev, cur in zip(window, window[1:]):
        diff = cur - prev
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = (gains / period) / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


class BuyAndHold:
    name = "buyhold"

    def __init__(self) -> None:
        self._sent = False

    def on_bar(self, history: list[Bar], portfolio: Portfolio) -> Order | None:
        del portfolio
        if self._sent or not history:
            return None
        self._sent = True
        return Order(target_weight=1.0)


class SmaCross:
    name = "sma"

    def __init__(self, fast: int = 10, slow: int = 30) -> None:
        if fast < 2 or slow <= fast:
            raise ValueError("require 2 <= fast < slow")
        self.fast = fast
        self.slow = slow
        self._target = 0.0

    def on_bar(self, history: list[Bar], portfolio: Portfolio) -> Order | None:
        del portfolio
        closes = [bar.close for bar in history]
        fast = sma(closes, self.fast)
        slow = sma(closes, self.slow)
        if fast is None or slow is None:
            return None
        target = 1.0 if fast > slow else 0.0
        if target == self._target:
            return None
        self._target = target
        return Order(target_weight=target)


class RsiReversion:
    name = "rsi"

    def __init__(self, period: int = 14, low: float = 30, high: float = 70) -> None:
        if not 0 <= low < high <= 100:
            raise ValueError("require 0 <= low < high <= 100")
        self.period = period
        self.low = low
        self.high = high
        self._target = 0.0

    def on_bar(self, history: list[Bar], portfolio: Portfolio) -> Order | None:
        del portfolio
        value = rsi([bar.close for bar in history], self.period)
        if value is None:
            return None
        target = self._target
        if self._target == 0 and value < self.low:
            target = 1.0
        elif self._target == 1 and value > self.high:
            target = 0.0
        if target == self._target:
            return None
        self._target = target
        return Order(target_weight=target)
