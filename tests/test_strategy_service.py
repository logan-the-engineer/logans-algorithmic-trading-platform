from __future__ import annotations

from unittest.mock import MagicMock

from core.domain.strategy import Strategy
from infra.registries.strategy_registry import StrategyRegistry
from services.strategy_service import StrategyService


def _make_registry(*strategy_ids: str) -> StrategyRegistry:
    """Return a StrategyRegistry pre-populated with mock strategies."""
    registry = StrategyRegistry()
    for sid in strategy_ids:
        mock = MagicMock(spec=Strategy)
        mock.strategy_id = sid
        registry.register(mock)
    return registry


def test_list_strategies_returns_empty_list_when_registry_is_empty() -> None:
    """list_strategies returns an empty list when no strategies are registered."""
    service = StrategyService(StrategyRegistry())
    assert service.list_strategies() == []


def test_list_strategies_returns_list() -> None:
    """list_strategies always returns a list type."""
    service = StrategyService(StrategyRegistry())
    assert isinstance(service.list_strategies(), list)


def test_get_by_id_returns_none_for_unknown_strategy() -> None:
    """get_by_id returns None for an unregistered strategy ID."""
    service = StrategyService(StrategyRegistry())
    assert service.get_by_id("does_not_exist") is None


def test_get_by_id_returns_strategy_if_registered() -> None:
    """get_by_id returns the registered Strategy instance for a known ID."""
    service = StrategyService(_make_registry("goldsight_v1"))
    result = service.get_by_id("goldsight_v1")
    assert result is not None
    assert isinstance(result, Strategy)
