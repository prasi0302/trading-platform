"""Order repository with optimistic concurrency control."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from trading_common import Order, OrderStatus

from app.db.models import OrderModel


class OrderRepository:
    """PostgreSQL repository for orders with optimistic concurrency."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, order: Order) -> Order:
        """Persist a new order."""
        model = OrderModel(
            id=uuid.UUID(order.id),
            session_id=order.session_id,
            symbol=order.symbol,
            type=order.type,
            side=order.side,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            filled_price=order.filled_price,
            created_at=order.created_at,
            filled_at=order.filled_at,
        )
        self._session.add(model)
        await self._session.commit()
        return order

    async def get_by_id(self, order_id: str, session_id: str) -> Order | None:
        """Get an order by ID, scoped to session."""
        result = await self._session.execute(
            select(OrderModel).where(
                OrderModel.id == uuid.UUID(order_id),
                OrderModel.session_id == session_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def get_by_session(
        self, session_id: str, status: str | None = None
    ) -> list[Order]:
        """Get all orders for a session, optionally filtered by status."""
        query = select(OrderModel).where(
            OrderModel.session_id == session_id
        ).order_by(OrderModel.created_at.desc())

        if status:
            query = query.where(OrderModel.status == status)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_pending_by_symbol(self, symbol: str) -> list[Order]:
        """Get all pending orders for a symbol (for monitoring)."""
        result = await self._session.execute(
            select(OrderModel).where(
                OrderModel.symbol == symbol,
                OrderModel.status == OrderStatus.PENDING.value,
            )
        )
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def fill_order(
        self, order_id: str, fill_price: float, filled_at: datetime
    ) -> bool:
        """Fill an order using optimistic concurrency.

        Returns True if the order was filled, False if already processed.
        """
        result = await self._session.execute(
            update(OrderModel)
            .where(
                OrderModel.id == uuid.UUID(order_id),
                OrderModel.status == OrderStatus.PENDING.value,
            )
            .values(
                status=OrderStatus.FILLED.value,
                filled_price=fill_price,
                filled_at=filled_at,
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    async def cancel_order(self, order_id: str, session_id: str) -> bool:
        """Cancel a pending order using optimistic concurrency.

        Returns True if cancelled, False if not pending.
        """
        result = await self._session.execute(
            update(OrderModel)
            .where(
                OrderModel.id == uuid.UUID(order_id),
                OrderModel.session_id == session_id,
                OrderModel.status == OrderStatus.PENDING.value,
            )
            .values(
                status=OrderStatus.CANCELLED.value,
                cancelled_at=datetime.now(timezone.utc),
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    async def get_pending_buy_total(self, session_id: str) -> float:
        """Get total reserved cash for pending buy orders."""
        result = await self._session.execute(
            select(OrderModel).where(
                OrderModel.session_id == session_id,
                OrderModel.status == OrderStatus.PENDING.value,
                OrderModel.side == "buy",
            )
        )
        models = result.scalars().all()
        return sum(float(m.price or 0) * m.quantity for m in models)

    async def get_pending_sell_quantity(self, session_id: str, symbol: str) -> int:
        """Get total shares reserved for pending sell orders."""
        result = await self._session.execute(
            select(OrderModel).where(
                OrderModel.session_id == session_id,
                OrderModel.symbol == symbol,
                OrderModel.status == OrderStatus.PENDING.value,
                OrderModel.side == "sell",
            )
        )
        models = result.scalars().all()
        return sum(m.quantity for m in models)

    def _to_domain(self, model: OrderModel) -> Order:
        """Convert SQLAlchemy model to domain entity."""
        return Order(
            id=str(model.id),
            session_id=model.session_id,
            symbol=model.symbol,
            type=model.type,
            side=model.side,
            quantity=model.quantity,
            price=float(model.price) if model.price else None,
            status=model.status,
            filled_price=float(model.filled_price) if model.filled_price else None,
            created_at=model.created_at,
            filled_at=model.filled_at,
        )
