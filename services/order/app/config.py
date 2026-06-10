"""Service configuration loaded from environment variables."""

import os


def _build_database_url() -> str:
    """Construct DATABASE_URL from components or use direct URL."""
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url
    # Build from individual components (production: DB_PASSWORD injected via ECS secret)
    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "trading_app")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{name}"


DATABASE_URL: str = _build_database_url()
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
MARKET_DATA_URL: str = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8002"))
STARTING_CASH: float = float(os.getenv("STARTING_CASH", "100000.0"))
