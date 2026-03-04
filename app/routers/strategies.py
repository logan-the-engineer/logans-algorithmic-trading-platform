from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import StrategiesResponse, StrategyMeta, StrategyDetail, StrategyParamSpec
from app.security import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])

_STRATEGIES = {
    "sma_cross_v1": StrategyDetail(
        strategy_id="sma_cross_v1",
        name="SMA Crossover v1",
        type="rules",
        parameters_schema={
            "fast_window": StrategyParamSpec(type="int", min=2, max=50, default=10),
            "slow_window": StrategyParamSpec(type="int", min=10, max=200, default=50),
        },
    )
}

@router.get("/strategies", response_model=StrategiesResponse)
def list_strategies() -> StrategiesResponse:
    metas = [StrategyMeta(strategy_id=s.strategy_id, name=s.name, type=s.type) for s in _STRATEGIES.values()]
    return StrategiesResponse(strategies=metas)

@router.get("/strategies/{strategy_id}", response_model=StrategyDetail)
def get_strategy(strategy_id: str) -> StrategyDetail:
    s = _STRATEGIES.get(strategy_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": {"code": "NOT_FOUND", "message": "strategy not found"}})
    return s
