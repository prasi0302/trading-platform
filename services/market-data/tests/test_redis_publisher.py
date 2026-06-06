"""Tests for Redis publisher with graceful degradation."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from trading_common import PriceTick
from app.repository.redis_publisher import RedisPublisher, MAX_CONSECUTIVE_FAILURES


class TestRedisPublisher:
    """Test suite for RedisPublisher."""

    @pytest.fixture
    def publisher(self):
        return RedisPublisher("redis://localhost:6379")

    @pytest.fixture
    def sample_tick(self):
        return PriceTick(
            symbol="AAPL",
            price=175.50,
            bid=175.45,
            ask=175.55,
            volume=1000,
            timestamp=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_publish_returns_false_when_not_connected(self, publisher, sample_tick):
        """Should return False when no Redis connection."""
        result = await publisher.publish_tick(sample_tick)
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_returns_false_when_not_connected(self, publisher):
        """Health check should return False without connection."""
        result = await publisher.health_check()
        assert result is False

    def test_degraded_state_after_max_failures(self, publisher):
        """Publisher should enter degraded state after max consecutive failures."""
        publisher._consecutive_failures = MAX_CONSECUTIVE_FAILURES
        publisher._enter_degraded_state()
        assert publisher._is_degraded() is True
