"""Service configuration loaded from environment variables."""

import os

from trading_common import SimulationConfig


def load_config() -> SimulationConfig:
    """Load simulation configuration from environment variables."""
    return SimulationConfig(
        tick_interval_ms=int(os.getenv("TICK_INTERVAL_MS", "1000")),
    )


# Infrastructure configuration
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
DYNAMODB_TABLE: str = "market-data-ticks-v2"  # Migrating to new table
S3_BUCKET: str = os.getenv("S3_BUCKET", "trading-app-historical")
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
AWS_ENDPOINT_URL: str | None = os.getenv("AWS_ENDPOINT_URL")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8001"))
