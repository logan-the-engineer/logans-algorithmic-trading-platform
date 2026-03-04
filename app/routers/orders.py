from __future__ import annotations

from fastapi import APIRouter, Depends, Header, status
from app.models import OrderRequest, OrderCreatedResponse
from app.security import require_auth
import uuid

router = APIRouter(dependencies=[Depends(require_auth)])

@router.post("/orders", response_model=OrderCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_order(req: OrderRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> OrderCreatedResponse:
    return OrderCreatedResponse(order_id=str(uuid.uuid4()), status="submitted", broker_order_id=None)
