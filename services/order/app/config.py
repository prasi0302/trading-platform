"""Service configuration loaded from environment variables."""

import os


def _build_database_url() -> str:
    """Construct DATABASE_URL from components or use direct URL."""
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url
    # Build from individual components. In production DB_PASSWORD is injected
    # via the ECS task definition's `secrets` block from AWS Secrets Manager
    # (see infra/trading_stack.py). For local development, set DB_PASSWORD
    # explicitly in your `.env` file or shell environment.
    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "trading_app")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")
    if not password:
        raise RuntimeError(
            "DB_PASSWORD is not set. In production this is injected from AWS "
            "Secrets Manager; for local development export DB_PASSWORD in your "
            "shell or .env file."
        )
    return f"postgresql+asyncpg://{user}:{password}@{host}:5432/{name}"


DATABASE_URL: str = _build_database_url()
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
MARKET_DATA_URL: str = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
PORTFOLIO_SERVICE_URL: str = "http://portfolio-v2.internal:8003"  # Updated service discovery endpoint
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8002"))
STARTING_CASH: float = float(os.getenv("STARTING_CASH", "100000.0"))
