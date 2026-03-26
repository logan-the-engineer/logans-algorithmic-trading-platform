from __future__ import annotations

import pandas as pd


_FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "ma_5",
    "ma_20",
    "ma_ratio",
    "rsi_14",
    "volatility_10",
    "volume_ratio",
]


class FeaturePipeline:
    """Transforms raw OHLCV price data into a fixed set of technical features."""

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute technical features from a raw OHLCV DataFrame.

        Args:
            df: DataFrame with columns [open, high, low, close, volume].
                Index should be a DatetimeIndex sorted in ascending order.

        Returns:
            A new DataFrame containing exactly the 8 feature columns, with
            any rows that contain NaN values dropped.
        """
        out = df.copy()

        close = out["close"]
        volume = out["volume"]

        out["return_1d"] = close.pct_change(1)
        out["return_5d"] = close.pct_change(5)
        out["ma_5"] = close.rolling(5).mean()
        out["ma_20"] = close.rolling(20).mean()
        out["ma_ratio"] = out["ma_5"] / out["ma_20"]

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        out["rsi_14"] = 100 - (100 / (1 + avg_gain / avg_loss))

        out["volatility_10"] = out["return_1d"].rolling(10).std()
        out["volume_ratio"] = volume / volume.rolling(20).mean()

        return out[_FEATURE_COLUMNS].dropna()
