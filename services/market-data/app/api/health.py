"""Health check endpoint for the Market Data service."""

from fastapi import APIRouter, Depends

from app.state import AppState, get_app_state

router = APIRouter()


@router.get("/health")
async def health_check(state: AppState = Depends(get_app_state)):
    """Service health check with dependency status."""
    redis_healthy = await state.redis_publisher.health_check()

    status = "healthy" if redis_healthy else "degraded"
    # ``simulation_engine.is_running`` is a @property; accessing it without
    # parentheses is intentional.
    simulation_running = state.simulation_engine.is_running
    return {
        "status": status,
        "service": "market-data",
        "simulation_running": simulation_running,
        "dependencies": {
            "redis": "connected" if redis_healthy else "disconnected",
        },
    }
