from __future__ import annotations

import pathlib

import joblib
import numpy as np
import pandas as pd

from core.domain.strategy import Signal, Strategy
from core.errors import StrategyNotReadyError
from data.feature_pipeline import FeaturePipeline

ARTIFACT_PATH = pathlib.Path(__file__).parent / "artifacts" / "goldsight_v1.pkl"

FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "ma_5",
    "ma_20",
    "ma_ratio",
    "rsi_14",
    "volatility_10",
    "volume_ratio",
]


class GoldSightStrategy(Strategy):
    """RandomForest strategy trained on gold futures (GC=F) daily data."""

    def __init__(self) -> None:
        try:
            self._model = joblib.load(ARTIFACT_PATH)
        except FileNotFoundError as exc:
            raise StrategyNotReadyError(
                f"GoldSight artifact not found at {ARTIFACT_PATH}"
            ) from exc
        except Exception as exc:
            raise StrategyNotReadyError(
                f"Failed to load GoldSight artifact: {exc}"
            ) from exc

    @property
    def strategy_id(self) -> str:
        """Unique identifier for this strategy."""
        return "goldsight_v1"

    @property
    def name(self) -> str:
        """Human-readable display name."""
        return "GoldSight v1"

    @property
    def supported_symbols(self) -> frozenset[str]:
        """GoldSight is trained on gold futures data only."""
        return frozenset({"GC=F"})

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute features by delegating to FeaturePipeline.

        Returns the 8-feature DataFrame that this strategy's
        RandomForest model expects.

        Args:
            df: Raw OHLCV DataFrame from MarketDataPort.fetch().

        Returns:
            DataFrame with columns: return_1d, return_5d, ma_5, ma_20,
            ma_ratio, rsi_14, volatility_10, volume_ratio.
        """
        return FeaturePipeline().compute(df)

    def generate_signal(self, features: pd.Series) -> Signal:
        """Generate a BUY or SELL signal from a pre-computed feature row.

        Args:
            features: A Series containing at least the 8 expected feature
                      columns defined in FEATURE_COLUMNS.

        Returns:
            Signal.BUY if the model predicts next-day close will be higher,
            Signal.SELL otherwise.
        """
        values = features[FEATURE_COLUMNS].to_numpy().reshape(1, -1)
        prediction = self._model.predict(values)[0]
        return Signal.BUY if prediction == 1 else Signal.SELL
