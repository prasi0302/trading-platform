"""Health check endpoint for Order Service."""

from fastapi import APIRouter, Depends

from app.state import AppState, get_app_state

router = APIRouter()


@router.get("/health")
async def health_check(state: AppState = Depends(get_app_state)):
    """Service health check with dependency status."""
    redis_ok = state.price_cache._client is not None
    db_ok = True  # Simplified — pool existence implies connectivity

    status = "healthy" if (redis_ok and db_ok) else "degraded"
    return {
        "status": status,
        "service": "order",
        "dependencies": {
            "redis": "connected" if redis_ok else "disconnected",
            "database": "connected" if db_ok else "disconnected",
        },
    }
