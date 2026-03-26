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

    @abstractmethod
    def generate_signal(self, features: pd.Series) -> Signal:
        """Generate a trading signal from a row of pre-computed features.

        Args:
            features: A Series whose index contains the feature column names
                      expected by this strategy.

        Returns:
            A Signal indicating the recommended action.
        """
