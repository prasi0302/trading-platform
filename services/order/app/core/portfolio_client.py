"""HTTP client for Portfolio Service with retry logic."""

import asyncio
import logging

import httpx

from trading_common import OrderFill

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # Exponential backoff
TIMEOUT_SECONDS = 5.0


class PortfolioClient:
    """Async HTTP client for Portfolio Service with retry."""

    def __init__(self, base_url: str):
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=TIMEOUT_SECONDS,
        )

    async def stop(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()

    async def update_on_fill(self, fill: OrderFill) -> bool:
        """Notify Portfolio Service of an order fill. Retries on failure."""
        if self._client is None:
            logger.error("Portfolio client not initialized")
            return False

        for attempt in range(MAX_RETRIES):
            try:
                response = await self._client.post(
                    "/api/portfolio/fill",
                    json=fill.model_dump(mode="json"),
                )
                if response.status_code == 200:
                    return True
                logger.warning(
                    "Portfolio update failed (attempt %d): status %d",
                    attempt + 1,
                    response.status_code,
                )
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(
                    "Portfolio update error (attempt %d): %s",
                    attempt + 1,
                    str(e),
                )

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])

        logger.error(
            "Portfolio update failed after %d attempts for order %s",
            MAX_RETRIES,
            fill.order_id,
        )
        return False

    async def get_available_cash(self, session_id: str) -> float:
        """Get available cash for a session."""
        if self._client is None:
            return 0.0
        try:
            response = await self._client.get(
                f"/api/portfolio",
                params={"session_id": session_id},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("cash", 0.0)
        except Exception as e:
            logger.warning("Failed to get portfolio cash: %s", str(e))
        return 0.0

    async def get_holdings_quantity(self, session_id: str, symbol: str) -> int:
        """Get quantity of shares held for a symbol."""
        if self._client is None:
            return 0
        try:
            response = await self._client.get(
                f"/api/portfolio",
                params={"session_id": session_id},
            )
            if response.status_code == 200:
                data = response.json()
                for holding in data.get("holdings", []):
                    if holding["symbol"] == symbol:
                        return holding["quantity"]
        except Exception as e:
            logger.warning("Failed to get holdings: %s", str(e))
        return 0
