from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class MarketDataPort(ABC):
    """Port (interface) for market data retrieval.

    Implementors must return a DataFrame with lowercase columns
    [open, high, low, close, volume] and a DatetimeIndex sorted ascending.
    """

    @abstractmethod
    def fetch(self, symbol: str, start: str, end: str, timeframe: str) -> pd.DataFrame:
        """Fetch OHLCV price data for a single symbol.

        Args:
            symbol:    Ticker symbol (e.g. "GC=F", "AAPL").
            start:     Start date in ISO format (e.g. "2022-01-01").
            end:       End date in ISO format, exclusive (e.g. "2023-01-01").
            timeframe: Bar interval — one of "1d", "1h", "5m", "1m".

        Returns:
            DataFrame with columns [open, high, low, close, volume],
            a DatetimeIndex sorted ascending.
        """
