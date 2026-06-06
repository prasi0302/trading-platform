"""Service configuration."""

import os

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_app",
)
MARKET_DATA_URL: str = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8003"))
STARTING_CASH: float = float(os.getenv("STARTING_CASH", "100000.0"))
