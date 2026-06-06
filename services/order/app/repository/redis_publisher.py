"""Redis publisher for order events (fire-and-forget)."""

import logging

import redis.asyncio as aioredis

from trading_common import Order, RedisChannels

logger = logging.getLogger(__name__)


class OrderEventPublisher:
    """Publishes order lifecycle events to Redis pub/sub."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._client = aioredis.from_url(
                self._redis_url, decode_responses=True, socket_connect_timeout=5
            )
            await self._client.ping()
            logger.info("Order event publisher connected to Redis")
        except Exception as e:
            logger.warning("Redis connection failed: %s", str(e))
            self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def publish_order_event(self, order: Order, event_type: str) -> None:
        """Publish an order event. Fire-and-forget — never blocks order processing."""
        if self._client is None:
            return

        try:
            channel = RedisChannels.orders(order.session_id)
            payload = {
                "event": event_type,
                "order": order.model_dump(mode="json"),
            }
            import json
            await self._client.publish(channel, json.dumps(payload))
        except Exception as e:
            logger.warning("Failed to publish order event: %s", str(e))
