"""Service configuration loaded from environment variables."""

import os

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_app",
)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
MARKET_DATA_URL: str = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8002"))
STARTING_CASH: float = float(os.getenv("STARTING_CASH", "100000.0"))
