"""Portfolio Service - FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from fastapi import FastAPI

from app.config import LOG_LEVEL
from app.core.portfolio_manager import PortfolioManager
from app.db.session import async_session_factory, init_db, close_db

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"portfolio","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Application state container."""
    portfolio_manager: PortfolioManager = field(default=None)


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    logger.info("Portfolio Service starting...")
    await init_db()

    session = async_session_factory()
    app_state.portfolio_manager = PortfolioManager(session)

    logger.info("Portfolio Service started")
    yield

    logger.info("Portfolio Service shutting down...")
    await session.close()
    await close_db()
    logger.info("Portfolio Service stopped")


app = FastAPI(
    title="Portfolio Service",
    description="Portfolio tracking and P&L calculation",
    version="0.1.0",
    lifespan=lifespan,
)

from app.api.routes import create_router
app.include_router(create_router(app_state))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "portfolio"}
