from __future__ import annotations

import pandas as pd
import yfinance as yf

from core.ports.market_data import MarketDataPort


class YFinanceMarketData(MarketDataPort):
    """MarketDataPort adapter backed by the yfinance library.

    Downloads OHLCV data from Yahoo Finance, normalises column names to
    lowercase, and returns a DataFrame with an ascending DatetimeIndex.
    """

    _INTERVAL_MAP: dict[str, str] = {
        "1d": "1d",
        "1h": "1h",
        "5m": "5m",
        "1m": "1m",
    }

    def fetch(self, symbol: str, start: str, end: str, timeframe: str) -> pd.DataFrame:
        """Download OHLCV data from Yahoo Finance and return a clean DataFrame.

        Args:
            symbol:    Ticker symbol recognised by yfinance (e.g. "GC=F").
            start:     Start date in ISO format, inclusive (e.g. "2022-01-01").
            end:       End date in ISO format, exclusive (e.g. "2023-01-01").
            timeframe: Bar interval — one of "1d", "1h", "5m", "1m".

        Returns:
            DataFrame with lowercase columns [open, high, low, close, volume]
            and a DatetimeIndex sorted ascending.

        Raises:
            ValueError: If the downloaded DataFrame is empty (bad symbol,
                        date range outside trading history, etc.).
        """
        interval = self._INTERVAL_MAP[timeframe]
        df: pd.DataFrame = yf.download(
            symbol,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        # yfinance sometimes returns a MultiIndex for single-ticker downloads;
        # flatten to a plain Index before lowercasing.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = df.columns.str.lower()
        df.sort_index(ascending=True, inplace=True)

        if df.empty:
            raise ValueError(
                f"No data returned for {symbol} "
                f"({start} \u2192 {end}, interval={interval}). "
                "Check the symbol and date range."
            )

        return df
