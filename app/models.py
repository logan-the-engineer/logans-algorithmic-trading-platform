from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Timeframe = Literal["1m", "5m", "1h", "1d"]

class HealthResponse(BaseModel):
    status: str
    time: str

class VersionResponse(BaseModel):
    name: str
    version: str
    commit: Optional[str] = None

class ConfigResponse(BaseModel):
    environment: str
    mode: Literal["paper", "live"]
    risk_profile_id: Optional[str] = None
    features: Dict[str, bool]

class ControlRequest(BaseModel):
    reason: str

class ControlResponse(BaseModel):
    halted: bool
    time: str

class Symbol(BaseModel):
    symbol: str
    asset_class: Literal["equity", "crypto"]
    exchange: Optional[str] = None

class SymbolsResponse(BaseModel):
    symbols: List[Symbol]

class Bar(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class BarsResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    bars: List[Bar]

class BackfillRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1)
    timeframe: Timeframe
    start: str
    end: str
    source: str

class JobEnqueuedResponse(BaseModel):
    job_id: str
    status: Literal["queued"]

class FeatureComputeRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1)
    timeframe: Timeframe
    start: str
    end: str
    feature_set: str

class FeatureRow(BaseModel):
    ts: str
    model_config = {"extra": "allow"}

class FeaturesResponse(BaseModel):
    symbol: str
    timeframe: Timeframe
    feature_set: str
    rows: List[FeatureRow]

class StrategyMeta(BaseModel):
    strategy_id: str
    name: str
    type: Literal["rules", "ml"]

class StrategiesResponse(BaseModel):
    strategies: List[StrategyMeta]

class StrategyParamSpec(BaseModel):
    type: Literal["int", "float", "string", "bool"]
    min: Optional[float] = None
    max: Optional[float] = None
    default: Optional[Any] = None

class StrategyDetail(StrategyMeta):
    parameters_schema: Dict[str, StrategyParamSpec]

class BacktestRequest(BaseModel):
    strategy_id: str
    symbols: List[str] = Field(..., min_length=1)
    timeframe: Timeframe
    start: str
    end: str
    initial_cash: float = Field(..., ge=0)
    fees_bps: float = Field(..., ge=0)
    slippage_bps: float = Field(..., ge=0)
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BacktestCreatedResponse(BaseModel):
    backtest_id: str
    status: Literal["queued", "running", "finished", "failed"]

class RunRequest(BaseModel):
    mode: Literal["paper", "live"]
    strategy_id: str
    symbols: List[str] = Field(..., min_length=1)
    timeframe: Timeframe
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_profile_id: str

class RunCreatedResponse(BaseModel):
    run_id: str
    status: Literal["running"]

class OrderRequest(BaseModel):
    run_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    qty: float = Field(..., ge=0)
    type: Literal["market", "limit"]
    limit_price: Optional[float] = None
    time_in_force: Literal["day", "gtc"] = "day"

class OrderCreatedResponse(BaseModel):
    order_id: str
    status: Literal["submitted", "accepted", "rejected"]
    broker_order_id: Optional[str] = None

class Event(BaseModel):
    ts: str
    level: Literal["info", "warn", "error"]
    type: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)

class EventsResponse(BaseModel):
    events: List[Event]

class MetricsSummaryResponse(BaseModel):
    system: Dict[str, Any]
    trading: Dict[str, Any]
