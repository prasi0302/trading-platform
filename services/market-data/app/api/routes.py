"""REST API routes for the Market Data Service."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from trading_common import OHLCV, MarketStatus, PriceTick, Symbol, Timeframe

from app.state import AppState, get_app_state

router = APIRouter(prefix="/api")


@router.get("/symbols", response_model=list[Symbol])
async def list_symbols(state: AppState = Depends(get_app_state)):
    """List all available stock symbols."""
    return state.symbols


@router.get("/symbols/{symbol}/price", response_model=PriceTick)
async def get_price(symbol: str, state: AppState = Depends(get_app_state)):
    """Get current price quote for a symbol."""
    symbol = symbol.upper()
    tick = state.price_cache.get(symbol)
    if tick is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    return tick


@router.get("/symbols/{symbol}/history", response_model=list[OHLCV])
async def get_history(
    symbol: str,
    timeframe: str = Query(..., description="1m, 5m, 15m, 1h, 4h, or 1D"),
    start: datetime = Query(..., description="Start time (ISO 8601)"),
    end: datetime = Query(..., description="End time (ISO 8601)"),
    state: AppState = Depends(get_app_state),
):
    """Get historical OHLCV candlestick data."""
    symbol = symbol.upper()

    # Validate symbol
    symbol_obj = state.symbol_map.get(symbol)
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

    candles = state.candle_aggregator.generate_history(symbol_obj, tf, start, end)
    return candles


@router.get("/market/status", response_model=MarketStatus)
async def get_market_status(state: AppState = Depends(get_app_state)):
    """Get current market status (open/closed)."""
    return state.market_hours.get_status()
