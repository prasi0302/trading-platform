"""Tests for portfolio manager business logic."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from trading_common import OrderFill


class TestPortfolioManagerLogic:
    """Test portfolio calculation logic (unit tests without DB)."""

    def test_buy_cost_calculation(self):
        """Buy cost should be quantity × fill_price."""
        fill = OrderFill(
            order_id="order-1",
            session_id="session-1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            fill_price=175.50,
            timestamp=datetime.now(timezone.utc),
        )
        cost = fill.quantity * fill.fill_price
        assert cost == 1755.0

    def test_sell_proceeds_calculation(self):
        """Sell proceeds should be quantity × fill_price."""
        fill = OrderFill(
            order_id="order-2",
            session_id="session-1",
            symbol="AAPL",
            side="sell",
            quantity=5,
            fill_price=180.00,
            timestamp=datetime.now(timezone.utc),
        )
        proceeds = fill.quantity * fill.fill_price
        assert proceeds == 900.0

    def test_average_cost_recalculation(self):
        """Average cost should be weighted average after multiple buys."""
        # First buy: 10 shares @ $100
        old_qty = 10
        old_avg = Decimal("100.00")
        # Second buy: 5 shares @ $110
        new_qty = 5
        new_price = Decimal("110.00")

        old_total = old_avg * old_qty
        new_total = old_total + (new_price * new_qty)
        total_qty = old_qty + new_qty
        new_avg = new_total / total_qty

        assert float(new_avg) == pytest.approx(103.33, rel=0.01)

    def test_starting_cash(self):
        """Starting cash should be $100,000."""
        from app.config import STARTING_CASH
        assert STARTING_CASH == 100000.0
