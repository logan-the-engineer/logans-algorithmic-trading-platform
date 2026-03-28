"""Unit tests for AlphaTraderStrategy.

All tests mock the artifact load; no .pth file is required on disk.
The QNetwork is replaced with a MagicMock whose forward() returns
controlled Q-values so signal logic can be tested in isolation.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import torch

from core.domain.strategy import Signal
from core.errors import StrategyNotReadyError


# ── Helpers ───────────────────────────────────────────────────────────────────

_FEATURE_NAMES = ["ret1", "ret5", "ma10_ratio", "ma20_ratio", "rsi14", "vol10"]


def _make_feature_series() -> pd.Series:
    return pd.Series(
        [0.001, 0.005, 1.01, 1.005, 0.55, 0.003],
        index=_FEATURE_NAMES,
        dtype=np.float32,
    )


def _make_strategy_with_qvalues(q_values: list[float]):
    """Return an AlphaTraderStrategy whose network always outputs the given Q-values."""
    mock_net = MagicMock()
    mock_output = torch.tensor([q_values])
    mock_net.return_value = mock_output

    dummy_state_dict = {}

    with patch("strategies.ml.alphatrader.torch.load", return_value=dummy_state_dict), \
         patch("strategies.ml.alphatrader.QNetwork", return_value=mock_net):
        from strategies.ml.alphatrader import AlphaTraderStrategy
        strategy = AlphaTraderStrategy()

    # Replace the net directly so the mock is used at inference time.
    strategy._net = mock_net
    return strategy


def _fill_buffer(strategy, n: int = 10) -> Signal:
    """Call generate_signal n times; return the last signal."""
    last = Signal.HOLD
    for _ in range(n):
        last = strategy.generate_signal(_make_feature_series())
    return last


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_artifact_missing_raises_strategy_not_ready_error():
    """StrategyNotReadyError is raised when torch.load raises FileNotFoundError."""
    with patch("strategies.ml.alphatrader.torch.load", side_effect=FileNotFoundError):
        from strategies.ml.alphatrader import AlphaTraderStrategy
        with pytest.raises(StrategyNotReadyError):
            AlphaTraderStrategy()


def test_buy_signal():
    """Q-values [0.0, 1.0, 0.0] (action=1) -> Signal.BUY on the 10th call."""
    strategy = _make_strategy_with_qvalues([0.0, 1.0, 0.0])
    result = _fill_buffer(strategy, n=10)
    assert result == Signal.BUY


def test_sell_signal():
    """Q-values [0.0, 0.0, 1.0] (action=2) -> Signal.SELL on the 10th call."""
    strategy = _make_strategy_with_qvalues([0.0, 0.0, 1.0])
    result = _fill_buffer(strategy, n=10)
    assert result == Signal.SELL


def test_hold_signal_argmax():
    """Q-values [1.0, 0.0, 0.0] (action=0) → Signal.HOLD on the 10th call."""
    strategy = _make_strategy_with_qvalues([1.0, 0.0, 0.0])
    result = _fill_buffer(strategy, n=10)
    assert result == Signal.HOLD


def test_buffer_warmup_returns_hold_for_first_nine_calls():
    """Calls 1–9 all return Signal.HOLD regardless of Q-values."""
    strategy = _make_strategy_with_qvalues([0.0, 1.0, 0.0])  # would BUY if buffer full
    for call_num in range(1, 10):
        result = strategy.generate_signal(_make_feature_series())
        assert result == Signal.HOLD, f"Expected HOLD on call {call_num}, got {result}"


def test_reset_clears_buffer_and_position():
    """After reset(), the next 9 calls return HOLD (buffer refilling)."""
    strategy = _make_strategy_with_qvalues([0.0, 1.0, 0.0])
    _fill_buffer(strategy, n=10)   # fill buffer; 10th call is BUY
    strategy.reset()

    for call_num in range(1, 10):
        result = strategy.generate_signal(_make_feature_series())
        assert result == Signal.HOLD, (
            f"Expected HOLD after reset on call {call_num}, got {result}"
        )


def test_position_flag_updates_on_buy_and_sell():
    """_position is 1 after a BUY signal and 0 after a SELL signal."""
    buy_strategy = _make_strategy_with_qvalues([0.0, 1.0, 0.0])
    _fill_buffer(buy_strategy, n=10)
    assert buy_strategy._position == 1

    sell_strategy = _make_strategy_with_qvalues([0.0, 0.0, 1.0])
    _fill_buffer(sell_strategy, n=10)
    assert sell_strategy._position == 0
