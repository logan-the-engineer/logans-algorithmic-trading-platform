from __future__ import annotations

import uuid

from app.models import BacktestRequest
from core.domain.backtest import BacktestMetrics, BacktestRun, BacktestStatus
from core.domain.strategy import Strategy
from core.engine.backtest_engine import BacktestEngine
from core.errors import UnsupportedSymbolError
from core.ports.market_data import MarketDataPort
from infra.registries.strategy_registry import StrategyRegistry
from infra.repositories.backtest_repository import BacktestRepository


class BacktestService:
    """Orchestrates backtest creation and results retrieval.

    On create(), the simulation runs synchronously so the run is FINISHED
    (or FAILED) by the time the call returns. get_metrics() is a pure
    repository lookup; it never triggers the engine.
    """

    def __init__(
        self,
        repo: BacktestRepository,
        strategy_registry: StrategyRegistry,
        market_data: MarketDataPort,
    ) -> None:
        """
        Args:
            repo:              In-memory store for runs and metrics.
            strategy_registry: Registry used to look up strategy instances.
            market_data:       Adapter used to fetch OHLCV price data.
        """
        self._repo = repo
        self._registry = strategy_registry
        self._market_data = market_data

    def create(self, req: BacktestRequest) -> BacktestRun:
        """Create and immediately execute a backtest run.

        Builds the BacktestRun record, looks up the strategy, runs the
        simulation synchronously via BacktestEngine, and persists the
        resulting metrics. Returns the run with status FINISHED on success
        or FAILED if the strategy was not found or the engine raised.

        Args:
            req: Validated BacktestRequest from the HTTP layer.

        Returns:
            BacktestRun with status FINISHED or FAILED.
        """
        run = BacktestRun(
            backtest_id=str(uuid.uuid4()),
            strategy_id=req.strategy_id,
            symbols=req.symbols,
            timeframe=req.timeframe,
            start=req.start,
            end=req.end,
            initial_cash=req.initial_cash,
            fees_bps=req.fees_bps,
            slippage_bps=req.slippage_bps,
            parameters=req.parameters,
        )
        self._repo.save(run)

        strategy: Strategy | None = self._registry.get_by_id(run.strategy_id)
        if strategy is None:
            run.status = BacktestStatus.FAILED
            self._repo.save(run)
            return run

        if run.symbols[0] not in strategy.supported_symbols:
            run.status = BacktestStatus.FAILED
            self._repo.save(run)
            raise UnsupportedSymbolError(
                f"Strategy '{run.strategy_id}' does not support symbol "
                f"'{run.symbols[0]}'. "
                f"Supported: {sorted(strategy.supported_symbols)}"
            )

        try:
            run.status = BacktestStatus.RUNNING
            self._repo.save(run)

            engine = BacktestEngine(self._market_data)
            metrics = engine.run(strategy, run)

            run.status = BacktestStatus.FINISHED
            self._repo.save(run)
            self._repo.save_metrics(metrics)
        except Exception:
            run.status = BacktestStatus.FAILED
            self._repo.save(run)
            raise

        return run

    def get_by_id(self, backtest_id: str) -> BacktestRun | None:
        """Return the BacktestRun for the given ID, or None if not found."""
        return self._repo.find_by_id(backtest_id)

    def get_metrics(self, backtest_id: str) -> BacktestMetrics | None:
        """Return stored metrics for the given backtest ID.

        This is a pure repository lookup; the simulation is never triggered
        here. Returns None if the run does not exist or metrics were never
        saved (e.g. the run failed before completing).

        Args:
            backtest_id: UUID string of the backtest run.

        Returns:
            BacktestMetrics if available, otherwise None.
        """
        run = self._repo.find_by_id(backtest_id)
        if run is None:
            return None
        return self._repo.find_metrics_by_id(backtest_id)
