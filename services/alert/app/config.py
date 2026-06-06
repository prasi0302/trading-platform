"""Service configuration."""

import os

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/trading_app",
)
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8004"))
