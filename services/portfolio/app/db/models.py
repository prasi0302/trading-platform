"""SQLAlchemy models for Portfolio Service."""

from sqlalchemy import Column, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PortfolioModel(Base):
    """Portfolio state per session."""

    __tablename__ = "portfolios"

    session_id = Column(String(64), primary_key=True)
    cash = Column(Numeric(14, 2), nullable=False, default=100000.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PositionModel(Base):
    """Stock position within a portfolio."""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    avg_cost = Column(Numeric(12, 2), nullable=False, default=0.0)

    __table_args__ = (
        # Unique constraint: one position per symbol per session
        {"sqlite_autoincrement": True},
    )


class TransactionModel(Base):
    """Audit log of all portfolio transactions."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    symbol = Column(String(10), nullable=False)
    side = Column(String(4), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
