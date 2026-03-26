from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.feature_pipeline import FeaturePipeline

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


@pytest.fixture
def ohlcv_df() -> pd.DataFrame:
    """25-row synthetic OHLCV DataFrame with plausible gold-futures prices."""
    n = 25
    rng = np.random.default_rng(42)
    close = 1800.0 + np.cumsum(rng.uniform(-5, 5, size=n))
    return pd.DataFrame(
        {
            "open": close - rng.uniform(0, 2, size=n),
            "high": close + rng.uniform(0, 3, size=n),
            "low": close - rng.uniform(0, 3, size=n),
            "close": close,
            "volume": rng.integers(80_000, 120_000, size=n).astype(float),
        }
    )


def test_output_has_exactly_8_columns(ohlcv_df: pd.DataFrame) -> None:
    result = FeaturePipeline().compute(ohlcv_df)
    assert set(result.columns) == set(FEATURE_COLUMNS)
    assert len(result.columns) == 8


def test_no_nan_in_output(ohlcv_df: pd.DataFrame) -> None:
    result = FeaturePipeline().compute(ohlcv_df)
    assert result.isna().sum().sum() == 0


def test_output_row_count_less_than_input(ohlcv_df: pd.DataFrame) -> None:
    result = FeaturePipeline().compute(ohlcv_df)
    assert len(result) < len(ohlcv_df)


def test_ma_ratio_equals_ma5_over_ma20(ohlcv_df: pd.DataFrame) -> None:
    result = FeaturePipeline().compute(ohlcv_df)
    last = result.iloc[-1]
    assert last["ma_ratio"] == pytest.approx(last["ma_5"] / last["ma_20"])
