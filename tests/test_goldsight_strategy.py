from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from core.domain.strategy import Signal
from core.errors import StrategyNotReadyError


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


def _make_feature_series() -> pd.Series:
    return pd.Series(
        [0.001, 0.003, 1820.0, 1815.0, 1.003, 52.0, 0.005, 1.1],
        index=FEATURE_COLUMNS,
    )


def test_raises_strategy_not_ready_when_artifact_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """StrategyNotReadyError is raised when the artifact path does not exist."""
    import strategies.ml.goldsight as goldsight_module

    monkeypatch.setattr(
        goldsight_module, "ARTIFACT_PATH", pathlib.Path("/nonexistent/goldsight_v1.pkl")
    )
    with pytest.raises(StrategyNotReadyError):
        from strategies.ml.goldsight import GoldSightStrategy
        GoldSightStrategy()


def test_generate_signal_returns_valid_signal() -> None:
    """generate_signal returns a Signal enum member when the model is mocked."""
    mock_model = MagicMock()
    mock_model.predict.return_value = [1]

    with patch("strategies.ml.goldsight.joblib.load", return_value=mock_model):
        from strategies.ml.goldsight import GoldSightStrategy
        strategy = GoldSightStrategy()

    result = strategy.generate_signal(_make_feature_series())

    assert isinstance(result, Signal)
    assert result == Signal.BUY


def test_generate_signal_sell_when_prediction_zero() -> None:
    """generate_signal returns Signal.SELL when the model predicts 0."""
    mock_model = MagicMock()
    mock_model.predict.return_value = [0]

    with patch("strategies.ml.goldsight.joblib.load", return_value=mock_model):
        from strategies.ml.goldsight import GoldSightStrategy
        strategy = GoldSightStrategy()

    result = strategy.generate_signal(_make_feature_series())

    assert result == Signal.SELL


def test_supported_symbols_is_gc_f() -> None:
    """GoldSightStrategy only accepts the GC=F symbol."""
    mock_model = MagicMock()

    with patch("strategies.ml.goldsight.joblib.load", return_value=mock_model):
        from strategies.ml.goldsight import GoldSightStrategy
        strategy = GoldSightStrategy()

    assert strategy.supported_symbols == frozenset({"GC=F"})
