from __future__ import annotations

import enum
from abc import ABC, abstractmethod

import pandas as pd


class Signal(str, enum.Enum):
    """Trading signal produced by a strategy."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """Abstract base class for all trading strategies."""

    @property
    @abstractmethod
    def strategy_id(self) -> str:
        """Unique identifier for this strategy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name for this strategy."""

    @property
    @abstractmethod
    def supported_symbols(self) -> frozenset[str]:
        """The set of symbols this strategy is valid for.

        BacktestService validates the requested symbol against this set
        before running the simulation. Returning frozenset() means the
        strategy accepts no symbols and will always be rejected.
        """

    def reset(self) -> None:
        """Lifecycle hook called by BacktestEngine before each simulation run.

        Stateless strategies do not need to override this method. Stateful
        strategies (e.g., those maintaining a lookback buffer or position
        flag across bars) should override it to reinitialize that state.
        """

    @abstractmethod
    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute the features this strategy requires from raw OHLCV data.

        Called by BacktestEngine before the simulation loop. The returned
        DataFrame's rows are passed one at a time to generate_signal().
        Shape and column names are strategy-defined.

        Args:
            df: Raw OHLCV DataFrame as returned by MarketDataPort.fetch().
                Expected columns: open, high, low, close, volume.
                Index: DatetimeIndex sorted ascending.

        Returns:
            A DataFrame whose rows will be passed one at a time to
            generate_signal(). Shape and column names are strategy-defined.
        """

    @abstractmethod
    def generate_signal(self, features: pd.Series) -> Signal:
        """Generate a trading signal from a row of pre-computed features.

        Args:
            features: A Series whose index contains the feature column names
                      expected by this strategy.

        Returns:
            A Signal indicating the recommended action.
        """
