from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from app.models import SymbolsResponse, Symbol
from app.security import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])

@router.get("/symbols", response_model=SymbolsResponse)
def list_symbols(asset_class: str | None = Query(default=None), search: str | None = Query(default=None)) -> SymbolsResponse:
    symbols = [
        Symbol(symbol="AAPL", asset_class="equity", exchange="NASDAQ"),
        Symbol(symbol="SPY", asset_class="equity", exchange="ARCA"),
    ]
    if asset_class:
        symbols = [s for s in symbols if s.asset_class == asset_class]
    if search:
        symbols = [s for s in symbols if search.upper() in s.symbol.upper()]
    return SymbolsResponse(symbols=symbols)
