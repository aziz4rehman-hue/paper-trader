"""Long-only paper-trading backtester. Not financial advice."""

__version__ = "0.1.0"

from papertrader.backtest import BacktestResult, run_backtest
from papertrader.data import load_csv, sample_path, synthetic_bars

__all__ = [
    "BacktestResult",
    "load_csv",
    "run_backtest",
    "sample_path",
    "synthetic_bars",
    "__version__",
]
