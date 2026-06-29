"""Portfolio Service - FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import LOG_LEVEL
from app.core.portfolio_manager import PortfolioManager
from app.db.session import async_session_factory, init_db, close_db
from app.state import app_state

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"portfolio","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


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

from app.api.routes import router as api_router  # noqa: E402

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "portfolio"}
