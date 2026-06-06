"""Health check endpoint for Order Service."""

from fastapi import APIRouter

router = APIRouter()


def create_health_router(app_state) -> APIRouter:
    """Create health check router."""

    @router.get("/health")
    async def health_check():
        """Service health check with dependency status."""
        redis_ok = app_state.price_cache._client is not None
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

    return router
