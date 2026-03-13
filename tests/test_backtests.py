from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

_AUTH = {"Authorization": "Bearer test-token"}
_VALID_PAYLOAD = {
    "strategy_id": "sma_cross_v1",
    "symbols": ["AAPL"],
    "timeframe": "1d",
    "start": "2020-01-01",
    "end": "2023-01-01",
    "initial_cash": 10000.0,
    "fees_bps": 10.0,
    "slippage_bps": 5.0,
    "parameters": {},
}


def test_create_backtest_returns_201():
    r = client.post("/api/v1/backtests", json=_VALID_PAYLOAD, headers=_AUTH)
    assert r.status_code == 201
    data = r.json()
    assert "backtest_id" in data
    assert data["status"] == "queued"


def test_create_backtest_returns_backtest_id():
    r = client.post("/api/v1/backtests", json=_VALID_PAYLOAD, headers=_AUTH)
    assert r.status_code == 201
    assert r.json()["backtest_id"] != ""


def test_get_backtest_returns_200():
    create = client.post("/api/v1/backtests", json=_VALID_PAYLOAD, headers=_AUTH)
    backtest_id = create.json()["backtest_id"]
    r = client.get(f"/api/v1/backtests/{backtest_id}", headers=_AUTH)
    assert r.status_code == 200
    assert r.json()["strategy_id"] == "sma_cross_v1"


def test_get_backtest_not_found_returns_404():
    r = client.get("/api/v1/backtests/nonexistent-id", headers=_AUTH)
    assert r.status_code == 404


def test_get_metrics_returns_200():
    create = client.post("/api/v1/backtests", json=_VALID_PAYLOAD, headers=_AUTH)
    backtest_id = create.json()["backtest_id"]
    r = client.get(f"/api/v1/backtests/{backtest_id}/metrics", headers=_AUTH)
    assert r.status_code == 200
    data = r.json()
    assert "backtest_id" in data
    assert "total_return" in data
    assert "sharpe_ratio" in data


def test_get_metrics_not_found_returns_404():
    r = client.get("/api/v1/backtests/nonexistent-id/metrics", headers=_AUTH)
    assert r.status_code == 404
