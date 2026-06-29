"""Application state container for the Order service.

Holds the singleton AppState populated by ``main.lifespan`` and consumed by
routes via ``Depends(get_app_state)``. Living in its own module avoids circular
imports between ``main`` and ``api.routes``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.execution_engine import ExecutionEngine
    from app.core.order_validator import OrderValidator
    from app.core.pending_monitor import PendingOrderMonitor
    from app.core.portfolio_client import PortfolioClient
    from app.repository.order_repository import OrderRepository
    from app.repository.redis_publisher import OrderEventPublisher
    from app.repository.redis_subscriber import PriceCache


@dataclass
class AppState:
    """Mutable application state populated during lifespan startup."""

    validator: "OrderValidator | None" = field(default=None)
    execution_engine: "ExecutionEngine | None" = field(default=None)
    pending_monitor: "PendingOrderMonitor | None" = field(default=None)
    portfolio_client: "PortfolioClient | None" = field(default=None)
    event_publisher: "OrderEventPublisher | None" = field(default=None)
    price_cache: "PriceCache | None" = field(default=None)
    order_repo: "OrderRepository | None" = field(default=None)


app_state = AppState()


def get_app_state() -> AppState:
    """FastAPI dependency that returns the live application state."""
    return app_state
