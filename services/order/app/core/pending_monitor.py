"""Pending order monitor — checks price updates against limit/stop orders."""

import logging
from collections import defaultdict
from datetime import datetime, timezone

from trading_common import Order, OrderFill, OrderType, OrderSide, OrderStatus, PriceTick

from app.repository.order_repository import OrderRepository
from app.repository.redis_publisher import OrderEventPublisher
from app.core.portfolio_client import PortfolioClient

logger = logging.getLogger(__name__)


class PendingOrderMonitor:
    """Monitors price updates and triggers pending limit/stop-loss orders."""

    def __init__(
        self,
        order_repo: OrderRepository,
        event_publisher: OrderEventPublisher,
        portfolio_client: PortfolioClient,
    ):
        self._order_repo = order_repo
        self._event_publisher = event_publisher
        self._portfolio_client = portfolio_client
        # In-memory index: symbol -> list of pending order IDs
        self._pending_orders: dict[str, list[Order]] = defaultdict(list)

    def add_pending_order(self, order: Order) -> None:
        """Add an order to the monitoring list."""
        self._pending_orders[order.symbol].append(order)

    def remove_pending_order(self, order_id: str, symbol: str) -> None:
        """Remove an order from the monitoring list."""
        self._pending_orders[symbol] = [
            o for o in self._pending_orders[symbol] if o.id != order_id
        ]

    async def on_price_update(self, tick: PriceTick) -> None:
        """Check pending orders when a new price arrives."""
        pending = self._pending_orders.get(tick.symbol, [])
        if not pending:
            return

        triggered: list[Order] = []

        for order in pending:
            if self._should_trigger(order, tick):
                triggered.append(order)

        for order in triggered:
            await self._execute_triggered_order(order, tick)

    def _should_trigger(self, order: Order, tick: PriceTick) -> bool:
        """Determine if a pending order should be triggered by the current price."""
        if order.type == OrderType.LIMIT.value:
            if order.side == OrderSide.BUY.value:
                # Limit buy: trigger when price <= limit price
                return tick.ask <= order.price
            else:
                # Limit sell: trigger when price >= limit price
                return tick.bid >= order.price

        elif order.type == OrderType.STOP_LOSS.value:
            # Stop-loss (sell only): trigger when price <= stop price
            return tick.bid <= order.price

        return False

    async def _execute_triggered_order(self, order: Order, tick: PriceTick) -> None:
        """Execute a triggered pending order."""
        now = datetime.now(timezone.utc)

        # Fill at current market price
        fill_price = (
            tick.ask if order.side == OrderSide.BUY.value else tick.bid
        )

        # Optimistic concurrency — only fills if still pending
        filled = await self._order_repo.fill_order(order.id, fill_price, now)

        if not filled:
            # Already processed (cancelled or filled by another trigger)
            self.remove_pending_order(order.id, order.symbol)
            return

        # Remove from monitoring
        self.remove_pending_order(order.id, order.symbol)

        # Update portfolio
        fill = OrderFill(
            order_id=order.id,
            session_id=order.session_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            timestamp=now,
        )
        await self._portfolio_client.update_on_fill(fill)

        # Publish event
        filled_order = Order(
            id=order.id,
            session_id=order.session_id,
            symbol=order.symbol,
            type=order.type,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status=OrderStatus.FILLED.value,
            filled_price=fill_price,
            created_at=order.created_at,
            filled_at=now,
        )
        await self._event_publisher.publish_order_event(filled_order, "order_filled")

        logger.info(
            "Pending order triggered: %s %s %d @ %.2f (was %s @ %.2f)",
            order.side,
            order.symbol,
            order.quantity,
            fill_price,
            order.type,
            order.price,
        )

    async def load_pending_orders(self) -> None:
        """Load all pending orders from database on startup."""
        # This would query all pending orders and populate the in-memory index
        # Called during service startup to recover state
        pass
