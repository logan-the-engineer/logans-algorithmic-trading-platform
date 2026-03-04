from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from app.models import BarsResponse, BackfillRequest, JobEnqueuedResponse
from app.security import require_auth
import uuid

router = APIRouter(dependencies=[Depends(require_auth)])

@router.get("/marketdata/bars", response_model=BarsResponse)
def get_bars(symbol: str = Query(...), timeframe: str = Query(...), start: str = Query(...), end: str = Query(...), limit: int = Query(500, ge=1, le=10000)) -> BarsResponse:
    return BarsResponse(symbol=symbol, timeframe=timeframe, bars=[])

@router.post("/marketdata/backfill", response_model=JobEnqueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def backfill(req: BackfillRequest) -> JobEnqueuedResponse:
    return JobEnqueuedResponse(job_id=str(uuid.uuid4()), status="queued")
