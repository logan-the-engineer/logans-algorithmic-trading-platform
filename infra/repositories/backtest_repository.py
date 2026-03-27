from __future__ import annotations

from core.domain.backtest import BacktestMetrics, BacktestRun


class BacktestRepository:
    def __init__(self) -> None:
        self._store: dict[str, BacktestRun] = {}
        self._metrics_store: dict[str, BacktestMetrics] = {}

    def save(self, run: BacktestRun) -> None:
        self._store[run.backtest_id] = run

    def find_by_id(self, backtest_id: str) -> BacktestRun | None:
        return self._store.get(backtest_id)

    def save_metrics(self, metrics: BacktestMetrics) -> None:
        """Persist metrics for a completed backtest run."""
        self._metrics_store[metrics.backtest_id] = metrics

    def find_metrics_by_id(self, backtest_id: str) -> BacktestMetrics | None:
        """Return stored metrics for the given backtest ID, or None if absent."""
        return self._metrics_store.get(backtest_id)
