"""REST API routes for Portfolio Service."""

from fastapi import APIRouter, Depends, Query

from trading_common import OrderFill, Portfolio

from app.state import AppState, get_app_state

router = APIRouter(prefix="/api")


@router.get("/portfolio", response_model=Portfolio)
async def get_portfolio(
    session_id: str = Query(...),
    state: AppState = Depends(get_app_state),
):
    """Get current portfolio state for a session."""
    portfolio = await state.portfolio_manager.get_or_create(session_id)
    return portfolio


@router.post("/portfolio/fill", response_model=Portfolio)
async def update_on_fill(
    fill: OrderFill,
    state: AppState = Depends(get_app_state),
):
    """Update portfolio based on an order fill (called by Order Service)."""
    portfolio = await state.portfolio_manager.update_on_fill(fill)
    return portfolio


@router.post("/portfolio/reset", response_model=Portfolio)
async def reset_portfolio(
    session_id: str = Query(...),
    state: AppState = Depends(get_app_state),
):
    """Reset portfolio to initial state ($100,000 cash, no holdings)."""
    portfolio = await state.portfolio_manager.reset(session_id)
    return portfolio
