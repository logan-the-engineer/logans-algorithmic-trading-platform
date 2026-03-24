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
├── openapi.yaml                        # OpenAPI 3.0 spec - source of truth for all endpoint shapes
├── requirements.txt                    # fastapi, uvicorn, pydantic, python-dotenv
│
├── app/
│   ├── main.py                         # App entry point; registers all routers under /api/v1
│   ├── models.py                       # Pydantic request/response models for all resources
│   ├── security.py                     # Bearer token auth stub (presence check only)
│   ├── util.py                         # now_iso() UTC timestamp helper
│   └── routers/
│       ├── backtests.py                # IMPLEMENTED: POST /backtests, GET /backtests/{id}, GET /backtests/{id}/metrics
│       ├── strategies.py               # Stub
│       ├── marketdata.py               # Stub
│       ├── symbols.py                  # Stub
│       ├── features.py                 # Stub
│       ├── runs.py                     # Stub
│       ├── orders.py                   # Stub
│       ├── observability.py            # Stub
│       ├── control.py                  # Stub
│       └── system.py                   # Stub
│
├── core/domain/
│   └── backtest.py                     # BacktestStatus, BacktestRun, BacktestMetrics
│
├── services/
│   └── backtest_service.py             # BacktestService: create, get_by_id, get_metrics
│
├── infra/repositories/
│   └── backtest_repository.py          # In-memory dict store: save(), find_by_id()
│
└── tests/
    └── test_backtests.py               # pytest integration tests (6 tests, happy path + error cases)
```

---

## Implemented Endpoints

All endpoints require a `Bearer` token in the `Authorization` header. Authentication is stubbed; any non-empty token is accepted (e.g., `Authorization: Bearer dev`).

### `POST /api/v1/backtests`
Submit a backtest run. Accepts a strategy ID, symbols, timeframe, date range, initial capital, fees, slippage, and optional strategy parameters. Returns a UUID and `status: queued`.

**Request body**git checkout maing
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
  "status": "queued"
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
Retrieve performance metrics for a completed backtest. Returns placeholder values until the backtesting engine is implemented. Returns 404 for unknown IDs.

**Response - 200 OK**
```json
{
  "backtest_id": "3fa85f64-...",
  "total_return": 0.0,
  "cagr": 0.0,
  "sharpe_ratio": 0.0,
  "max_drawdown": 0.0,
  "win_rate": 0.0,
  "num_trades": 0
}
```

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

Six tests cover all three backtest endpoints: two tests for `POST /backtests`, two for `GET /backtests/{id}`, and two for `GET /backtests/{id}/metrics`. Each test is self-contained; POST-then-GET tests create their own backtest rather than relying on shared state.

---

## Roadmap

- [ ] Implement backtesting simulation loop and real metrics output
- [ ] Integrate ML/RL strategy engine (Random Forest, DQN)
- [ ] Swap in-memory repository for PostgreSQL + TimescaleDB adapter
- [ ] Implement remaining resource endpoints (strategies, market data, runs, orders)
- [ ] Full JWT authentication
- [ ] Broker integration (paper and live trading)
