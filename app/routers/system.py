from __future__ import annotations

from fastapi import APIRouter, Depends
from app.models import HealthResponse, VersionResponse, ConfigResponse
from app.security import require_auth
from app.util import now_iso

router = APIRouter()

@router.get("/health", response_model=HealthResponse, include_in_schema=True)
def health() -> HealthResponse:
    return HealthResponse(status="ok", time=now_iso())

@router.get("/version", response_model=VersionResponse, include_in_schema=True)
def version() -> VersionResponse:
    return VersionResponse(name="trading-platform", version="0.1.0", commit=None)

@router.get("/config", response_model=ConfigResponse, dependencies=[Depends(require_auth)])
def get_config() -> ConfigResponse:
    return ConfigResponse(environment="dev", mode="paper", risk_profile_id=None, features={"live_trading_enabled": False})
