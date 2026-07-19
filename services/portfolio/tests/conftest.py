"""Shared test fixtures for Portfolio Service tests.

Sets DB_PASSWORD before any test module imports app.config, so that the
module-level DATABASE_URL construction in app/config.py does not raise at
import time. Unit tests never open a database connection; the value is a
placeholder used only to satisfy the config-validator.

In production DB_PASSWORD is injected via the ECS task definition's `secrets`
block from AWS Secrets Manager (see infra/trading_stack.py). Local dev still
requires you to export DB_PASSWORD in your shell — the setdefault below only
takes effect when the variable is not set.
"""

import os

os.environ.setdefault("DB_PASSWORD", "test")
