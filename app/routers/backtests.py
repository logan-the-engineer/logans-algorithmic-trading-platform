from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import (
    BacktestCreatedResponse,
    BacktestRequest,
    BacktestStatusResponse,
)
from app.security import require_auth
from core.domain.backtest import BacktestMetrics, BacktestStatus
from core.errors import UnsupportedSymbolError
from infra.wiring import build_backtest_service

_service = build_backtest_service()

router = APIRouter(dependencies=[Depends(require_auth)])

_NOT_FOUND = {"error": {"code": "NOT_FOUND", "message": "Backtest not found"}}


@router.post("/backtests", response_model=BacktestCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_backtest(req: BacktestRequest) -> BacktestCreatedResponse:
    try:
        run = _service.create(req)
    except UnsupportedSymbolError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    return BacktestCreatedResponse(backtest_id=run.backtest_id, status=run.status)


@router.get("/backtests/{backtest_id}", response_model=BacktestStatusResponse)
def get_backtest(backtest_id: str) -> BacktestStatusResponse:
    run = _service.get_by_id(backtest_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return BacktestStatusResponse(
        backtest_id=run.backtest_id,
        status=run.status,
        strategy_id=run.strategy_id,
        symbols=run.symbols,
        timeframe=run.timeframe,
        start=run.start,
        end=run.end,
        initial_cash=run.initial_cash,
        fees_bps=run.fees_bps,
        slippage_bps=run.slippage_bps,
        parameters=run.parameters,
    )


@router.get("/backtests/{backtest_id}/metrics", response_model=BacktestMetrics)
def get_backtest_metrics(backtest_id: str) -> BacktestMetrics:
    run = _service.get_by_id(backtest_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    if run.status in (BacktestStatus.QUEUED, BacktestStatus.RUNNING):
        raise HTTPException(status_code=202, detail="Backtest is not yet complete")
    if run.status == BacktestStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Backtest failed; no metrics available")
    metrics = _service.get_metrics(backtest_id)
    return metrics
