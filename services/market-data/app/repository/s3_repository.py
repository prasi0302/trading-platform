"""S3 repository for historical OHLCV data storage."""

import json
import logging

import aioboto3

from trading_common import OHLCV

logger = logging.getLogger(__name__)


class S3Repository:
    """Stores and retrieves historical OHLCV data from S3."""

    def __init__(self, bucket: str, region: str, endpoint_url: str | None = None):
        self._bucket = bucket
        self._region = region
        self._endpoint_url = endpoint_url
        self._session = aioboto3.Session()

    async def store_candles(
        self, symbol: str, timeframe: str, date: str, candles: list[OHLCV]
    ) -> None:
        """Store candles to S3 as JSON."""
        key = f"historical/{symbol}/{timeframe}/{date}.json"
        data = json.dumps([c.model_dump(mode="json") for c in candles])

        try:
            async with self._session.client(
                "s3",
                region_name=self._region,
                endpoint_url=self._endpoint_url,
            ) as client:
                await client.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=data.encode(),
                    ContentType="application/json",
                )
                logger.debug("Stored %d candles to s3://%s/%s", len(candles), self._bucket, key)
        except Exception as e:
            logger.error("S3 store failed for %s: %s", key, str(e))

    async def get_candles(
        self, symbol: str, timeframe: str, date: str
    ) -> list[OHLCV] | None:
        """Retrieve candles from S3. Returns None if not found."""
        key = f"historical/{symbol}/{timeframe}/{date}.json"

        try:
            async with self._session.client(
                "s3",
                region_name=self._region,
                endpoint_url=self._endpoint_url,
            ) as client:
                response = await client.get_object(Bucket=self._bucket, Key=key)
                body = await response["Body"].read()
                data = json.loads(body.decode())
                return [OHLCV(**item) for item in data]
        except client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.debug("S3 get failed for %s: %s", key, str(e))
            return None
