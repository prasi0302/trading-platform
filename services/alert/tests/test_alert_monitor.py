"""Tests for alert monitor trigger logic."""

from datetime import datetime, timezone

import pytest

from trading_common import Alert, PriceTick
from app.core.alert_monitor import AlertMonitor


class TestAlertMonitor:
    @pytest.fixture
    def monitor(self):
        return AlertMonitor()

    @pytest.fixture
    def above_alert(self):
        return Alert(
            id="alert-1", session_id="s1", symbol="AAPL",
            condition="above", threshold=180.0, active=True,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def below_alert(self):
        return Alert(
            id="alert-2", session_id="s1", symbol="AAPL",
            condition="below", threshold=170.0, active=True,
            created_at=datetime.now(timezone.utc),
        )

    def test_above_alert_triggers(self, monitor, above_alert):
        tick = PriceTick(symbol="AAPL", price=181.0, bid=180.9, ask=181.1, volume=100, timestamp=datetime.now(timezone.utc))
        assert monitor._should_trigger(above_alert, tick) is True

    def test_above_alert_does_not_trigger(self, monitor, above_alert):
        tick = PriceTick(symbol="AAPL", price=175.0, bid=174.9, ask=175.1, volume=100, timestamp=datetime.now(timezone.utc))
        assert monitor._should_trigger(above_alert, tick) is False

    def test_below_alert_triggers(self, monitor, below_alert):
        tick = PriceTick(symbol="AAPL", price=169.0, bid=168.9, ask=169.1, volume=100, timestamp=datetime.now(timezone.utc))
        assert monitor._should_trigger(below_alert, tick) is True

    def test_below_alert_does_not_trigger(self, monitor, below_alert):
        tick = PriceTick(symbol="AAPL", price=175.0, bid=174.9, ask=175.1, volume=100, timestamp=datetime.now(timezone.utc))
        assert monitor._should_trigger(below_alert, tick) is False

    def test_add_and_remove_alert(self, monitor, above_alert):
        monitor.add_alert(above_alert)
        assert len(monitor._alerts["AAPL"]) == 1
        monitor.remove_alert("alert-1", "AAPL")
        assert len(monitor._alerts["AAPL"]) == 0
