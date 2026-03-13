from __future__ import annotations

import enum
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class BacktestStatus(str, enum.Enum):
    QUEUED   = "queued"
    RUNNING  = "running"
    FINISHED = "finished"
    FAILED   = "failed"


class BacktestRun(BaseModel):
    backtest_id:  str
    strategy_id:  str
    symbols:      List[str]
    timeframe:    str
    start:        str
    end:          str
    initial_cash: float
    fees_bps:     float
    slippage_bps: float
    parameters:   dict
    status:       BacktestStatus = BacktestStatus.QUEUED
    created_at:   datetime = Field(default_factory=datetime.utcnow)

    def is_finished(self) -> bool:
        return self.status in (BacktestStatus.FINISHED, BacktestStatus.FAILED)


class BacktestMetrics(BaseModel):
    backtest_id:  str
    total_return: float
    cagr:         float
    sharpe_ratio: float # internal name; mapped to "sharpe" in HTTP response
    max_drawdown: float
    win_rate:     float
    num_trades:   int
