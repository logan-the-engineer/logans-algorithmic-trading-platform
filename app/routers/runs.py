from __future__ import annotations

from fastapi import APIRouter, Depends, status
from app.models import RunRequest, RunCreatedResponse
from app.security import require_auth
import uuid

router = APIRouter(dependencies=[Depends(require_auth)])

@router.post("/runs", response_model=RunCreatedResponse, status_code=status.HTTP_201_CREATED)
def start_run(req: RunRequest) -> RunCreatedResponse:
    return RunCreatedResponse(run_id=str(uuid.uuid4()), status="running")
