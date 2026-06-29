"""Service configuration."""

import os

# Alert service uses Redis only — no PostgreSQL access — so no DB_PASSWORD,
# DATABASE_URL, or related components are required at startup.
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
PORT: int = int(os.getenv("PORT", "8004"))
