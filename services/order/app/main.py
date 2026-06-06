"""Order Service - FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI

from trading_common import DEFAULT_SYMBOLS

from app.config import (
    DATABASE_URL,
    LOG_LEVEL,
    MARKET_DATA_URL,
    PORTFOLIO_SERVICE_URL,
    REDIS_URL,
)
from app.core.execution_engine import ExecutionEngine
from app.core.order_validator import OrderValidator
from app.core.pending_monitor import PendingOrderMonitor
from app.core.portfolio_client import PortfolioClient
from app.db.session import async_session_factory, init_db, close_db
from app.repository.order_repository import OrderRepository
from app.repository.redis_publisher import OrderEventPublisher
from app.repository.redis_subscriber import PriceCache

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"order","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Application state container."""

    validator: OrderValidator = field(default=None)
    execution_engine: ExecutionEngine = field(default=None)
    pending_monitor: PendingOrderMonitor = field(default=None)
    portfolio_client: PortfolioClient = field(default=None)
    event_publisher: OrderEventPublisher = field(default=None)
    price_cache: PriceCache = field(default=None)
    order_repo: OrderRepository = field(default=None)


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Order Service starting...")

    # Initialize database
    await init_db()

    # Create session for repository (simplified — in production use dependency injection)
    session = async_session_factory()
    app_state.order_repo = OrderRepository(session)

    # Initialize validator
    known_symbols = {s.ticker for s in DEFAULT_SYMBOLS}
    app_state.validator = OrderValidator(known_symbols)

    # Initialize portfolio client
    app_state.portfolio_client = PortfolioClient(PORTFOLIO_SERVICE_URL)
    await app_state.portfolio_client.start()

    # Initialize event publisher
    app_state.event_publisher = OrderEventPublisher(REDIS_URL)
    await app_state.event_publisher.connect()

    # Initialize execution engine
    app_state.execution_engine = ExecutionEngine(
        order_repo=app_state.order_repo,
        event_publisher=app_state.event_publisher,
        portfolio_client=app_state.portfolio_client,
    )

    # Initialize pending monitor
    app_state.pending_monitor = PendingOrderMonitor(
        order_repo=app_state.order_repo,
        event_publisher=app_state.event_publisher,
        portfolio_client=app_state.portfolio_client,
    )

    # Initialize price cache with pending monitor callback
    app_state.price_cache = PriceCache(
        redis_url=REDIS_URL,
        on_price_update=app_state.pending_monitor.on_price_update,
    )
    await app_state.price_cache.start()

    logger.info("Order Service started")
    yield

    # Shutdown
    logger.info("Order Service shutting down...")
    await app_state.price_cache.stop()
    await app_state.event_publisher.disconnect()
    await app_state.portfolio_client.stop()
    await session.close()
    await close_db()
    logger.info("Order Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Order Service",
    description="Order lifecycle management and execution",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routes
from app.api.routes import create_router
from app.api.health import create_health_router

app.include_router(create_router(app_state))
app.include_router(create_health_router(app_state))
