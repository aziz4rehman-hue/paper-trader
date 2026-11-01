# paper-trader

Long-only paper-trading backtester in the Python standard library. It replays OHLCV bars, fills **next bar's open** (no lookahead), and charges commission and slippage.

**Not financial advice. This does not place live orders. The bundled series is synthetic.**

On the included demo data, buy-and-hold beats both SMA crossover and RSI. That is the point of a backtester: a strategy can look reasonable and still lose.

## Quick start

```bash
git clone https://github.com/aziz4rehman-hue/paper-trader.git
cd paper-trader
python -m papertrader compare
```

```
strategy      return      cagr     maxDD  sharpe  trades     win
sma           +5.38%    +7.66%    -7.04%    1.11       2   50.0%
rsi          -12.47%   -17.10%   -15.85%   -2.73       2    0.0%
buyhold      +12.88%   +18.60%   -18.28%    1.63       0     n/a
synthetic demo data · not a real market · not financial advice
```

One strategy, with an equity sparkline:

```bash
python -m papertrader backtest --strategy sma
```

```
papertrader · sma
bars            180
equity          10000.00 -> 10538.47
return          +5.38%
cagr            +7.66%
max drawdown    -7.04%
sharpe          1.11
closed trades   2
win rate        50.0%
profit factor   1.40
not financial advice · paper trading only
```

Your own CSV needs a header: `date,open,high,low,close,volume`.

```bash
python -m papertrader backtest --strategy sma --csv my_bars.csv --cash 25000 --commission-bps 5 --slippage-bps 5
```

## What it models

| Piece | Behavior |
|---|---|
| Signal | Uses only bars up to and including today |
| Fill | Next bar's open. A signal on the last bar is dropped |
| Position | One symbol, long or flat. Weight is 0 to 1. No leverage, no shorts |
| Costs | Commission and slippage in basis points, on both sides |
| Stats | Total return, CAGR (252-bar year), max drawdown, Sharpe, win rate, profit factor |

Strategies included:

- `sma` — long when the fast SMA is above the slow SMA (default 10/30), else flat
- `rsi` — buy when simple RSI is under 30, sell when it is over 70
- `buyhold` — go long on the first bar and hold

Buy-and-hold reports `n/a` for win rate because it never closes a trade.

## Use it as a library

```python
from papertrader import load_csv, run_backtest, sample_path
from papertrader.strategies import SmaCross

result = run_backtest(load_csv(sample_path()), SmaCross(fast=10, slow=30), cash=10_000)
print(result.metrics())
```

A strategy is any object with `on_bar(history, portfolio) -> Order | None`.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check next-open fills, that commission reduces P&L, that target weights above 1 are rejected, and that the strategy never receives future bars.

Requires Python 3.10+. No third-party packages.

## License

MIT. Built by [Aziz Rehman](https://github.com/aziz4rehman-hue).
