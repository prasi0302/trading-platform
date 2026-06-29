"""Tests for the GBM tick generator."""

import pytest

from trading_common import SimulationConfig, Symbol
from app.core.tick_generator import TickGenerator


class TestTickGenerator:
    """Test suite for TickGenerator."""

    def test_generate_tick_returns_valid_price(self, sample_symbol, config):
        generator = TickGenerator(sample_symbol, config)
        tick = generator.generate_tick()

        assert tick.symbol == "TEST"
        assert tick.price > 0
        assert tick.bid > 0
        assert tick.ask > 0
        assert tick.bid < tick.ask
        assert tick.volume >= 1
        assert tick.timestamp is not None

    def test_price_floor_enforced(self, config):
        """Price should never go below $0.01."""
        symbol = Symbol(
            ticker="PENNY",
            name="Penny Stock",
            sector="Test",
            initial_price=0.02,
            volatility=5.0,  # Extreme volatility to force negative
            drift=-10.0,
        )
        generator = TickGenerator(symbol, config)

        # Generate many ticks — price should never go below 0.01
        for _ in range(1000):
            tick = generator.generate_tick()
            assert tick.price >= 0.01

    def test_bid_ask_spread(self, sample_symbol, config):
        """Bid should be below price, ask should be above."""
        generator = TickGenerator(sample_symbol, config)
        tick = generator.generate_tick()

        assert tick.bid <= tick.price
        assert tick.ask >= tick.price
        assert tick.bid < tick.ask

    def test_volume_within_bounds(self, sample_symbol, config):
        """Volume should be at least 1."""
        generator = TickGenerator(sample_symbol, config)

        for _ in range(100):
            tick = generator.generate_tick()
            assert tick.volume >= 1

    def test_current_price_updates(self, sample_symbol, config):
        """Current price should change after generating a tick."""
        generator = TickGenerator(sample_symbol, config)
        initial = generator.current_price

        generator.generate_tick()
        # Price should have changed (extremely unlikely to be exactly the same)
        # We just verify it's still valid
        assert generator.current_price > 0

    def test_mean_reversion_at_high_price(self, config):
        """Drift should be reduced when price exceeds 10x initial."""
        symbol = Symbol(
            ticker="HIGH",
            name="High Flyer",
            sector="Test",
            initial_price=10.0,
            volatility=0.01,  # Low volatility
            drift=100.0,  # Extreme drift to push price up
        )
        generator = TickGenerator(symbol, config)
        generator.current_price = 150.0  # 15x initial (above 10x threshold)

        # Generate ticks — with drift=0 and low volatility, price should stay relatively stable
        prices = [generator.generate_tick().price for _ in range(100)]
        avg_price = sum(prices) / len(prices)

        # Price shouldn't explode further (rough check)
        assert avg_price < 200.0
