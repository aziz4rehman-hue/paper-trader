"""CLI for one strategy or a three-way comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

from papertrader import __version__
from papertrader.backtest import BacktestResult, run_backtest
from papertrader.data import load_csv, sample_path
from papertrader.strategies import BuyAndHold, RsiReversion, SmaCross

_BLOCKS = "▁▂▃▄▅▆▇█"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="papertrader",
        description="Paper-trade backtester. Not financial advice. No live orders.",
    )
    parser.add_argument("--version", action="version", version=f"papertrader {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    backtest = sub.add_parser("backtest", help="Run one strategy")
    _add_common(backtest)
    backtest.add_argument("--strategy", choices=["sma", "rsi", "buyhold"], default="sma")
    backtest.add_argument("--fast", type=int, default=10)
    backtest.add_argument("--slow", type=int, default=30)

    compare = sub.add_parser("compare", help="Compare sma, rsi, and buy-and-hold")
    _add_common(compare)
    return parser


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cash", type=float, default=10_000)
    parser.add_argument("--commission-bps", type=float, default=5)
    parser.add_argument("--slippage-bps", type=float, default=5)
    parser.add_argument("--csv", default="", help="OHLCV csv. Defaults to the bundled synthetic series.")


def make_strategy(name: str, fast: int = 10, slow: int = 30):
    if name == "sma":
        return SmaCross(fast=fast, slow=slow)
    if name == "rsi":
        return RsiReversion()
    if name == "buyhold":
        return BuyAndHold()
    raise ValueError(name)


def sparkline(values: list[float], width: int = 42) -> str:
    if not values:
        return ""
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
    lo, hi = min(sampled), max(sampled)
    if hi == lo:
        return _BLOCKS[0] * len(sampled)
    out = []
    for value in sampled:
        index = int((value - lo) / (hi - lo) * (len(_BLOCKS) - 1))
        out.append(_BLOCKS[index])
    return "".join(out)


def _pct(value: float) -> str:
    return f"{value * 100:+.2f}%"


def _maybe_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _factor(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value == float("inf"):
        return "inf"
    return f"{value:.2f}"


def format_result(result: BacktestResult) -> str:
    stats = result.metrics()
    equity = [value for _, value in result.equity_curve]
    lines = [
        f"papertrader · {result.strategy}",
        f"bars            {len(result.equity_curve)}",
        f"equity          {stats['start_equity']:.2f} -> {stats['end_equity']:.2f}",
        f"return          {_pct(stats['total_return'])}",
        f"cagr            {_pct(stats['cagr'])}",
        f"max drawdown    {_pct(stats['max_drawdown'])}",
        f"sharpe          {stats['sharpe']:.2f}",
        f"closed trades   {stats['trades']}",
        f"win rate        {_maybe_pct(stats['win_rate'])}",
        f"profit factor   {_factor(stats['profit_factor'])}",
        f"curve           {sparkline(equity)}",
        "not financial advice · paper trading only",
    ]
    return "\n".join(lines)


def format_compare(results: list[BacktestResult]) -> str:
    header = f"{'strategy':<10}{'return':>10}{'cagr':>10}{'maxDD':>10}{'sharpe':>8}{'trades':>8}{'win':>8}"
    rows = [header]
    for result in results:
        stats = result.metrics()
        rows.append(
            f"{result.strategy:<10}"
            f"{_pct(stats['total_return']):>10}"
            f"{_pct(stats['cagr']):>10}"
            f"{_pct(stats['max_drawdown']):>10}"
            f"{stats['sharpe']:>8.2f}"
            f"{stats['trades']:>8}"
            f"{_maybe_pct(stats['win_rate']):>8}"
        )
    rows.append("synthetic demo data · not a real market · not financial advice")
    return "\n".join(rows)


def load_bars(csv_path: str):
    path = Path(csv_path) if csv_path else sample_path()
    return load_csv(path)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bars = load_bars(args.csv)
    if args.cmd == "backtest":
        strategy = make_strategy(args.strategy, args.fast, args.slow)
        result = run_backtest(
            bars,
            strategy,
            cash=args.cash,
            commission_bps=args.commission_bps,
            slippage_bps=args.slippage_bps,
        )
        print(format_result(result))
        return 0
    results = [
        run_backtest(bars, make_strategy(name), cash=args.cash,
                     commission_bps=args.commission_bps, slippage_bps=args.slippage_bps)
        for name in ("sma", "rsi", "buyhold")
    ]
    print(format_compare(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
