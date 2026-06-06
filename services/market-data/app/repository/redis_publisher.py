"""Redis pub/sub publisher with graceful degradation."""

import asyncio
import logging

import redis.asyncio as aioredis

from trading_common import PriceTick, RedisChannels

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FAILURES = 5
DEGRADED_COOLDOWN_SECONDS = 30


class RedisPublisher:
    """Publishes price ticks to Redis pub/sub with graceful degradation."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client: aioredis.Redis | None = None
        self._consecutive_failures = 0
        self._degraded_until: float = 0

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            await self._client.ping()
            logger.info("Redis connected: %s", self._redis_url)
        except Exception as e:
            logger.warning("Redis connection failed: %s", str(e))
            self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def publish_tick(self, tick: PriceTick) -> bool:
        """Publish a price tick to Redis. Returns True on success."""
        if self._client is None:
            await self._try_reconnect()
            if self._client is None:
                return False

        # Check if in degraded state
        if self._is_degraded():
            return False

        try:
            channel = RedisChannels.price(tick.symbol)
            await self._client.publish(channel, tick.model_dump_json())
            self._consecutive_failures = 0
            return True
        except Exception as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                self._enter_degraded_state()
            logger.warning(
                "Redis publish failed for %s (attempt %d): %s",
                tick.symbol,
                self._consecutive_failures,
                str(e),
            )
            return False

    async def health_check(self) -> bool:
        """Check if Redis is reachable."""
        if self._client is None:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    def _is_degraded(self) -> bool:
        """Check if publisher is in degraded cooldown state."""
        if self._degraded_until == 0:
            return False
        current_time = asyncio.get_event_loop().time()
        if current_time >= self._degraded_until:
            self._degraded_until = 0
            self._consecutive_failures = 0
            logger.info("Redis publisher exiting degraded state, retrying")
            return False
        return True

    def _enter_degraded_state(self) -> None:
        """Enter degraded state — skip publishing for cooldown period."""
        current_time = asyncio.get_event_loop().time()
        self._degraded_until = current_time + DEGRADED_COOLDOWN_SECONDS
        logger.warning(
            "Redis publisher entering degraded state for %ds",
            DEGRADED_COOLDOWN_SECONDS,
        )

    async def _try_reconnect(self) -> None:
        """Attempt to reconnect to Redis."""
        try:
            await self.connect()
        except Exception:
            pass
