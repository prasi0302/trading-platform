"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


def create_health_router(app_state) -> APIRouter:
    """Create health check router with access to application state."""

    @router.get("/health")
    async def health_check():
        """Service health check with dependency status."""
        redis_healthy = await app_state.redis_publisher.health_check()

        status = "healthy" if redis_healthy else "degraded"
        return {
            "status": status,
            "service": "market-data",
            "simulation_running": app_state.simulation_engine.is_running,
            "dependencies": {
                "redis": "connected" if redis_healthy else "disconnected",
            },
        }

    return router
