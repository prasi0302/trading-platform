"""Tests for order validation logic."""

import pytest

from trading_common import OrderRequest, PriceTick
from trading_common.exceptions import (
    InsufficientFundsError,
    InvalidOrderError,
    SymbolNotFoundError,
)
from app.core.order_validator import OrderValidator


class TestOrderValidator:
    """Test suite for OrderValidator."""

    @pytest.fixture
    def validator(self, known_symbols):
        return OrderValidator(known_symbols)

    def test_valid_market_buy(self, validator, market_buy_request, sample_price):
        """Valid market buy should pass validation."""
        validator.validate(market_buy_request, sample_price, 100000.0, 0)

    def test_unknown_symbol_raises(self, validator, sample_price):
        """Unknown symbol should raise SymbolNotFoundError."""
        request = OrderRequest(
            symbol="UNKNOWN", type="market", side="buy", quantity=1, session_id="s1"
        )
        with pytest.raises(SymbolNotFoundError):
            validator.validate(request, sample_price, 100000.0, 0)

    def test_invalid_order_type_raises(self, validator, sample_price):
        """Invalid order type should raise InvalidOrderError."""
        request = OrderRequest(
            symbol="AAPL", type="invalid", side="buy", quantity=1, session_id="s1"
        )
        with pytest.raises(InvalidOrderError):
            validator.validate(request, sample_price, 100000.0, 0)

    def test_limit_order_requires_price(self, validator, sample_price):
        """Limit order without price should raise InvalidOrderError."""
        request = OrderRequest(
            symbol="AAPL", type="limit", side="buy", quantity=1, session_id="s1"
        )
        with pytest.raises(InvalidOrderError):
            validator.validate(request, sample_price, 100000.0, 0)

    def test_stop_loss_must_be_sell(self, validator, sample_price):
        """Stop-loss buy should raise InvalidOrderError."""
        request = OrderRequest(
            symbol="AAPL", type="stop_loss", side="buy", quantity=1, price=160.0, session_id="s1"
        )
        with pytest.raises(InvalidOrderError):
            validator.validate(request, sample_price, 100000.0, 0)

    def test_insufficient_funds_raises(self, validator, market_buy_request, sample_price):
        """Buy order exceeding available cash should raise InsufficientFundsError."""
        with pytest.raises(InsufficientFundsError):
            validator.validate(market_buy_request, sample_price, 100.0, 0)

    def test_insufficient_shares_raises(self, validator, sample_price):
        """Sell order exceeding available shares should raise InvalidOrderError."""
        request = OrderRequest(
            symbol="AAPL", type="market", side="sell", quantity=100, session_id="s1"
        )
        with pytest.raises(InvalidOrderError):
            validator.validate(request, sample_price, 100000.0, 10)

    def test_market_order_without_price_data_raises(self, validator, market_buy_request):
        """Market order without current price should raise InvalidOrderError."""
        with pytest.raises(InvalidOrderError):
            validator.validate(market_buy_request, None, 100000.0, 0)
