# Algorithmic Trading Platform

A modular algorithmic trading research and execution platform built with Python and FastAPI. The project follows a strict layered monolith architecture designed to grow toward a live-trading system while serving as a demonstrable engineering portfolio piece.

---

## Architecture

The codebase is organized into four layers. Each layer depends only on the one directly below it (e.g., routers never touch `infra/`, services never touch `app/`).

```
app/routers/   ->  HTTP boundary (FastAPI route handlers)
services/      ->  Use-case orchestration (business logic)
core/          ->  Domain types and interfaces (no framework dependencies)
infra/         ->  Adapters (repositories, external integrations)
```

---

## Project Status

The backtesting vertical slice is fully implemented end-to-end: domain models, repository, service, HTTP handlers, and pytest suite. All other resource endpoints exist as intentional stubs, shaped by the OpenAPI spec, and ready for implementation in future sprints.

---

## File Structure

```
logans-algorithmic-trading-platform/
├── openapi.yaml                              # OpenAPI 3.0 spec - source of truth for all endpoint shapes
├── requirements.txt                          # fastapi, uvicorn, pydantic, pandas, numpy, scikit-learn, torch, joblib, yfinance
│
├── app/
│   ├── main.py                               # App entry point; registers all routers under /api/v1
│   ├── models.py                             # Pydantic request/response models for all resources
│   ├── security.py                           # Bearer token auth stub (presence check only)
│   ├── util.py                               # now_iso() UTC timestamp helper
│   └── routers/
│       ├── backtests.py                      # IMPLEMENTED: POST /backtests, GET /backtests/{id}, GET /backtests/{id}/metrics
│       ├── strategies.py                     # IMPLEMENTED: GET /strategies, GET /strategies/{id}
│       ├── marketdata.py                     # Stub
│       ├── symbols.py                        # Stub
│       ├── features.py                       # Stub
│       ├── runs.py                           # Stub
│       ├── orders.py                         # Stub
│       ├── observability.py                  # Stub
│       ├── control.py                        # Stub
│       └── system.py                         # Stub
│
├── core/
│   ├── errors.py                             # StrategyNotReadyError, UnsupportedSymbolError
│   ├── domain/
│   │   ├── backtest.py                       # BacktestStatus, BacktestRun, BacktestMetrics
│   │   └── strategy.py                       # Signal enum, Strategy ABC
│   ├── engine/
│   │   └── backtest_engine.py                # BacktestEngine: bar-by-bar simulation loop
│   └── ports/
│       └── market_data.py                    # MarketDataPort ABC: data ingestion contract
│
├── services/
│   ├── backtest_service.py                   # BacktestService: create (runs simulation), get_by_id, get_metrics
│   └── strategy_service.py                   # StrategyService: list_strategies, get_by_id
│
├── infra/
│   ├── wiring.py                             # Dependency wiring; builds and shares StrategyRegistry
│   ├── adapters/
│   │   └── yfinance_market_data.py           # MarketDataPort impl using yfinance
│   ├── registries/
│   │   └── strategy_registry.py             # In-memory strategy registry
│   └── repositories/
│       └── backtest_repository.py            # In-memory store: save(), find_by_id(), save_metrics()
│
├── data/
│   └── feature_pipeline.py                   # FeaturePipeline: 8 technical features from OHLCV
│
├── strategies/ml/
│   ├── goldsight.py                          # GoldSightStrategy: RandomForest on GC=F (gold futures)
│   ├── alphatrader.py                        # AlphaTraderStrategy: DQN on SPY; stateful 10-bar lookback
│   ├── train_goldsight.py                    # Standalone training script (not imported by app)
│   └── artifacts/
│       ├── goldsight_v1.pkl                  # Trained RandomForest model artifact
│       └── alphatrader_v1.pth                # Trained DQN model artifact (PyTorch state dict)
│
└── tests/
    ├── test_backtests.py                     # Integration tests for all three backtest endpoints
    ├── test_backtest_engine.py               # Unit tests for BacktestEngine (mock data, no network)
    ├── test_backtest_service.py              # Unit tests for BacktestService symbol validation
    ├── test_feature_pipeline.py              # Unit tests for FeaturePipeline
    ├── test_goldsight_strategy.py            # Unit tests for GoldSightStrategy
    ├── test_alphatrader_strategy.py          # Unit tests for AlphaTraderStrategy (mocked network)
    └── test_strategy_service.py             # Unit tests for StrategyService
```

---

## Implemented Endpoints

All endpoints require a `Bearer` token in the `Authorization` header. Authentication is stubbed; any non-empty token is accepted (e.g., `Authorization: Bearer dev`).

### `POST /api/v1/backtests`
Submit a backtest run. Accepts a strategy ID, symbols, timeframe, date range, initial capital, fees, slippage, and optional strategy parameters. Returns a UUID and `status: finished`.

**Request body**
```json
{
  "strategy_id": "sma_cross_v1",
  "symbols": ["AAPL"],
  "timeframe": "1d",
  "start": "2020-01-01",
  "end": "2023-01-01",
  "initial_cash": 10000.0,
  "fees_bps": 10.0,
  "slippage_bps": 5.0,
  "parameters": {}
}
```

**Response - 201 Created**
```json
{
  "backtest_id": "3fa85f64-...",
  "status": "finished"
}
```

---

### `GET /api/v1/backtests/{backtest_id}`
Retrieve the status and configuration of a backtest run by ID. Returns 404 for unknown IDs.

**Response - 200 OK**
```json
{
  "backtest_id": "3fa85f64-...",
  "status": "queued",
  "strategy_id": "sma_cross_v1",
  "symbols": ["AAPL"],
  "timeframe": "1d",
  "start": "2020-01-01",
  "end": "2023-01-01",
  "initial_cash": 10000.0,
  "fees_bps": 10.0,
  "slippage_bps": 5.0,
  "parameters": {}
}
```

---

### `GET /api/v1/backtests/{backtest_id}/metrics`
Retrieve simulation-derived performance metrics for a completed backtest. The endpoint gates on `BacktestStatus`: returns 200 with metrics for finished runs, 202 while the run is still in progress, and 422 if the run failed. Returns 404 for unknown IDs.

**Response - 200 OK**
```json
{
  "backtest_id": "3fa85f64-...",
  "total_return": 0.143,
  "cagr": 0.048,
  "sharpe_ratio": 0.87,
  "max_drawdown": -0.112,
  "win_rate": 0.54,
  "num_trades": 26
}
```

---

## Registered Strategies

| Strategy ID | Symbol | Model Type |
|---|---|---|
| `goldsight_v1` | `GC=F` | RandomForest |
| `alphatrader_v1` | `SPY` | DQN |

Strategies are queryable via `GET /api/v1/strategies` and `GET /api/v1/strategies/{strategy_id}`. Each strategy declares the symbols it supports; a backtest request with a mismatched symbol is rejected with a 422 before the simulation runs.

---

## Tech Stack

| Concern | Tool |
|---|---|
| Framework | FastAPI |
| Validation | Pydantic v2 |
| API spec | OpenAPI 3.0 (`openapi.yaml`) |
| Storage | In-memory (dict-based); PostgreSQL + TimescaleDB planned |
| Testing | pytest + FastAPI `TestClient` |
| Runtime | Python 3.11+, uvicorn |

---

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger UI is available at `http://localhost:8000/docs`.

---

## Running Tests

```bash
pytest tests/
```

36 tests across 7 files, all passing:

| File | Coverage |
|---|---|
| `test_backtests.py` | Integration tests for all three backtest endpoints |
| `test_backtest_engine.py` | Unit tests for BacktestEngine (mock market data, no network) |
| `test_backtest_service.py` | Unit tests for BacktestService symbol validation |
| `test_feature_pipeline.py` | Unit tests for FeaturePipeline |
| `test_goldsight_strategy.py` | Unit tests for GoldSightStrategy |
| `test_alphatrader_strategy.py` | Unit tests for AlphaTraderStrategy (mocked network, no filesystem) |
| `test_strategy_service.py` | Unit tests for StrategyService |

---

## Roadmap

- [x] Implement backtesting simulation loop and real metrics output
- [x] Integrate ML/RL strategy engine (RandomForest - GoldSight, DQN - AlphaTrader)
- [ ] Swap in-memory repository for PostgreSQL + TimescaleDB adapter
- [ ] Implement remaining resource endpoints (market data, runs, orders)
- [ ] Full JWT authentication
- [ ] Broker integration (paper and live trading)
