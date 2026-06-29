"""REST API routes for the Order Service."""

from fastapi import APIRouter, Depends, HTTPException, Query

from trading_common import Order, OrderRequest, OrderType
from trading_common.exceptions import (
    InsufficientFundsError,
    InvalidOrderError,
    SymbolNotFoundError,
)

from app.state import AppState, get_app_state

router = APIRouter(prefix="/api")


@router.post("/orders", response_model=Order, status_code=201)
async def submit_order(
    request: OrderRequest,
    state: AppState = Depends(get_app_state),
):
    """Submit a new order (market, limit, or stop-loss)."""
    try:
        # Get current price
        current_price = state.price_cache.get_price(request.symbol)

        # Get available cash and holdings
        available_cash = await state.portfolio_client.get_available_cash(
            request.session_id
        )
        pending_buy_total = await state.order_repo.get_pending_buy_total(
            request.session_id
        )
        effective_cash = available_cash - pending_buy_total

        available_shares = await state.portfolio_client.get_holdings_quantity(
            request.session_id, request.symbol.upper()
        )
        pending_sell_qty = await state.order_repo.get_pending_sell_quantity(
            request.session_id, request.symbol.upper()
        )
        effective_shares = available_shares - pending_sell_qty

        # Validate
        state.validator.validate(
            request, current_price, effective_cash, effective_shares
        )

        # Execute based on type
        order_type = OrderType(request.type)
        if order_type == OrderType.MARKET:
            order = await state.execution_engine.execute_market_order(
                request, current_price
            )
        else:
            order = await state.execution_engine.create_pending_order(request)
            state.pending_monitor.add_pending_order(order)

        return order

    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except InsufficientFundsError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except InvalidOrderError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.delete("/orders/{order_id}", response_model=Order)
async def cancel_order(
    order_id: str,
    session_id: str = Query(...),
    state: AppState = Depends(get_app_state),
):
    """Cancel a pending order."""
    cancelled = await state.order_repo.cancel_order(order_id, session_id)
    if not cancelled:
        order = await state.order_repo.get_by_id(order_id, session_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be cancelled (status: {order.status})",
        )

    state.pending_monitor.remove_pending_order(order_id, "")
    order = await state.order_repo.get_by_id(order_id, session_id)
    await state.event_publisher.publish_order_event(order, "order_cancelled")
    return order


@router.get("/orders", response_model=list[Order])
async def list_orders(
    session_id: str = Query(...),
    status: str | None = Query(default=None),
    state: AppState = Depends(get_app_state),
):
    """Get order history for a session."""
    return await state.order_repo.get_by_session(session_id, status)


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    session_id: str = Query(...),
    state: AppState = Depends(get_app_state),
):
    """Get a single order by ID."""
    order = await state.order_repo.get_by_id(order_id, session_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
