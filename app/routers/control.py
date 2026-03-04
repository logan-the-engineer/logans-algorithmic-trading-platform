from __future__ import annotations

from fastapi import APIRouter, Depends
from app.models import ControlRequest, ControlResponse
from app.security import require_auth
from app.util import now_iso

router = APIRouter(dependencies=[Depends(require_auth)])
_halted = False

@router.post("/control/trading/halt", response_model=ControlResponse)
def halt(req: ControlRequest) -> ControlResponse:
    global _halted
    _halted = True
    return ControlResponse(halted=True, time=now_iso())

@router.post("/control/trading/resume", response_model=ControlResponse)
def resume(req: ControlRequest) -> ControlResponse:
    global _halted
    _halted = False
    return ControlResponse(halted=False, time=now_iso())
