"""SQLAlchemy models for the Order Service."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    """SQLAlchemy model for orders table."""

    __tablename__ = "orders"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    session_id = Column(String(64), nullable=False)
    symbol = Column(String(10), nullable=False)
    type = Column(String(10), nullable=False)  # market, limit, stop_loss
    side = Column(String(4), nullable=False)  # buy, sell
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=True)
    status = Column(String(10), nullable=False, default="pending")
    filled_price = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_orders_session_status", "session_id", "status"),
        Index("idx_orders_symbol_status", "symbol", "status"),
    )
