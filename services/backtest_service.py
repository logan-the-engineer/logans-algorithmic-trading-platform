from __future__ import annotations

import uuid

from app.models import BacktestRequest
from core.domain.backtest import BacktestMetrics, BacktestRun
from infra.repositories.backtest_repository import BacktestRepository


class BacktestService:
    def __init__(self, repo: BacktestRepository) -> None:
        self._repo = repo

    def create(self, req: BacktestRequest) -> BacktestRun:
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
        return run

    def get_by_id(self, backtest_id: str) -> BacktestRun | None:
        return self._repo.find_by_id(backtest_id)

    def get_metrics(self, backtest_id: str) -> BacktestMetrics | None:
        run = self._repo.find_by_id(backtest_id)
        if run is None:
            return None
        return BacktestMetrics(
            backtest_id=backtest_id,
            total_return=0.0,
            cagr=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            num_trades=0,
        )
