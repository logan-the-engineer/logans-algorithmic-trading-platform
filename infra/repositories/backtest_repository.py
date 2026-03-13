from __future__ import annotations

from core.domain.backtest import BacktestRun


class BacktestRepository:
    def __init__(self) -> None:
        self._store: dict[str, BacktestRun] = {}

    def save(self, run: BacktestRun) -> None:
        self._store[run.backtest_id] = run

    def find_by_id(self, backtest_id: str) -> BacktestRun | None:
        return self._store.get(backtest_id)
