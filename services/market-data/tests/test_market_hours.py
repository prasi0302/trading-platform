"""Tests for market hours management."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from trading_common import SimulationConfig
from app.core.market_hours import MarketHoursManager

ET = ZoneInfo("America/New_York")


class TestMarketHoursManager:
    """Test suite for MarketHoursManager."""

    @pytest.fixture
    def manager(self, config):
        return MarketHoursManager(config)

    def test_market_open_during_trading_hours(self, manager):
        """Market should be open during trading hours on a weekday."""
        # Wednesday at 10:00 AM ET
        dt = datetime(2026, 5, 20, 10, 0, tzinfo=ET)
        assert manager.is_market_open(dt) is True

    def test_market_closed_before_open(self, manager):
        """Market should be closed before 9:30 AM ET."""
        # Wednesday at 9:00 AM ET
        dt = datetime(2026, 5, 20, 9, 0, tzinfo=ET)
        assert manager.is_market_open(dt) is False

    def test_market_closed_after_close(self, manager):
        """Market should be closed after 4:00 PM ET."""
        # Wednesday at 4:01 PM ET
        dt = datetime(2026, 5, 20, 16, 1, tzinfo=ET)
        assert manager.is_market_open(dt) is False

    def test_market_closed_on_saturday(self, manager):
        """Market should be closed on Saturday."""
        # Saturday at 11:00 AM ET
        dt = datetime(2026, 5, 23, 11, 0, tzinfo=ET)
        assert manager.is_market_open(dt) is False

    def test_market_closed_on_sunday(self, manager):
        """Market should be closed on Sunday."""
        # Sunday at 11:00 AM ET
        dt = datetime(2026, 5, 24, 11, 0, tzinfo=ET)
        assert manager.is_market_open(dt) is False

    def test_market_open_at_exact_open_time(self, manager):
        """Market should be open at exactly 9:30 AM ET."""
        dt = datetime(2026, 5, 20, 9, 30, tzinfo=ET)
        assert manager.is_market_open(dt) is True

    def test_market_closed_at_exact_close_time(self, manager):
        """Market should be closed at exactly 4:00 PM ET (close is exclusive)."""
        dt = datetime(2026, 5, 20, 16, 0, tzinfo=ET)
        assert manager.is_market_open(dt) is False

    def test_get_status_when_open(self, manager):
        """Status should show open with next close time."""
        dt = datetime(2026, 5, 20, 10, 0, tzinfo=ET)
        status = manager.get_status(dt)

        assert status.is_open is True
        assert status.next_close is not None
        assert status.next_open is None

    def test_get_status_when_closed(self, manager):
        """Status should show closed with next open time."""
        dt = datetime(2026, 5, 20, 17, 0, tzinfo=ET)
        status = manager.get_status(dt)

        assert status.is_open is False
        assert status.next_open is not None
        assert status.next_close is None

    def test_next_open_skips_weekend(self, manager):
        """Next open from Friday evening should be Monday."""
        # Friday at 5:00 PM ET
        dt = datetime(2026, 5, 22, 17, 0, tzinfo=ET)
        status = manager.get_status(dt)

        assert status.next_open is not None
        assert status.next_open.weekday() == 0  # Monday
