"""Price tick generation using Geometric Brownian Motion (GBM).

The RNG used here is the standard library ``random`` module. Bandit B311
flags this as not suitable for cryptography, but this is **simulated market
data** — not a security primitive — so the standard PRNG is the right
choice. The B311 finding on this file is intentional; see ``# nosec B311``
on the call site below.
"""

import random  # nosec B311 - simulated market data, not security-sensitive
from datetime import datetime, timezone

import numpy as np

from trading_common import PriceTick, SimulationConfig, Symbol

# Trading seconds per year: 252 trading days * 6.5 hours * 3600 seconds
TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600


class TickGenerator:
    """Generates simulated price ticks using Geometric Brownian Motion."""

    def __init__(self, symbol: Symbol, config: SimulationConfig):
        self._symbol = symbol
        self._config = config
        self._current_price = symbol.initial_price
        self._rng = np.random.default_rng()

    @property
    def current_price(self) -> float:
        return self._current_price

    @current_price.setter
    def current_price(self, value: float) -> None:
        self._current_price = max(value, 0.01)

    def generate_tick(self) -> PriceTick:
        """Generate the next price tick using GBM.

        Formula: S(t+dt) = S(t) * exp((mu - sigma^2/2) * dt + sigma * sqrt(dt) * Z)
        """
        dt = (self._config.tick_interval_ms / 1000.0) / TRADING_SECONDS_PER_YEAR

        drift = self._symbol.drift
        volatility = self._symbol.volatility

        # Mean-reversion pressure if price exceeds 10x initial
        if self._current_price > self._symbol.initial_price * 10:
            drift = 0.0

        z = self._rng.standard_normal()
        price_change = self._current_price * (
            drift * dt + volatility * np.sqrt(dt) * z
        )

        new_price = self._current_price + price_change
        # Apply price floor
        self._current_price = max(new_price, 0.01)

        # Calculate bid/ask spread
        spread = self._current_price * (self._config.spread_bps / 10000.0)
        bid = self._current_price - spread
        ask = self._current_price + spread

        # Generate volume. nosec B311: deliberate use of standard PRNG for
        # simulated market data; cryptographic RNG would be incorrect here.
        volume_variation = random.uniform(  # nosec B311
            -self._config.volume_volatility, self._config.volume_volatility
        )
        volume = max(1, int(self._config.volume_base * (1 + volume_variation)))

        return PriceTick(
            symbol=self._symbol.ticker,
            price=round(self._current_price, 2),
            bid=round(max(bid, 0.01), 2),
            ask=round(ask, 2),
            volume=volume,
            timestamp=datetime.now(timezone.utc),
        )
