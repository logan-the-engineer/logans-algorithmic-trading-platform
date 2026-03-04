from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from app.models import EventsResponse, Event, MetricsSummaryResponse
from app.security import require_auth
from app.util import now_iso

router = APIRouter(dependencies=[Depends(require_auth)])

@router.get("/events", response_model=EventsResponse)
def events(level: str | None = Query(default=None), run_id: str | None = Query(default=None), limit: int = Query(500, ge=1, le=10000)) -> EventsResponse:
    ev = [Event(ts=now_iso(), level="info", type="SYSTEM", message="skeleton running", context={"run_id": run_id})]
    if level:
        ev = [e for e in ev if e.level == level]
    return EventsResponse(events=ev[:limit])

@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def metrics() -> MetricsSummaryResponse:
    return MetricsSummaryResponse(system={"uptime_s": 0}, trading={"active_runs": 0, "halted": False})
