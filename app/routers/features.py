from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from app.models import FeatureComputeRequest, JobEnqueuedResponse, FeaturesResponse
from app.security import require_auth
import uuid

router = APIRouter(dependencies=[Depends(require_auth)])

@router.post("/features/compute", response_model=JobEnqueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def compute(req: FeatureComputeRequest) -> JobEnqueuedResponse:
    return JobEnqueuedResponse(job_id=str(uuid.uuid4()), status="queued")

@router.get("/features", response_model=FeaturesResponse)
def get_features(symbol: str = Query(...), timeframe: str = Query(...), start: str = Query(...), end: str = Query(...), feature_set: str = Query("basic_v1")) -> FeaturesResponse:
    return FeaturesResponse(symbol=symbol, timeframe=timeframe, feature_set=feature_set, rows=[])
