from __future__ import annotations

import logging

from core.errors import StrategyNotReadyError
from infra.registries.strategy_registry import StrategyRegistry
from services.strategy_service import StrategyService
from strategies.ml.goldsight import GoldSightStrategy

logger = logging.getLogger(__name__)


def build_strategy_service() -> StrategyService:
    """Wire and return a fully-configured StrategyService.

    Attempts to register each known strategy. Strategies whose artifacts
    are missing are skipped with a warning so the application starts
    regardless of training state.
    """
    registry = StrategyRegistry()

    try:
        registry.register(GoldSightStrategy())
    except StrategyNotReadyError:
        logger.warning("GoldSight artifact not found or unloadable; skipping registration")

    return StrategyService(registry)
