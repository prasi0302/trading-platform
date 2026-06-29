"""Application state container for the Portfolio service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.portfolio_manager import PortfolioManager


@dataclass
class AppState:
    """Mutable application state populated during lifespan startup."""

    portfolio_manager: "PortfolioManager | None" = field(default=None)


app_state = AppState()


def get_app_state() -> AppState:
    """FastAPI dependency that returns the live application state."""
    return app_state
