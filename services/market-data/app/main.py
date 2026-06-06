"""Market Data Service - FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI

from trading_common import DEFAULT_SYMBOLS, PriceTick, SimulationConfig, Symbol

from app.config import (
    AWS_REGION,
    AWS_ENDPOINT_URL,
    DYNAMODB_TABLE,
    LOG_LEVEL,
    REDIS_URL,
    S3_BUCKET,
    load_config,
)
from app.core.candle_aggregator import CandleAggregator
from app.core.market_hours import MarketHoursManager
from app.core.simulation_engine import SimulationEngine
from app.repository.dynamodb_repository import DynamoDBRepository
from app.repository.redis_publisher import RedisPublisher
from app.repository.s3_repository import S3Repository

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"market-data","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Application state container."""

    symbols: list[Symbol] = field(default_factory=lambda: DEFAULT_SYMBOLS)
    symbol_map: dict[str, Symbol] = field(default_factory=dict)
    price_cache: dict[str, PriceTick] = field(default_factory=dict)
    config: SimulationConfig = field(default_factory=load_config)
    redis_publisher: RedisPublisher = field(default=None)
    dynamodb_repo: DynamoDBRepository = field(default=None)
    s3_repo: S3Repository = field(default=None)
    simulation_engine: SimulationEngine = field(default=None)
    market_hours: MarketHoursManager = field(default=None)
    candle_aggregator: CandleAggregator = field(default=None)
    _flush_task: asyncio.Task | None = field(default=None, repr=False)


app_state = AppState()


async def on_tick(tick: PriceTick) -> None:
    """Handle a new price tick: cache, publish, persist."""
    app_state.price_cache[tick.symbol] = tick
    await app_state.redis_publisher.publish_tick(tick)
    await app_state.dynamodb_repo.put_tick(tick)


async def periodic_flush() -> None:
    """Periodically flush DynamoDB buffer."""
    while True:
        await asyncio.sleep(5)
        await app_state.dynamodb_repo.flush()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Market Data Service starting...")

    # Initialize state
    app_state.symbol_map = {s.ticker: s for s in app_state.symbols}
    app_state.market_hours = MarketHoursManager(app_state.config)
    app_state.candle_aggregator = CandleAggregator(app_state.config)

    # Initialize repositories
    app_state.redis_publisher = RedisPublisher(REDIS_URL)
    await app_state.redis_publisher.connect()

    app_state.dynamodb_repo = DynamoDBRepository(
        table_name=DYNAMODB_TABLE,
        region=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
    )
    app_state.s3_repo = S3Repository(
        bucket=S3_BUCKET,
        region=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,
    )

    # Start simulation engine
    app_state.simulation_engine = SimulationEngine(
        symbols=app_state.symbols,
        config=app_state.config,
        on_tick=on_tick,
    )
    await app_state.simulation_engine.start()

    # Start periodic DynamoDB flush
    app_state._flush_task = asyncio.create_task(periodic_flush())

    logger.info(
        "Market Data Service started: %d symbols, tick interval %dms",
        len(app_state.symbols),
        app_state.config.tick_interval_ms,
    )

    yield

    # Shutdown
    logger.info("Market Data Service shutting down...")
    if app_state._flush_task:
        app_state._flush_task.cancel()
    await app_state.simulation_engine.stop()
    await app_state.dynamodb_repo.flush()
    await app_state.redis_publisher.disconnect()
    logger.info("Market Data Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Market Data Service",
    description="Simulated stock market data generation and distribution",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routes
from app.api.routes import create_router
from app.api.health import create_health_router

app.include_router(create_router(app_state))
app.include_router(create_health_router(app_state))
