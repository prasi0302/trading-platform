"""Tests for pending order monitor."""

from datetime import datetime, timezone

import pytest

from trading_common import Order, OrderStatus, PriceTick
from app.core.pending_monitor import PendingOrderMonitor


class TestPendingOrderMonitor:
    """Test suite for PendingOrderMonitor trigger logic."""

    @pytest.fixture
    def limit_buy_order(self):
        return Order(
            id="test-order-1",
            session_id="session-1",
            symbol="AAPL",
            type="limit",
            side="buy",
            quantity=10,
            price=170.00,
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def limit_sell_order(self):
        return Order(
            id="test-order-2",
            session_id="session-1",
            symbol="AAPL",
            type="limit",
            side="sell",
            quantity=5,
            price=180.00,
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def stop_loss_order(self):
        return Order(
            id="test-order-3",
            session_id="session-1",
            symbol="AAPL",
            type="stop_loss",
            side="sell",
            quantity=5,
            price=160.00,
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        )

    def test_limit_buy_triggers_when_price_below(self, limit_buy_order):
        """Limit buy should trigger when ask <= limit price."""
        monitor = PendingOrderMonitor(None, None, None)
        tick = PriceTick(
            symbol="AAPL", price=169.00, bid=168.95, ask=169.05,
            volume=1000, timestamp=datetime.now(timezone.utc),
        )
        assert monitor._should_trigger(limit_buy_order, tick) is True

    def test_limit_buy_does_not_trigger_when_price_above(self, limit_buy_order):
        """Limit buy should not trigger when ask > limit price."""
        monitor = PendingOrderMonitor(None, None, None)
        tick = PriceTick(
            symbol="AAPL", price=175.00, bid=174.95, ask=175.05,
            volume=1000, timestamp=datetime.now(timezone.utc),
        )
        assert monitor._should_trigger(limit_buy_order, tick) is False

    def test_limit_sell_triggers_when_price_above(self, limit_sell_order):
        """Limit sell should trigger when bid >= limit price."""
        monitor = PendingOrderMonitor(None, None, None)
        tick = PriceTick(
            symbol="AAPL", price=181.00, bid=180.95, ask=181.05,
            volume=1000, timestamp=datetime.now(timezone.utc),
        )
        assert monitor._should_trigger(limit_sell_order, tick) is True

    def test_stop_loss_triggers_when_price_drops(self, stop_loss_order):
        """Stop-loss should trigger when bid <= stop price."""
        monitor = PendingOrderMonitor(None, None, None)
        tick = PriceTick(
            symbol="AAPL", price=159.00, bid=158.95, ask=159.05,
            volume=1000, timestamp=datetime.now(timezone.utc),
        )
        assert monitor._should_trigger(stop_loss_order, tick) is True

    def test_stop_loss_does_not_trigger_above_price(self, stop_loss_order):
        """Stop-loss should not trigger when bid > stop price."""
        monitor = PendingOrderMonitor(None, None, None)
        tick = PriceTick(
            symbol="AAPL", price=175.00, bid=174.95, ask=175.05,
            volume=1000, timestamp=datetime.now(timezone.utc),
        )
        assert monitor._should_trigger(stop_loss_order, tick) is False
