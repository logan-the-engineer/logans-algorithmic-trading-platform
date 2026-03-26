from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models import StrategiesResponse, StrategyDetail, StrategyMeta
from app.security import require_auth
from infra.wiring import build_strategy_service

router = APIRouter(dependencies=[Depends(require_auth)])

_service = build_strategy_service()

_NOT_FOUND = {"error": {"code": "NOT_FOUND", "message": "strategy not found"}}


@router.get("/strategies", response_model=StrategiesResponse)
def list_strategies() -> StrategiesResponse:
    """Return metadata for all registered strategies."""
    metas = [
        StrategyMeta(strategy_id=s.strategy_id, name=s.name, type="ml")
        for s in _service.list_strategies()
    ]
    return StrategiesResponse(strategies=metas)


@router.get("/strategies/{strategy_id}", response_model=StrategyDetail)
def get_strategy(strategy_id: str) -> StrategyDetail:
    """Return full detail for a single strategy, or 404 if not registered."""
    s = _service.get_by_id(strategy_id)
    if s is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND
        )
    return StrategyDetail(
        strategy_id=s.strategy_id,
        name=s.name,
        type="ml",
        parameters_schema={},
    )
