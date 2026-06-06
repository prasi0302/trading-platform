"""REST API routes for Portfolio Service."""

from fastapi import APIRouter, HTTPException, Query

from trading_common import OrderFill, Portfolio

router = APIRouter(prefix="/api")


def create_router(app_state) -> APIRouter:
    """Create router with access to application state."""

    @router.get("/portfolio", response_model=Portfolio)
    async def get_portfolio(session_id: str = Query(...)):
        """Get current portfolio state for a session."""
        portfolio = await app_state.portfolio_manager.get_or_create(session_id)
        return portfolio

    @router.post("/portfolio/fill", response_model=Portfolio)
    async def update_on_fill(fill: OrderFill):
        """Update portfolio based on an order fill (called by Order Service)."""
        portfolio = await app_state.portfolio_manager.update_on_fill(fill)
        return portfolio

    @router.post("/portfolio/reset", response_model=Portfolio)
    async def reset_portfolio(session_id: str = Query(...)):
        """Reset portfolio to initial state ($100,000 cash, no holdings)."""
        portfolio = await app_state.portfolio_manager.reset(session_id)
        return portfolio

    return router
