"""DynamoDB repository for price tick persistence."""

import logging
import time
from datetime import datetime, timedelta

import aioboto3

from trading_common import PriceTick

logger = logging.getLogger(__name__)

TTL_DAYS = 7
BATCH_SIZE = 25


class DynamoDBRepository:
    """Stores price ticks in DynamoDB with batch writes and TTL."""

    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None):
        self._table_name = table_name
        self._region = region
        self._endpoint_url = endpoint_url
        self._session = aioboto3.Session()
        self._buffer: list[dict] = []

    async def put_tick(self, tick: PriceTick) -> None:
        """Buffer a tick for batch writing."""
        ttl = int(time.time()) + (TTL_DAYS * 86400)
        item = {
            "symbol": {"S": tick.symbol},
            "timestamp": {"S": tick.timestamp.isoformat()},
            "price": {"N": str(tick.price)},
            "bid": {"N": str(tick.bid)},
            "ask": {"N": str(tick.ask)},
            "volume": {"N": str(tick.volume)},
            "ttl": {"N": str(ttl)},
        }
        self._buffer.append(item)

        if len(self._buffer) >= BATCH_SIZE:
            await self.flush()

    async def flush(self) -> None:
        """Write buffered items to DynamoDB."""
        if not self._buffer:
            return

        items_to_write = self._buffer[:BATCH_SIZE]
        self._buffer = self._buffer[BATCH_SIZE:]

        try:
            async with self._session.client(
                "dynamodb",
                region_name=self._region,
                endpoint_url=self._endpoint_url,
            ) as client:
                request_items = {
                    self._table_name: [
                        {"PutRequest": {"Item": item}} for item in items_to_write
                    ]
                }
                await client.batch_write_item(RequestItems=request_items)
                logger.debug("Flushed %d items to DynamoDB", len(items_to_write))
        except Exception as e:
            logger.error("DynamoDB batch write failed: %s", str(e))
            # Re-buffer failed items for retry
            self._buffer = items_to_write + self._buffer

    async def query_ticks(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[PriceTick]:
        """Query ticks for a symbol within a time range."""
        try:
            async with self._session.client(
                "dynamodb",
                region_name=self._region,
                endpoint_url=self._endpoint_url,
            ) as client:
                response = await client.query(
                    TableName=self._table_name,
                    KeyConditionExpression="symbol = :sym AND #ts BETWEEN :start AND :end",
                    ExpressionAttributeNames={"#ts": "timestamp"},
                    ExpressionAttributeValues={
                        ":sym": {"S": symbol},
                        ":start": {"S": start.isoformat()},
                        ":end": {"S": end.isoformat()},
                    },
                )

                ticks = []
                for item in response.get("Items", []):
                    ticks.append(
                        PriceTick(
                            symbol=item["symbol"]["S"],
                            price=float(item["price"]["N"]),
                            bid=float(item["bid"]["N"]),
                            ask=float(item["ask"]["N"]),
                            volume=int(item["volume"]["N"]),
                            timestamp=datetime.fromisoformat(item["timestamp"]["S"]),
                        )
                    )
                return ticks
        except Exception as e:
            logger.error("DynamoDB query failed for %s: %s", symbol, str(e))
            return []
