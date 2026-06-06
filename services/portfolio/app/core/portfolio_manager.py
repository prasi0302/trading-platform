"""Portfolio management — position updates and P&L calculation."""

import logging
from decimal import Decimal

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from trading_common import OrderFill, OrderSide, Portfolio, Position

from app.config import STARTING_CASH
from app.db.models import PortfolioModel, PositionModel, TransactionModel

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages portfolio state, position updates, and P&L calculations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_or_create(self, session_id: str) -> Portfolio:
        """Get portfolio for session, creating if it doesn't exist."""
        result = await self._session.execute(
            select(PortfolioModel).where(PortfolioModel.session_id == session_id)
        )
        portfolio_model = result.scalar_one_or_none()

        if portfolio_model is None:
            portfolio_model = PortfolioModel(session_id=session_id, cash=Decimal(str(STARTING_CASH)))
            self._session.add(portfolio_model)
            await self._session.commit()

        # Load positions
        positions_result = await self._session.execute(
            select(PositionModel).where(PositionModel.session_id == session_id)
        )
        position_models = positions_result.scalars().all()

        holdings = [
            Position(
                symbol=p.symbol,
                quantity=p.quantity,
                avg_cost=float(p.avg_cost),
            )
            for p in position_models
            if p.quantity > 0
        ]

        cash = float(portfolio_model.cash)
        total_value = cash + sum(h.quantity * h.avg_cost for h in holdings)

        return Portfolio(
            session_id=session_id,
            cash=cash,
            holdings=holdings,
            total_value=total_value,
        )

    async def update_on_fill(self, fill: OrderFill) -> Portfolio:
        """Update portfolio based on an order fill."""
        # Ensure portfolio exists
        await self.get_or_create(fill.session_id)

        if fill.side == OrderSide.BUY.value:
            await self._process_buy(fill)
        else:
            await self._process_sell(fill)

        # Log transaction
        tx = TransactionModel(
            session_id=fill.session_id,
            order_id=fill.order_id,
            symbol=fill.symbol,
            side=fill.side,
            quantity=fill.quantity,
            price=Decimal(str(fill.fill_price)),
            timestamp=fill.timestamp,
        )
        self._session.add(tx)
        await self._session.commit()

        return await self.get_or_create(fill.session_id)

    async def reset(self, session_id: str) -> Portfolio:
        """Reset portfolio to initial state."""
        # Delete positions
        await self._session.execute(
            delete(PositionModel).where(PositionModel.session_id == session_id)
        )
        # Reset cash
        await self._session.execute(
            update(PortfolioModel)
            .where(PortfolioModel.session_id == session_id)
            .values(cash=Decimal(str(STARTING_CASH)))
        )
        # Delete transactions
        await self._session.execute(
            delete(TransactionModel).where(TransactionModel.session_id == session_id)
        )
        await self._session.commit()

        return await self.get_or_create(session_id)

    async def _process_buy(self, fill: OrderFill) -> None:
        """Process a buy fill: decrease cash, increase/create position."""
        cost = Decimal(str(fill.fill_price)) * fill.quantity

        # Decrease cash
        await self._session.execute(
            update(PortfolioModel)
            .where(PortfolioModel.session_id == fill.session_id)
            .values(cash=PortfolioModel.cash - cost)
        )

        # Update or create position
        result = await self._session.execute(
            select(PositionModel).where(
                PositionModel.session_id == fill.session_id,
                PositionModel.symbol == fill.symbol,
            )
        )
        position = result.scalar_one_or_none()

        if position is None:
            position = PositionModel(
                session_id=fill.session_id,
                symbol=fill.symbol,
                quantity=fill.quantity,
                avg_cost=Decimal(str(fill.fill_price)),
            )
            self._session.add(position)
        else:
            # Recalculate average cost
            old_total = Decimal(str(position.avg_cost)) * position.quantity
            new_total = old_total + cost
            new_quantity = position.quantity + fill.quantity
            new_avg = new_total / new_quantity

            position.quantity = new_quantity
            position.avg_cost = new_avg

    async def _process_sell(self, fill: OrderFill) -> None:
        """Process a sell fill: increase cash, decrease position."""
        proceeds = Decimal(str(fill.fill_price)) * fill.quantity

        # Increase cash
        await self._session.execute(
            update(PortfolioModel)
            .where(PortfolioModel.session_id == fill.session_id)
            .values(cash=PortfolioModel.cash + proceeds)
        )

        # Decrease position
        result = await self._session.execute(
            select(PositionModel).where(
                PositionModel.session_id == fill.session_id,
                PositionModel.symbol == fill.symbol,
            )
        )
        position = result.scalar_one_or_none()

        if position:
            new_quantity = position.quantity - fill.quantity
            if new_quantity <= 0:
                await self._session.delete(position)
            else:
                position.quantity = new_quantity
