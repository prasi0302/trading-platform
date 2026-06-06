"""REST API routes for the Market Data Service."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from trading_common import OHLCV, MarketStatus, PriceTick, Symbol, Timeframe
from trading_common.exceptions import SymbolNotFoundError

router = APIRouter(prefix="/api")


def create_router(app_state) -> APIRouter:
    """Create router with access to application state."""

    @router.get("/symbols", response_model=list[Symbol])
    async def list_symbols():
        """List all available stock symbols."""
        return app_state.symbols

    @router.get("/symbols/{symbol}/price", response_model=PriceTick)
    async def get_price(symbol: str):
        """Get current price quote for a symbol."""
        symbol = symbol.upper()
        tick = app_state.price_cache.get(symbol)
        if tick is None:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
        return tick

    @router.get("/symbols/{symbol}/history", response_model=list[OHLCV])
    async def get_history(
        symbol: str,
        timeframe: str = Query(..., description="1m, 5m, 15m, 1h, 4h, or 1D"),
        start: datetime = Query(..., description="Start time (ISO 8601)"),
        end: datetime = Query(..., description="End time (ISO 8601)"),
    ):
        """Get historical OHLCV candlestick data."""
        symbol = symbol.upper()

        # Validate symbol
        symbol_obj = app_state.symbol_map.get(symbol)
        if symbol_obj is None:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

        # Validate timeframe
        try:
            tf = Timeframe(timeframe)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe '{timeframe}'. Valid: 1m, 5m, 15m, 1h, 4h, 1D",
            )

        # Validate date range
        if start >= end:
            raise HTTPException(status_code=400, detail="Start must be before end")

        candles = app_state.candle_aggregator.generate_history(
            symbol_obj, tf, start, end
        )
        return candles

    @router.get("/market/status", response_model=MarketStatus)
    async def get_market_status():
        """Get current market status (open/closed)."""
        return app_state.market_hours.get_status()

    return router
