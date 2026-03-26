from __future__ import annotations

from core.domain.strategy import Strategy


class StrategyRegistry:
    """In-memory registry mapping strategy IDs to Strategy instances."""

    def __init__(self) -> None:
        self._registry: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        """Register a strategy under its strategy_id."""
        self._registry[strategy.strategy_id] = strategy

    def get_by_id(self, strategy_id: str) -> Strategy | None:
        """Return a strategy by ID, or None if not registered."""
        return self._registry.get(strategy_id)

    def list_all(self) -> list[Strategy]:
        """Return all registered strategies."""
        return list(self._registry.values())
