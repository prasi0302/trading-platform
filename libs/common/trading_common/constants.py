"""Shared constants for the trading application."""

from enum import Enum

from trading_common.models import Symbol


class RedisChannels:
    """Redis pub/sub channel patterns."""

    PRICE_PREFIX = "channel:price:"
    ORDERS_PREFIX = "channel:orders:"
    ALERTS_PREFIX = "channel:alerts:"

    @staticmethod
    def price(symbol: str) -> str:
        return f"channel:price:{symbol.upper()}"

    @staticmethod
    def orders(session_id: str) -> str:
        return f"channel:orders:{session_id}"

    @staticmethod
    def alerts(session_id: str) -> str:
        return f"channel:alerts:{session_id}"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


class AlertCondition(str, Enum):
    ABOVE = "above"
    BELOW = "below"


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1D"


DEFAULT_SYMBOLS: list[Symbol] = [
    Symbol(ticker="AAPL", name="Apple Inc.", sector="Technology", initial_price=175.0, volatility=0.25, drift=0.08),
    Symbol(ticker="GOOGL", name="Alphabet Inc.", sector="Technology", initial_price=140.0, volatility=0.28, drift=0.10),
    Symbol(ticker="MSFT", name="Microsoft Corp.", sector="Technology", initial_price=380.0, volatility=0.22, drift=0.09),
    Symbol(ticker="AMZN", name="Amazon.com Inc.", sector="Consumer", initial_price=180.0, volatility=0.30, drift=0.12),
    Symbol(ticker="TSLA", name="Tesla Inc.", sector="Automotive", initial_price=250.0, volatility=0.50, drift=0.15),
    Symbol(ticker="JPM", name="JPMorgan Chase", sector="Finance", initial_price=190.0, volatility=0.20, drift=0.06),
    Symbol(ticker="NVDA", name="NVIDIA Corp.", sector="Technology", initial_price=800.0, volatility=0.45, drift=0.20),
    Symbol(ticker="META", name="Meta Platforms", sector="Technology", initial_price=500.0, volatility=0.35, drift=0.11),
]
