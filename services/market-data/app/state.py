"""Application state container for the Market Data service.

This module exposes a single ``app_state`` singleton that ``main.py`` populates
during the lifespan startup and that ``api.routes`` / ``api.health`` consume via
the FastAPI ``Depends(get_app_state)`` dependency. Keeping ``app_state`` in its
own module avoids circular imports between ``main`` and ``api.routes`` and lets
tests swap it out cleanly with ``app.dependency_overrides``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from trading_common import DEFAULT_SYMBOLS, PriceTick, SimulationConfig, Symbol

if TYPE_CHECKING:
    from app.core.candle_aggregator import CandleAggregator
    from app.core.market_hours import MarketHoursManager
    from app.core.simulation_engine import SimulationEngine
    from app.repository.dynamodb_repository import DynamoDBRepository
    from app.repository.redis_publisher import RedisPublisher
    from app.repository.s3_repository import S3Repository

from app.config import load_config


@dataclass
class AppState:
    """Mutable application state populated during the lifespan startup."""

    symbols: list[Symbol] = field(default_factory=lambda: DEFAULT_SYMBOLS)
    symbol_map: dict[str, Symbol] = field(default_factory=dict)
    price_cache: dict[str, PriceTick] = field(default_factory=dict)
    config: SimulationConfig = field(default_factory=load_config)
    redis_publisher: "RedisPublisher | None" = field(default=None)
    dynamodb_repo: "DynamoDBRepository | None" = field(default=None)
    s3_repo: "S3Repository | None" = field(default=None)
    simulation_engine: "SimulationEngine | None" = field(default=None)
    market_hours: "MarketHoursManager | None" = field(default=None)
    candle_aggregator: "CandleAggregator | None" = field(default=None)
    _flush_task: asyncio.Task | None = field(default=None, repr=False)


app_state = AppState()


def get_app_state() -> AppState:
    """FastAPI dependency that returns the live application state.

    Tests override this via ``app.dependency_overrides[get_app_state]``.
    """
    return app_state
