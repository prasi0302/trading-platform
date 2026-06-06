"""Tests for REST API routes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from trading_common import DEFAULT_SYMBOLS, PriceTick, SimulationConfig, Symbol
from app.core.candle_aggregator import CandleAggregator
from app.core.market_hours import MarketHoursManager


class MockAppState:
    """Mock application state for testing."""

    def __init__(self):
        self.symbols = DEFAULT_SYMBOLS
        self.symbol_map = {s.ticker: s for s in DEFAULT_SYMBOLS}
        self.config = SimulationConfig()
        self.market_hours = MarketHoursManager(self.config)
        self.candle_aggregator = CandleAggregator(self.config)
        self.price_cache = {
            "AAPL": PriceTick(
                symbol="AAPL",
                price=175.50,
                bid=175.45,
                ask=175.55,
                volume=1000,
                timestamp=datetime.now(timezone.utc),
            )
        }


@pytest.fixture
def client():
    """Create test client with mock state."""
    from fastapi import FastAPI
    from app.api.routes import create_router
    from app.api.health import create_health_router

    mock_state = MockAppState()
    mock_state.redis_publisher = MagicMock()
    mock_state.redis_publisher.health_check = AsyncMock(return_value=True)
    mock_state.simulation_engine = MagicMock()
    mock_state.simulation_engine.is_running = True

    test_app = FastAPI()
    test_app.include_router(create_router(mock_state))
    test_app.include_router(create_health_router(mock_state))

    return TestClient(test_app)


class TestSymbolsEndpoint:
    """Tests for GET /api/symbols."""

    def test_list_symbols(self, client):
        response = client.get("/api/symbols")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 8
        assert data[0]["ticker"] == "AAPL"

    def test_symbols_have_required_fields(self, client):
        response = client.get("/api/symbols")
        data = response.json()
        for symbol in data:
            assert "ticker" in symbol
            assert "name" in symbol
            assert "sector" in symbol


class TestPriceEndpoint:
    """Tests for GET /api/symbols/{symbol}/price."""

    def test_get_price_existing_symbol(self, client):
        response = client.get("/api/symbols/AAPL/price")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 175.50

    def test_get_price_unknown_symbol(self, client):
        response = client.get("/api/symbols/UNKNOWN/price")
        assert response.status_code == 404

    def test_get_price_case_insensitive(self, client):
        response = client.get("/api/symbols/aapl/price")
        assert response.status_code == 200


class TestHistoryEndpoint:
    """Tests for GET /api/symbols/{symbol}/history."""

    def test_invalid_timeframe(self, client):
        response = client.get(
            "/api/symbols/AAPL/history",
            params={
                "timeframe": "invalid",
                "start": "2026-05-20T09:30:00Z",
                "end": "2026-05-20T10:00:00Z",
            },
        )
        assert response.status_code == 400

    def test_unknown_symbol(self, client):
        response = client.get(
            "/api/symbols/UNKNOWN/history",
            params={
                "timeframe": "5m",
                "start": "2026-05-20T09:30:00Z",
                "end": "2026-05-20T10:00:00Z",
            },
        )
        assert response.status_code == 404

    def test_start_after_end(self, client):
        response = client.get(
            "/api/symbols/AAPL/history",
            params={
                "timeframe": "5m",
                "start": "2026-05-20T16:00:00Z",
                "end": "2026-05-20T09:30:00Z",
            },
        )
        assert response.status_code == 400


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "market-data"
        assert "status" in data
        assert "dependencies" in data
