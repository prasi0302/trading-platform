"""Order execution engine for market orders."""

import logging
import uuid
from datetime import datetime, timezone

from trading_common import Order, OrderFill, OrderRequest, OrderType, OrderSide, OrderStatus, PriceTick

from app.repository.order_repository import OrderRepository
from app.repository.redis_publisher import OrderEventPublisher
from app.core.portfolio_client import PortfolioClient

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Executes market orders immediately at current price."""

    def __init__(
        self,
        order_repo: OrderRepository,
        event_publisher: OrderEventPublisher,
        portfolio_client: PortfolioClient,
    ):
        self._order_repo = order_repo
        self._event_publisher = event_publisher
        self._portfolio_client = portfolio_client

    async def execute_market_order(
        self, request: OrderRequest, current_price: PriceTick
    ) -> Order:
        """Execute a market order immediately."""
        now = datetime.now(timezone.utc)

        # Determine fill price (ask for buy, bid for sell)
        fill_price = (
            current_price.ask
            if request.side == OrderSide.BUY.value
            else current_price.bid
        )

        # Create filled order
        order = Order(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            symbol=request.symbol.upper(),
            type=request.type,
            side=request.side,
            quantity=request.quantity,
            price=None,
            status=OrderStatus.FILLED.value,
            filled_price=fill_price,
            created_at=now,
            filled_at=now,
        )

        # Persist order
        await self._order_repo.create(order)

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

        # Publish event (fire-and-forget)
        await self._event_publisher.publish_order_event(order, "order_filled")

        logger.info(
            "Market order filled: %s %s %d %s @ %.2f",
            order.side,
            order.symbol,
            order.quantity,
            order.id[:8],
            fill_price,
        )
        return order

    async def create_pending_order(self, request: OrderRequest) -> Order:
        """Create a pending limit or stop-loss order."""
        now = datetime.now(timezone.utc)

        order = Order(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            symbol=request.symbol.upper(),
            type=request.type,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            status=OrderStatus.PENDING.value,
            filled_price=None,
            created_at=now,
            filled_at=None,
        )

        await self._order_repo.create(order)
        await self._event_publisher.publish_order_event(order, "order_submitted")

        logger.info(
            "Pending order created: %s %s %d %s @ %.2f (%s)",
            order.side,
            order.symbol,
            order.quantity,
            order.type,
            order.price,
            order.id[:8],
        )
        return order
