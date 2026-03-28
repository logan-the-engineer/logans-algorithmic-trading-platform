"""
alphatrader.py - DQN-based trading strategy for SPY.

Wraps a pre-trained Deep Q-Network as a Strategy implementation.
The network architecture must match the training configuration exactly:
input_dim=61, hidden layers 128 and 64, action_dim=3.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from core.domain.strategy import Signal, Strategy
from core.errors import StrategyNotReadyError

ARTIFACT_PATH = pathlib.Path(__file__).parent / "artifacts" / "alphatrader_v1.pth"

LOOKBACK = 10
N_FEATURES = 6


class QNetwork(nn.Module):
    """Feedforward Q-network matching the AlphaTrader training architecture."""

    def __init__(self, input_dim: int, action_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return Q-values for each action given input state x."""
        return self.net(x)


class AlphaTraderStrategy(Strategy):
    """DQN-based strategy trained on SPY daily OHLCV data (2015-2022).

    Maintains a 10-bar lookback buffer and a position flag across calls to
    generate_signal(). Call reset() between simulation runs to clear this
    state.
    """

    def __init__(self) -> None:
        try:
            state_dict = torch.load(
                ARTIFACT_PATH, map_location="cpu", weights_only=True
            )
            self._net = QNetwork(input_dim=LOOKBACK * N_FEATURES + 1, action_dim=3)
            self._net.load_state_dict(state_dict)
            self._net.eval()
        except FileNotFoundError as exc:
            raise StrategyNotReadyError(
                f"AlphaTrader artifact not found at {ARTIFACT_PATH}"
            ) from exc
        except Exception as exc:
            raise StrategyNotReadyError(
                f"Failed to load AlphaTrader artifact: {exc}"
            ) from exc

        self._buffer: list[np.ndarray] = []
        self._position: int = 0

    @property
    def strategy_id(self) -> str:
        """Unique identifier for this strategy."""
        return "alphatrader_v1"

    @property
    def name(self) -> str:
        """Human-readable display name."""
        return "AlphaTrader v1"

    @property
    def supported_symbols(self) -> frozenset[str]:
        """AlphaTrader is trained on SPY daily data only."""
        return frozenset({"SPY"})

    def reset(self) -> None:
        """Clear the lookback buffer and reset the position flag.

        Must be called by BacktestEngine before each simulation run so that
        state from a previous run does not leak into the next.
        """
        self._buffer = []
        self._position = 0

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute the 6 per-bar features matching the training distribution.

        Args:
            df: Raw OHLCV DataFrame from MarketDataPort.fetch().
                Expected columns: open, high, low, close, volume.
                Index: DatetimeIndex sorted ascending.

        Returns:
            DataFrame with columns: ret1, ret5, ma10_ratio, ma20_ratio,
            rsi14, vol10. Rows with any NaN are dropped.
        """
        close = df["close"]
        period = 14

        ret1 = close.pct_change(1)
        ret5 = close.pct_change(5)
        ma10_ratio = close / close.rolling(10).mean()
        ma20_ratio = close / close.rolling(20).mean()

        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi14 = (100 - (100 / (1 + rs))) / 100.0
        rsi14 = rsi14.fillna(1.0)  # avg_loss == 0 → all gains → RSI = 100 → normalized 1.0

        vol10 = ret1.rolling(10).std()

        features = pd.DataFrame(
            {
                "ret1": ret1,
                "ret5": ret5,
                "ma10_ratio": ma10_ratio,
                "ma20_ratio": ma20_ratio,
                "rsi14": rsi14,
                "vol10": vol10,
            },
            index=df.index,
        )
        return features.dropna()

    def generate_signal(self, features: pd.Series) -> Signal:
        """Generate a trading signal from one feature row.

        Appends the row to the internal lookback buffer. Returns Signal.HOLD
        while the buffer is warming up (fewer than LOOKBACK bars). Once the
        buffer is full, assembles the 61-dimensional state vector (60 feature
        values + position flag) and queries the network.

        Args:
            features: A Series with columns ret1, ret5, ma10_ratio,
                      ma20_ratio, rsi14, vol10.

        Returns:
            Signal.BUY, Signal.SELL, or Signal.HOLD.
        """
        self._buffer.append(features.values.astype(np.float32))

        if len(self._buffer) < LOOKBACK:
            return Signal.HOLD

        self._buffer = self._buffer[-LOOKBACK:]

        window = np.array(self._buffer).flatten()   # shape (60,)
        state = np.concatenate([window, [float(self._position)]])  # shape (61,)

        with torch.no_grad():
            tensor = torch.FloatTensor(state).unsqueeze(0)
            action = int(self._net(tensor).argmax(dim=1).item())

        if action == 1:
            signal = Signal.BUY
            self._position = 1
        elif action == 2:
            signal = Signal.SELL
            self._position = 0
        else:
            signal = Signal.HOLD

        return signal
