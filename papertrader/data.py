"""CSV bars and a seeded synthetic series so the demo runs offline."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from papertrader.models import Bar


def sample_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "sample_ohlcv.csv"


def synthetic_bars(n: int = 180, seed: int = 7, start: float = 100.0) -> list[Bar]:
    """Alternating up/down regimes. This is not a real market."""
    if n < 2:
        raise ValueError("need at least 2 bars")
    rng = random.Random(seed)
    price = start
    day = date(2024, 1, 2)
    bars: list[Bar] = []
    for i in range(n):
        drift = 0.004 if (i // 40) % 2 == 0 else -0.004
        shock = rng.gauss(0, 0.006)
        open_ = price
        close = max(1.0, open_ * (1 + drift + shock))
        high = max(open_, close) * (1 + abs(rng.gauss(0, 0.003)))
        low = min(open_, close) * (1 - abs(rng.gauss(0, 0.003)))
        high = max(high, open_, close)
        low = min(low, open_, close)
        open_, high, low, close = (round(v, 4) for v in (open_, high, low, close))
        high = max(high, open_, close)
        low = min(low, open_, close)
        volume = float(rng.randint(100_000, 500_000))
        bars.append(Bar(day.isoformat(), open_, high, low, close, volume))
        price = close
        day += timedelta(days=1)
        while day.weekday() >= 5:
            day += timedelta(days=1)
    return bars


def write_csv(path: Path, bars: list[Bar]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "open", "high", "low", "close", "volume"])
        for bar in bars:
            writer.writerow([bar.date, bar.open, bar.high, bar.low, bar.close, int(bar.volume)])


def load_csv(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"date", "open", "high", "low", "close", "volume"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError("csv must include date, open, high, low, close, volume")
        for line, row in enumerate(reader, start=2):
            try:
                bar = Bar(
                    date=row["date"].strip(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"bad row on line {line}") from exc
            if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
                raise ValueError(f"ohlc inconsistent on line {line}")
            if min(bar.open, bar.high, bar.low, bar.close) <= 0:
                raise ValueError(f"non-positive price on line {line}")
            bars.append(bar)
    if len(bars) < 2:
        raise ValueError("need at least 2 bars")
    return bars
