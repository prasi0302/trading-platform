"""Shared exception types for the trading application."""


class TradingError(Exception):
    """Base exception for all trading application errors."""

    def __init__(self, message: str, code: str = "TRADING_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class SymbolNotFoundError(TradingError):
    """Raised when a requested symbol does not exist."""

    def __init__(self, symbol: str):
        super().__init__(
            message=f"Symbol '{symbol}' not found",
            code="SYMBOL_NOT_FOUND",
        )
        self.symbol = symbol


class InsufficientFundsError(TradingError):
    """Raised when a user lacks sufficient funds for an order."""

    def __init__(self, required: float, available: float):
        super().__init__(
            message=f"Insufficient funds: required ${required:.2f}, available ${available:.2f}",
            code="INSUFFICIENT_FUNDS",
        )
        self.required = required
        self.available = available


class OrderNotFoundError(TradingError):
    """Raised when a requested order does not exist."""

    def __init__(self, order_id: str):
        super().__init__(
            message=f"Order '{order_id}' not found",
            code="ORDER_NOT_FOUND",
        )
        self.order_id = order_id


class InvalidOrderError(TradingError):
    """Raised when an order request is invalid."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid order: {reason}",
            code="INVALID_ORDER",
        )
        self.reason = reason
