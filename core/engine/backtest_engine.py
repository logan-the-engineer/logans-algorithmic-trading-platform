from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import List

from core.domain.backtest import BacktestMetrics, BacktestRun
from core.domain.strategy import Signal, Strategy
from core.ports.market_data import MarketDataPort
from data.feature_pipeline import FeaturePipeline


@dataclass
class Trade:
    """Record of a single executed trade."""

    date: str          # ISO-format date string of the bar
    side: str          # "BUY" or "SELL"
    price: float       # effective execution price after fees and slippage
    shares: float      # number of shares transacted
    cash_flow: float   # signed cash impact: negative for BUY (outflow), positive for SELL (inflow)
    fees: float        # fee and slippage drag in dollars (shares * close * factor)
    cash_after: float  # cash balance immediately after this trade


@dataclass
class SimulationResult:
    """Full internal output of a backtest run."""

    equity_curve: List[float] = field(default_factory=list)
    trade_log: List[Trade] = field(default_factory=list)


class BacktestEngine:
    """Runs a bar-by-bar backtest simulation for a single symbol.

    The engine fetches OHLCV data via a MarketDataPort, computes technical
    features via FeaturePipeline, then iterates row-by-row calling the
    strategy for signals. A long-only, all-in/all-out position model is
    used: BUY buys as many whole shares as cash allows; SELL sells all
    shares. Any open position is force-closed at the final bar.
    """

    def __init__(self, market_data: MarketDataPort) -> None:
        """
        Args:
            market_data: Adapter used to fetch OHLCV price data.
        """
        self._market_data = market_data
        self._last_result: SimulationResult | None = None

    def run(self, strategy: Strategy, run: BacktestRun) -> BacktestMetrics:
        """Execute the bar-by-bar simulation and return performance metrics.

        Fetches data for run.symbols[0], applies FeaturePipeline, then steps
        through each feature row calling strategy.generate_signal(). After
        the simulation, computes and returns BacktestMetrics. The full
        SimulationResult (equity curve and trade log) is stored on
        self._last_result for inspection.

        Args:
            strategy: Trading strategy whose generate_signal() is called on
                      each feature row.
            run:      BacktestRun configuration (dates, initial capital,
                      fees, slippage).

        Returns:
            BacktestMetrics with total_return, cagr, sharpe_ratio,
            max_drawdown, win_rate, and num_trades populated.

        Raises:
            ValueError: If market_data.fetch() returns an empty DataFrame.
        """
        df = self._market_data.fetch(
            run.symbols[0], run.start, run.end, run.timeframe
        )
        if df.empty:
            raise ValueError(
                f"No market data returned for {run.symbols[0]} "
                f"({run.start} \u2192 {run.end}, timeframe={run.timeframe})"
            )

        features = FeaturePipeline().compute(df)
        close_series = df["close"].reindex(features.index)

        cash: float = run.initial_cash
        shares: float = 0.0
        factor = (run.fees_bps + run.slippage_bps) / 10_000.0
        equity_curve: List[float] = []
        trade_log: List[Trade] = []

        rows = list(features.iterrows())
        last_idx = len(rows) - 1

        for bar_num, (idx, row) in enumerate(rows):
            close = float(close_series[idx])
            signal = strategy.generate_signal(row)

            if signal == Signal.BUY and shares == 0.0:
                effective_price = close * (1.0 + factor)
                new_shares = math.floor(cash / effective_price)
                if new_shares > 0:
                    outflow = new_shares * effective_price
                    cash -= outflow
                    shares = float(new_shares)
                    trade_log.append(Trade(
                        date=str(idx.date()),
                        side="BUY",
                        price=effective_price,
                        shares=shares,
                        cash_flow=-outflow,
                        fees=shares * close * factor,
                        cash_after=cash,
                    ))

            elif signal == Signal.SELL and shares > 0.0:
                effective_price = close * (1.0 - factor)
                proceeds = shares * effective_price
                trade_log.append(Trade(
                    date=str(idx.date()),
                    side="SELL",
                    price=effective_price,
                    shares=shares,
                    cash_flow=proceeds,
                    fees=shares * close * factor,
                    cash_after=cash + proceeds,
                ))
                cash += proceeds
                shares = 0.0

            # Force-close on the final bar if a position is still open.
            # This runs after the signal branch so a SELL signal on the
            # final bar is handled normally (shares == 0.0 here → no-op).
            if bar_num == last_idx and shares > 0.0:
                effective_price = close * (1.0 - factor)
                proceeds = shares * effective_price
                trade_log.append(Trade(
                    date=str(idx.date()),
                    side="SELL",
                    price=effective_price,
                    shares=shares,
                    cash_flow=proceeds,
                    fees=shares * close * factor,
                    cash_after=cash + proceeds,
                ))
                cash += proceeds
                shares = 0.0

            equity_curve.append(cash + shares * close)

        self._last_result = SimulationResult(
            equity_curve=equity_curve,
            trade_log=trade_log,
        )

        return self._compute_metrics(run, equity_curve, trade_log)

    def _compute_metrics(
        self,
        run: BacktestRun,
        equity_curve: List[float],
        trade_log: List[Trade],
    ) -> BacktestMetrics:
        """Derive BacktestMetrics from the completed simulation output."""
        initial_cash = run.initial_cash
        final_equity = equity_curve[-1] if equity_curve else initial_cash

        # Total return
        total_return = (final_equity - initial_cash) / initial_cash

        # CAGR
        start_d = date.fromisoformat(run.start)
        end_d = date.fromisoformat(run.end)
        calendar_days = (end_d - start_d).days
        if calendar_days > 0 and final_equity > 0 and initial_cash > 0:
            cagr = (final_equity / initial_cash) ** (365.0 / calendar_days) - 1.0
        else:
            cagr = 0.0

        # Sharpe ratio (annualised, population std)
        sharpe_ratio = 0.0
        if len(equity_curve) > 1:
            daily_returns = [
                (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                for i in range(1, len(equity_curve))
                if equity_curve[i - 1] != 0.0
            ]
            n = len(daily_returns)
            if n > 1:
                mean_r = sum(daily_returns) / n
                variance = sum((r - mean_r) ** 2 for r in daily_returns) / n
                std_r = variance ** 0.5
                if std_r > 0.0:
                    sharpe_ratio = mean_r / std_r * (252 ** 0.5)

        # Max drawdown (most negative trough-from-peak; 0.0 if no drawdown)
        max_drawdown = 0.0
        if equity_curve:
            peak = equity_curve[0]
            for v in equity_curve:
                if v > peak:
                    peak = v
                if peak > 0.0:
                    dd = (v - peak) / peak
                    if dd < max_drawdown:
                        max_drawdown = dd

        # Win rate: profitable round trips / total round trips
        buys = [t for t in trade_log if t.side == "BUY"]
        sells = [t for t in trade_log if t.side == "SELL"]
        round_trips = min(len(buys), len(sells))
        if round_trips > 0:
            profitable = sum(
                1 for b, s in zip(buys, sells) if s.cash_flow > abs(b.cash_flow)
            )
            win_rate = profitable / round_trips
        else:
            win_rate = 0.0

        return BacktestMetrics(
            backtest_id=run.backtest_id,
            total_return=total_return,
            cagr=cagr,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=len(buys),
        )
