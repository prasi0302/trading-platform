"""Shared test fixtures for Order Service tests."""

from datetime import datetime, timezone

import pytest

from trading_common import OrderRequest, PriceTick, DEFAULT_SYMBOLS


@pytest.fixture
def known_symbols() -> set[str]:
    return {s.ticker for s in DEFAULT_SYMBOLS}


@pytest.fixture
def sample_price() -> PriceTick:
    return PriceTick(
        symbol="AAPL",
        price=175.50,
        bid=175.45,
        ask=175.55,
        volume=1000,
        timestamp=datetime.now(timezone.utc),
    )


@pytest.fixture
def market_buy_request() -> OrderRequest:
    return OrderRequest(
        symbol="AAPL",
        type="market",
        side="buy",
        quantity=10,
        session_id="test-session-123",
    )


@pytest.fixture
def limit_buy_request() -> OrderRequest:
    return OrderRequest(
        symbol="AAPL",
        type="limit",
        side="buy",
        quantity=10,
        price=170.00,
        session_id="test-session-123",
    )


@pytest.fixture
def stop_loss_request() -> OrderRequest:
    return OrderRequest(
        symbol="AAPL",
        type="stop_loss",
        side="sell",
        quantity=5,
        price=160.00,
        session_id="test-session-123",
    )
