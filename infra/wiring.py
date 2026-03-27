from __future__ import annotations

import logging

from core.errors import StrategyNotReadyError
from infra.adapters.yfinance_market_data import YFinanceMarketData
from infra.registries.strategy_registry import StrategyRegistry
from infra.repositories.backtest_repository import BacktestRepository
from services.backtest_service import BacktestService
from services.strategy_service import StrategyService
from strategies.ml.goldsight import GoldSightStrategy

logger = logging.getLogger(__name__)

_shared_registry: StrategyRegistry | None = None


def _get_registry() -> StrategyRegistry:
    """Return the module-level shared StrategyRegistry, building it once.

    Attempts to register each known strategy. Strategies whose artifacts
    are missing are skipped with a warning so the application starts
    regardless of training state.
    """
    global _shared_registry
    if _shared_registry is None:
        _shared_registry = StrategyRegistry()
        try:
            _shared_registry.register(GoldSightStrategy())
        except StrategyNotReadyError:
            logger.warning("GoldSight artifact not found or unloadable; skipping registration")
    return _shared_registry


def build_strategy_service() -> StrategyService:
    """Wire and return a fully-configured StrategyService."""
    return StrategyService(_get_registry())


def build_backtest_service() -> BacktestService:
    """Wire and return a fully-configured BacktestService.

    Shares the same StrategyRegistry as build_strategy_service() so both
    services see identical strategy registrations.
    """
    return BacktestService(
        BacktestRepository(),
        _get_registry(),
        YFinanceMarketData(),
    )
