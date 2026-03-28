class StrategyNotReadyError(Exception):
    """Raised when a strategy's model artifact is missing or cannot be loaded."""


class UnsupportedSymbolError(Exception):
    """Raised when a backtest requests a symbol the strategy does not support."""
