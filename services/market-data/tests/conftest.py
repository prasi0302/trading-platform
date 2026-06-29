"""Shared test fixtures for market data service tests."""

import pytest

from trading_common import SimulationConfig, Symbol


@pytest.fixture
def config() -> SimulationConfig:
    return SimulationConfig(tick_interval_ms=1000)


@pytest.fixture
def sample_symbol() -> Symbol:
    return Symbol(
        ticker="TEST",
        name="Test Corp",
        sector="Technology",
        initial_price=100.0,
        volatility=0.25,
        drift=0.08,
    )


@pytest.fixture
def all_symbols() -> list[Symbol]:
    from trading_common import DEFAULT_SYMBOLS
    return DEFAULT_SYMBOLS
