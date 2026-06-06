"""Order validation logic."""

from trading_common import OrderRequest, OrderType, OrderSide, PriceTick
from trading_common.exceptions import InvalidOrderError, SymbolNotFoundError, InsufficientFundsError


class OrderValidator:
    """Validates incoming order requests."""

    def __init__(self, known_symbols: set[str]):
        self._known_symbols = known_symbols

    def validate(
        self,
        request: OrderRequest,
        current_price: PriceTick | None,
        available_cash: float,
        available_shares: int,
    ) -> None:
        """Validate an order request. Raises on failure."""
        # Symbol validation
        symbol = request.symbol.upper()
        if symbol not in self._known_symbols:
            raise SymbolNotFoundError(symbol)

        # Type validation
        try:
            order_type = OrderType(request.type)
        except ValueError:
            raise InvalidOrderError(
                f"Invalid order type '{request.type}'. Valid: market, limit, stop_loss"
            )

        # Side validation
        try:
            OrderSide(request.side)
        except ValueError:
            raise InvalidOrderError(
                f"Invalid order side '{request.side}'. Valid: buy, sell"
            )

        # Price validation for limit/stop orders
        if order_type in (OrderType.LIMIT, OrderType.STOP_LOSS):
            if request.price is None or request.price <= 0:
                raise InvalidOrderError(
                    f"{order_type.value} orders require a positive price"
                )

        # Stop-loss must be sell
        if order_type == OrderType.STOP_LOSS and request.side != OrderSide.SELL.value:
            raise InvalidOrderError("Stop-loss orders can only be sell orders")

        # Market order requires current price
        if order_type == OrderType.MARKET and current_price is None:
            raise InvalidOrderError("Cannot execute market order: market data unavailable")

        # Funds validation for buy orders
        if request.side == OrderSide.BUY.value:
            if order_type == OrderType.MARKET:
                required = request.quantity * current_price.ask
            else:
                required = request.quantity * request.price

            if required > available_cash:
                raise InsufficientFundsError(required=required, available=available_cash)

        # Holdings validation for sell orders
        if request.side == OrderSide.SELL.value:
            if request.quantity > available_shares:
                raise InvalidOrderError(
                    f"Insufficient shares: need {request.quantity}, have {available_shares}"
                )
