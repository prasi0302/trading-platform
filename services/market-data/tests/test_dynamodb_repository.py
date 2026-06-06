"""Tests for DynamoDB repository."""

from datetime import datetime, timezone

import pytest

from trading_common import PriceTick
from app.repository.dynamodb_repository import DynamoDBRepository, BATCH_SIZE


class TestDynamoDBRepository:
    """Test suite for DynamoDBRepository."""

    @pytest.fixture
    def repo(self):
        return DynamoDBRepository(
            table_name="test-ticks",
            region="us-east-1",
            endpoint_url="http://localhost:4566",
        )

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
    async def test_buffer_tick(self, repo, sample_tick):
        """Tick should be buffered without immediate write."""
        await repo.put_tick(sample_tick)
        assert len(repo._buffer) == 1

    @pytest.mark.asyncio
    async def test_buffer_accumulates(self, repo, sample_tick):
        """Buffer should accumulate ticks until batch size."""
        for i in range(BATCH_SIZE - 1):
            await repo.put_tick(sample_tick)
        assert len(repo._buffer) == BATCH_SIZE - 1

    @pytest.mark.asyncio
    async def test_flush_empty_buffer(self, repo):
        """Flush with empty buffer should be a no-op."""
        await repo.flush()  # Should not raise
