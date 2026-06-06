"""Tests for the candle aggregator."""

from datetime import datetime, timezone

import pytest

from trading_common import SimulationConfig, Symbol, Timeframe
from app.core.candle_aggregator import CandleAggregator


class TestCandleAggregator:
    """Test suite for CandleAggregator."""

    @pytest.fixture
    def aggregator(self, config):
        return CandleAggregator(config)

    @pytest.fixture
    def symbol(self):
        return Symbol(
            ticker="TEST",
            name="Test Corp",
            sector="Technology",
            initial_price=100.0,
            volatility=0.25,
            drift=0.08,
        )

    def test_generates_candles(self, aggregator, symbol):
        """Should generate OHLCV candles for a valid time range."""
        start = datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc)
        end = datetime(2026, 5, 20, 10, 30, tzinfo=timezone.utc)

        candles = aggregator.generate_history(symbol, Timeframe.M5, start, end)

        assert len(candles) > 0
        for candle in candles:
            assert candle.symbol == "TEST"
            assert candle.timeframe == "5m"
            assert candle.high >= candle.low
            assert candle.high >= candle.open
            assert candle.high >= candle.close
            assert candle.low <= candle.open
            assert candle.low <= candle.close
            assert candle.volume > 0

    def test_deterministic_output(self, aggregator, symbol):
        """Same inputs should always produce the same candles."""
        start = datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc)
        end = datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc)

        candles_1 = aggregator.generate_history(symbol, Timeframe.M1, start, end)
        candles_2 = aggregator.generate_history(symbol, Timeframe.M1, start, end)

        assert len(candles_1) == len(candles_2)
        for c1, c2 in zip(candles_1, candles_2):
            assert c1.open == c2.open
            assert c1.high == c2.high
            assert c1.low == c2.low
            assert c1.close == c2.close

    def test_skips_non_market_hours(self, aggregator, symbol):
        """Should not generate candles outside market hours."""
        # Saturday
        start = datetime(2026, 5, 23, 9, 30, tzinfo=timezone.utc)
        end = datetime(2026, 5, 23, 16, 0, tzinfo=timezone.utc)

        candles = aggregator.generate_history(symbol, Timeframe.M5, start, end)
        assert len(candles) == 0

    def test_price_always_positive(self, aggregator, symbol):
        """All candle prices should be positive."""
        start = datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc)
        end = datetime(2026, 5, 20, 16, 0, tzinfo=timezone.utc)

        candles = aggregator.generate_history(symbol, Timeframe.M15, start, end)

        for candle in candles:
            assert candle.open > 0
            assert candle.high > 0
            assert candle.low > 0
            assert candle.close > 0
