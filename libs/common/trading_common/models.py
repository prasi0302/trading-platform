"""Shared Pydantic models for the trading application."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Symbol(BaseModel):
    """Tradeable stock instrument."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Market sector")
    initial_price: float = Field(..., gt=0, description="Starting price for simulation")
    volatility: float = Field(..., gt=0, description="Annual volatility (sigma) for GBM")
    drift: float = Field(..., description="Annual drift (mu) for GBM")


class PriceTick(BaseModel):
    """Single price update event."""

    symbol: str
    price: float = Field(..., gt=0)
    bid: float = Field(..., gt=0)
    ask: float = Field(..., gt=0)
    volume: int = Field(..., ge=1)
    timestamp: datetime


class OHLCV(BaseModel):
    """Aggregated candlestick data for a time period."""

    symbol: str
    timeframe: str
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    timestamp: datetime


class SimulationConfig(BaseModel):
    """Configuration for the price simulation engine."""

    tick_interval_ms: int = Field(default=1000, ge=100, le=60000)
    market_open_hour: int = Field(default=9)
    market_open_minute: int = Field(default=30)
    market_close_hour: int = Field(default=16)
    market_close_minute: int = Field(default=0)
    spread_bps: float = Field(default=10.0, gt=0)
    volume_base: int = Field(default=1000, gt=0)
    volume_volatility: float = Field(default=0.5, ge=0, le=1)


class MarketStatus(BaseModel):
    """Current state of the simulated market."""

    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    current_time_et: datetime


class OrderRequest(BaseModel):
    """Request to submit a new order."""

    symbol: str
    type: str = Field(..., description="market, limit, or stop_loss")
    side: str = Field(..., description="buy or sell")
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    session_id: str


class Order(BaseModel):
    """Order entity with full lifecycle state."""

    id: str
    symbol: str
    type: str
    side: str
    quantity: int
    price: Optional[float] = None
    status: str = "pending"
    filled_price: Optional[float] = None
    created_at: datetime
    filled_at: Optional[datetime] = None
    session_id: str


class OrderFill(BaseModel):
    """Record of an order execution."""

    order_id: str
    symbol: str
    side: str
    quantity: int
    fill_price: float
    timestamp: datetime
    session_id: str


class Portfolio(BaseModel):
    """User portfolio state."""

    session_id: str
    cash: float = Field(default=100000.0)
    holdings: list["Position"] = Field(default_factory=list)
    total_value: float = Field(default=100000.0)


class Position(BaseModel):
    """Single stock position in a portfolio."""

    symbol: str
    quantity: int = Field(..., gt=0)
    avg_cost: float = Field(..., gt=0)
    current_price: float = Field(default=0.0, ge=0)
    pnl: float = Field(default=0.0)


class Alert(BaseModel):
    """Price alert definition."""

    id: str
    session_id: str
    symbol: str
    condition: str = Field(..., description="above or below")
    threshold: float = Field(..., gt=0)
    active: bool = True
    created_at: datetime


class TriggeredAlert(BaseModel):
    """Record of a triggered price alert."""

    alert_id: str
    symbol: str
    condition: str
    threshold: float
    triggered_price: float
    timestamp: datetime
    session_id: str
