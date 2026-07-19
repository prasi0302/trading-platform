"""Shared test fixtures for Order Service tests.

The os.environ.setdefault below defends against ISS-005 (module-level
DATABASE_URL construction in app/config.py raises when DB_PASSWORD is
unset). Order's current tests happen not to import app.config, so the
defect is latent here — but any future test that does would fail at
collection time in CI. Unit tests never open a database connection.
"""

import os

os.environ.setdefault("DB_PASSWORD", "test")

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
