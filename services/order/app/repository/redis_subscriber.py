"""Redis subscriber for price updates with in-memory cache."""

import asyncio
import json
import logging
from typing import Callable, Awaitable

import redis.asyncio as aioredis

from trading_common import PriceTick, RedisChannels

logger = logging.getLogger(__name__)


class PriceCache:
    """In-memory price cache updated from Redis subscription."""

    def __init__(
        self,
        redis_url: str,
        on_price_update: Callable[[PriceTick], Awaitable[None]] | None = None,
    ):
        self._redis_url = redis_url
        self._prices: dict[str, PriceTick] = {}
        self._on_price_update = on_price_update
        self._client: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._task: asyncio.Task | None = None

    def get_price(self, symbol: str) -> PriceTick | None:
        """Get latest cached price for a symbol."""
        return self._prices.get(symbol.upper())

    def get_all_prices(self) -> dict[str, PriceTick]:
        """Get all cached prices."""
        return dict(self._prices)

    async def start(self) -> None:
        """Start subscribing to price updates."""
        try:
            self._client = aioredis.from_url(self._redis_url, decode_responses=True)
            self._pubsub = self._client.pubsub()
            await self._pubsub.psubscribe(f"{RedisChannels.PRICE_PREFIX}*")
            self._task = asyncio.create_task(self._listen(), name="price-cache-listener")
            logger.info("Price cache subscriber started")
        except Exception as e:
            logger.warning("Failed to start price cache subscriber: %s", str(e))

    async def stop(self) -> None:
        """Stop subscribing."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
        if self._client:
            await self._client.close()
        logger.info("Price cache subscriber stopped")

    async def _listen(self) -> None:
        """Listen for price updates from Redis."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "pmessage":
                    continue

                try:
                    data = json.loads(message["data"])
                    tick = PriceTick(**data)
                    self._prices[tick.symbol] = tick

                    if self._on_price_update:
                        await self._on_price_update(tick)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning("Invalid price message: %s", str(e))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Price cache listener error: %s", str(e))
