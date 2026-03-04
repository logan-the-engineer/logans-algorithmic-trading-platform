from __future__ import annotations

from fastapi import APIRouter, Depends, status
from app.models import BacktestRequest, BacktestCreatedResponse
from app.security import require_auth
import uuid

router = APIRouter(dependencies=[Depends(require_auth)])

@router.post("/backtests", response_model=BacktestCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_backtest(req: BacktestRequest) -> BacktestCreatedResponse:
    return BacktestCreatedResponse(backtest_id=str(uuid.uuid4()), status="queued")
