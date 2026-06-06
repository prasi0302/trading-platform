"""Simulation engine orchestrating price generation across all symbols."""

import asyncio
import logging
from typing import Callable, Awaitable

from trading_common import PriceTick, SimulationConfig, Symbol

from app.core.market_hours import MarketHoursManager
from app.core.tick_generator import TickGenerator

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Orchestrates GBM-based price simulation for all configured symbols."""

    def __init__(
        self,
        symbols: list[Symbol],
        config: SimulationConfig,
        on_tick: Callable[[PriceTick], Awaitable[None]],
    ):
        self._symbols = symbols
        self._config = config
        self._on_tick = on_tick
        self._market_hours = MarketHoursManager(config)
        self._generators: dict[str, TickGenerator] = {}
        self._running = False
        self._tasks: list[asyncio.Task] = []

        for symbol in symbols:
            self._generators[symbol.ticker] = TickGenerator(symbol, config)

    @property
    def is_running(self) -> bool:
        return self._running

    def get_current_price(self, symbol: str) -> float | None:
        """Get the current price for a symbol."""
        generator = self._generators.get(symbol.upper())
        if generator is None:
            return None
        return generator.current_price

    async def start(self) -> None:
        """Start the simulation engine."""
        if self._running:
            return

        self._running = True
        logger.info("Simulation engine starting for %d symbols", len(self._symbols))

        for symbol in self._symbols:
            task = asyncio.create_task(
                self._symbol_loop(symbol.ticker),
                name=f"sim-{symbol.ticker}",
            )
            self._tasks.append(task)

    async def stop(self) -> None:
        """Stop the simulation engine gracefully."""
        self._running = False
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Simulation engine stopped")

    async def _symbol_loop(self, ticker: str) -> None:
        """Generate ticks for a single symbol in a loop."""
        generator = self._generators[ticker]
        interval_seconds = self._config.tick_interval_ms / 1000.0

        while self._running:
            try:
                tick = generator.generate_tick()

                try:
                    await self._on_tick(tick)
                except Exception as e:
                    logger.error(
                        "Error publishing tick for %s: %s",
                        ticker,
                        str(e),
                        exc_info=True,
                    )

                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Unexpected error in symbol loop for %s: %s",
                    ticker,
                    str(e),
                    exc_info=True,
                )
                await asyncio.sleep(interval_seconds)
