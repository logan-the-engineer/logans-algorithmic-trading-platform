"""Unit tests for BacktestEngine.

All tests use a mock MarketDataPort backed by a synthetic DataFrame;
no network calls are made.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from core.domain.backtest import BacktestRun
from core.domain.strategy import Signal, Strategy
from core.engine.backtest_engine import BacktestEngine
from core.ports.market_data import MarketDataPort
from data.feature_pipeline import FeaturePipeline


# Helpers


def make_ohlcv(n: int = 60) -> pd.DataFrame:
    """Return a synthetic 60-row daily OHLCV DataFrame.

    60 rows gives the FeaturePipeline's 20-day rolling window enough data
    to produce non-empty output (~41 feature rows after dropna).
    """
    rng = np.random.default_rng(42)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, n))
    close = np.clip(close, 10.0, None)
    open_ = close * (1.0 + rng.normal(0, 0.002, n))
    high = np.maximum(close, open_) * (1.0 + np.abs(rng.normal(0, 0.003, n)))
    low = np.minimum(close, open_) * (1.0 - np.abs(rng.normal(0, 0.003, n)))
    volume = rng.integers(1_000, 10_000, n).astype(float)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def make_run(**overrides) -> BacktestRun:
    """Return a BacktestRun with sensible defaults, optionally overridden."""
    defaults = dict(
        backtest_id="test-run",
        strategy_id="test",
        symbols=["GC=F"],
        timeframe="1d",
        start="2020-01-01",
        end="2021-01-01",
        initial_cash=10_000.0,
        fees_bps=0.0,
        slippage_bps=0.0,
        parameters={},
    )
    defaults.update(overrides)
    return BacktestRun(**defaults)


class MockMarketData(MarketDataPort):
    """MarketDataPort that returns a fixed DataFrame, ignoring all parameters."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def fetch(self, symbol: str, start: str, end: str, timeframe: str) -> pd.DataFrame:
        """Return the pre-loaded DataFrame unchanged."""
        return self._df.copy()


class SignalSequenceStrategy(Strategy):
    """Strategy that returns signals from a fixed list; HOLD when exhausted."""

    def __init__(self, signals: list[Signal]) -> None:
        self._signals = signals
        self._i = 0

    @property
    def strategy_id(self) -> str:
        return "test_sequence"

    @property
    def name(self) -> str:
        return "Test Sequence Strategy"

    @property
    def supported_symbols(self) -> frozenset[str]:
        return frozenset({"GC=F"})  # matches make_run() default symbol

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Delegate to FeaturePipeline, preserving existing test behavior."""
        from data.feature_pipeline import FeaturePipeline
        return FeaturePipeline().compute(df)

    def generate_signal(self, features: pd.Series) -> Signal:
        """Return the next pre-configured signal, or HOLD if exhausted."""
        if self._i < len(self._signals):
            sig = self._signals[self._i]
        else:
            sig = Signal.HOLD
        self._i += 1
        return sig


# Tests


def test_buy_signal_opens_position_and_records_trade():
    """BUY on the first feature bar creates a Trade(side='BUY') with shares > 0."""
    df = make_ohlcv()
    engine = BacktestEngine(MockMarketData(df))
    # BUY on bar 0; rest are HOLD (force-close will add a SELL at the end)
    engine.run(SignalSequenceStrategy([Signal.BUY]), make_run())

    trade_log = engine._last_result.trade_log
    buy_trades = [t for t in trade_log if t.side == "BUY"]
    assert len(buy_trades) == 1
    assert buy_trades[0].shares > 0


def test_sell_after_buy_closes_position():
    """BUY then SELL produces exactly two trades; shares sold equal shares bought."""
    df = make_ohlcv()
    engine = BacktestEngine(MockMarketData(df))
    engine.run(SignalSequenceStrategy([Signal.BUY, Signal.SELL]), make_run())

    trade_log = engine._last_result.trade_log
    assert len(trade_log) == 2
    assert trade_log[0].side == "BUY"
    assert trade_log[1].side == "SELL"
    assert trade_log[1].shares == trade_log[0].shares


def test_hold_does_not_change_position():
    """All-HOLD strategy: no trades, equity curve stays at initial_cash throughout."""
    df = make_ohlcv()
    initial_cash = 10_000.0
    engine = BacktestEngine(MockMarketData(df))
    engine.run(SignalSequenceStrategy([]), make_run(initial_cash=initial_cash))

    result = engine._last_result
    assert len(result.trade_log) == 0
    assert all(abs(v - initial_cash) < 1e-9 for v in result.equity_curve)


def test_fees_slippage_adjust_effective_price():
    """BUY effective_price > close; SELL effective_price < close when fees > 0."""
    df = make_ohlcv()
    fees_bps = 10.0
    slip_bps = 5.0
    factor = (fees_bps + slip_bps) / 10_000.0

    engine = BacktestEngine(MockMarketData(df))
    engine.run(
        SignalSequenceStrategy([Signal.BUY, Signal.SELL]),
        make_run(fees_bps=fees_bps, slippage_bps=slip_bps),
    )

    features = FeaturePipeline().compute(df)
    close_values = df["close"].reindex(features.index).values

    buy_trade = engine._last_result.trade_log[0]
    sell_trade = engine._last_result.trade_log[1]

    expected_buy_price = close_values[0] * (1.0 + factor)
    expected_sell_price = close_values[1] * (1.0 - factor)

    assert abs(buy_trade.price - expected_buy_price) < 1e-9
    assert abs(sell_trade.price - expected_sell_price) < 1e-9
    assert buy_trade.price > close_values[0]
    assert sell_trade.price < close_values[1]


def test_hold_only_num_trades_and_equity_curve_length():
    """All-HOLD: num_trades == 0, win_rate == 0.0, len(equity_curve) == feature rows."""
    df = make_ohlcv()
    engine = BacktestEngine(MockMarketData(df))
    metrics = engine.run(SignalSequenceStrategy([]), make_run())

    n_feature_rows = len(FeaturePipeline().compute(df))
    assert metrics.num_trades == 0
    assert metrics.win_rate == 0.0
    assert len(engine._last_result.equity_curve) == n_feature_rows


def test_force_close_on_final_bar():
    """BUY with no SELL: engine force-closes at the last feature bar."""
    df = make_ohlcv()
    engine = BacktestEngine(MockMarketData(df))
    # BUY on bar 0, never SELL
    engine.run(SignalSequenceStrategy([Signal.BUY]), make_run())

    trade_log = engine._last_result.trade_log
    assert len(trade_log) == 2
    assert trade_log[0].side == "BUY"
    assert trade_log[1].side == "SELL"

    features = FeaturePipeline().compute(df)
    last_date = str(features.index[-1].date())
    assert trade_log[1].date == last_date


def test_total_return_computed_correctly():
    """total_return matches manual calculation for a BUY-at-bar0, SELL-at-bar1 sequence."""
    df = make_ohlcv()
    initial_cash = 10_000.0

    features = FeaturePipeline().compute(df)
    close_vals = df["close"].reindex(features.index).values
    c0 = float(close_vals[0])
    c1 = float(close_vals[1])

    shares = math.floor(initial_cash / c0)
    remainder = initial_cash - shares * c0
    proceeds = shares * c1
    expected_return = (remainder + proceeds - initial_cash) / initial_cash

    engine = BacktestEngine(MockMarketData(df))
    metrics = engine.run(
        SignalSequenceStrategy([Signal.BUY, Signal.SELL]),
        make_run(initial_cash=initial_cash, fees_bps=0.0, slippage_bps=0.0),
    )

    assert abs(metrics.total_return - expected_return) < 1e-9


def test_sharpe_ratio_zero_when_equity_flat():
    """All-HOLD equity curve is flat (std == 0), so sharpe_ratio must be 0.0."""
    df = make_ohlcv()
    engine = BacktestEngine(MockMarketData(df))
    metrics = engine.run(SignalSequenceStrategy([]), make_run())
    assert metrics.sharpe_ratio == 0.0


def test_value_error_on_empty_dataframe():
    """ValueError is raised when market_data.fetch() returns an empty DataFrame."""
    empty_df = pd.DataFrame()
    engine = BacktestEngine(MockMarketData(empty_df))
    with pytest.raises(ValueError, match="No market data"):
        engine.run(SignalSequenceStrategy([]), make_run())
