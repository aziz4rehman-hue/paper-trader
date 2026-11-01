import tempfile
import unittest
from pathlib import Path

from papertrader.backtest import run_backtest
from papertrader.data import load_csv, sample_path, synthetic_bars, write_csv
from papertrader.models import Bar, Order
from papertrader.portfolio import Portfolio
from papertrader.strategies import BuyAndHold, RsiReversion, SmaCross


def _bars():
    return [
        Bar("2024-01-02", 100, 100, 100, 100, 1),
        Bar("2024-01-03", 100, 110, 100, 110, 1),
        Bar("2024-01-04", 110, 120, 110, 120, 1),
    ]


class EngineTests(unittest.TestCase):
    def test_buyhold_fills_next_open_without_lookahead(self):
        seen: list[int] = []

        class Recorder(BuyAndHold):
            def on_bar(self, history, portfolio):
                seen.append(len(history))
                self.assert_no_future(history)
                return super().on_bar(history, portfolio)

            def assert_no_future(self, history):
                dates = [bar.date for bar in history]
                self_dates = dates
                assert self_dates == sorted(self_dates)

        result = run_backtest(_bars(), Recorder(), cash=1000, commission_bps=0, slippage_bps=0)
        self.assertEqual(seen, [1, 2, 3])
        self.assertEqual(len(result.fills), 1)
        self.assertEqual(result.fills[0].date, "2024-01-03")
        self.assertAlmostEqual(result.fills[0].price, 100)
        self.assertAlmostEqual(result.end_equity, 1200)

    def test_commission_lowers_result(self):
        free = run_backtest(_bars(), BuyAndHold(), cash=1000, commission_bps=0, slippage_bps=0)
        paid = run_backtest(_bars(), BuyAndHold(), cash=1000, commission_bps=50, slippage_bps=0)
        self.assertLess(paid.end_equity, free.end_equity)

    def test_rejects_leverage(self):
        portfolio = Portfolio(1000)
        with self.assertRaises(ValueError):
            portfolio.rebalance("2024-01-02", 100, 1.5, 0, 0)

    def test_sma_trades_on_regimes_and_stays_long_only(self):
        bars = synthetic_bars()
        result = run_backtest(bars, SmaCross(), cash=10_000)
        self.assertGreaterEqual(result.metrics()["trades"], 1)
        self.assertGreater(result.end_equity, 0)
        for fill in result.fills:
            self.assertIn(fill.side, {"buy", "sell"})
            self.assertGreater(fill.qty, 0)
        stats = result.metrics()
        for key in ("total_return", "cagr", "max_drawdown", "sharpe"):
            self.assertEqual(stats[key], stats[key])  # not NaN
        self.assertLessEqual(stats["max_drawdown"], 0)

    def test_rsi_runs(self):
        result = run_backtest(synthetic_bars(), RsiReversion(), cash=10_000)
        self.assertEqual(len(result.equity_curve), 180)

    def test_csv_roundtrip_matches_generator(self):
        bars = synthetic_bars()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bars.csv"
            write_csv(path, bars)
            loaded = load_csv(path)
        self.assertEqual(loaded, bars)
        self.assertEqual(load_csv(sample_path()), synthetic_bars())

    def test_bad_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("date,open,high,low,close,volume\n2024-01-02,10,9,8,10,1\n2024-01-03,10,11,9,10,1\n")
            with self.assertRaises(ValueError):
                load_csv(path)


class OrderTests(unittest.TestCase):
    def test_flat_order_weight(self):
        self.assertEqual(Order(target_weight=0).target_weight, 0)


if __name__ == "__main__":
    unittest.main()
