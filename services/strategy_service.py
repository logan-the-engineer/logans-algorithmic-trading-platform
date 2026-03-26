from __future__ import annotations

from core.domain.strategy import Strategy
from infra.registries.strategy_registry import StrategyRegistry


class StrategyService:
    """Orchestrates strategy look-up and listing via the StrategyRegistry."""

    def __init__(self, registry: StrategyRegistry) -> None:
        self._registry = registry

    def list_strategies(self) -> list[Strategy]:
        """Return all currently registered strategies."""
        return self._registry.list_all()

    def get_by_id(self, strategy_id: str) -> Strategy | None:
        """Return a strategy by ID, or None if not registered."""
        return self._registry.get_by_id(strategy_id)
