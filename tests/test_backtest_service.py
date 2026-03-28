"""Unit tests for BacktestService.create() symbol validation."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models import BacktestRequest
from core.errors import UnsupportedSymbolError
from services.backtest_service import BacktestService


def _make_request(**overrides) -> BacktestRequest:
    defaults = dict(
        strategy_id="goldsight_v1",
        symbols=["AAPL"],
        timeframe="1d",
        start="2020-01-01",
        end="2021-01-01",
        initial_cash=10_000.0,
        fees_bps=0.0,
        slippage_bps=0.0,
        parameters={},
    )
    defaults.update(overrides)
    return BacktestRequest(**defaults)


def test_create_raises_unsupported_symbol_error():
    """BacktestService.create() raises UnsupportedSymbolError when the strategy
    does not support the requested symbol."""
    mock_strategy = MagicMock()
    mock_strategy.supported_symbols = frozenset({"GC=F"})

    mock_registry = MagicMock()
    mock_registry.get_by_id.return_value = mock_strategy

    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = None

    mock_market_data = MagicMock()

    service = BacktestService(
        repo=mock_repo,
        strategy_registry=mock_registry,
        market_data=mock_market_data,
    )

    with pytest.raises(UnsupportedSymbolError, match="AAPL"):
        service.create(_make_request(symbols=["AAPL"]))
