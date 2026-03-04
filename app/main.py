from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import system, control, symbols, marketdata, features, strategies, backtests, runs, orders, observability

API_PREFIX = "/api/v1"

app = FastAPI(
    title="Algorithmic Trading Platform API (Skeleton)",
    version="0.1.0",
    description="FastAPI skeleton matching the trading platform API shape.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix=API_PREFIX)
app.include_router(control.router, prefix=API_PREFIX)
app.include_router(symbols.router, prefix=API_PREFIX)
app.include_router(marketdata.router, prefix=API_PREFIX)
app.include_router(features.router, prefix=API_PREFIX)
app.include_router(strategies.router, prefix=API_PREFIX)
app.include_router(backtests.router, prefix=API_PREFIX)
app.include_router(runs.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(observability.router, prefix=API_PREFIX)
