"""On-demand OHLCV candle generation with deterministic seeded random."""

import hashlib
from datetime import datetime, timedelta, timezone

import numpy as np

from trading_common import OHLCV, SimulationConfig, Symbol, Timeframe

# Trading seconds per year
TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600

TIMEFRAME_MINUTES = {
    Timeframe.M1: 1,
    Timeframe.M5: 5,
    Timeframe.M15: 15,
    Timeframe.H1: 60,
    Timeframe.H4: 240,
    Timeframe.D1: 390,  # 6.5 hours in minutes
}


class CandleAggregator:
    """Generates deterministic historical OHLCV data on demand."""

    def __init__(self, config: SimulationConfig):
        self._config = config

    def generate_history(
        self,
        symbol: Symbol,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> list[OHLCV]:
        """Generate historical candles for a symbol and timeframe.

        Uses seeded random for deterministic output: same inputs always
        produce the same candles.
        """
        seed = self._compute_seed(symbol.ticker, start, end)
        rng = np.random.default_rng(seed)

        candles: list[OHLCV] = []
        minutes_per_candle = TIMEFRAME_MINUTES[timeframe]
        ticks_per_candle = max(1, minutes_per_candle)  # 1 tick per minute simulated

        current_time = self._align_to_boundary(start, minutes_per_candle)
        price = symbol.initial_price

        while current_time < end:
            # Skip non-market hours
            if not self._is_market_time(current_time):
                current_time += timedelta(minutes=minutes_per_candle)
                continue

            # Generate ticks within this candle
            prices = []
            total_volume = 0

            for _ in range(ticks_per_candle):
                dt = 60.0 / TRADING_SECONDS_PER_YEAR  # 1 minute step
                z = rng.standard_normal()
                price_change = price * (
                    symbol.drift * dt + symbol.volatility * np.sqrt(dt) * z
                )
                price = max(price + price_change, 0.01)
                prices.append(price)
                total_volume += max(1, int(self._config.volume_base * (1 + rng.uniform(-0.5, 0.5))))

            if prices:
                candle = OHLCV(
                    symbol=symbol.ticker,
                    timeframe=timeframe.value,
                    open=round(prices[0], 2),
                    high=round(max(prices), 2),
                    low=round(min(prices), 2),
                    close=round(prices[-1], 2),
                    volume=total_volume,
                    timestamp=current_time,
                )
                candles.append(candle)

            current_time += timedelta(minutes=minutes_per_candle)

        return candles

    def _compute_seed(self, symbol: str, start: datetime, end: datetime) -> int:
        """Compute deterministic seed from symbol and date range."""
        seed_str = f"{symbol}:{start.date()}:{end.date()}"
        return int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)

    def _align_to_boundary(self, dt: datetime, minutes: int) -> datetime:
        """Align datetime to the nearest candle boundary."""
        total_minutes = dt.hour * 60 + dt.minute
        aligned_minutes = (total_minutes // minutes) * minutes
        return dt.replace(
            hour=aligned_minutes // 60,
            minute=aligned_minutes % 60,
            second=0,
            microsecond=0,
        )

    def _is_market_time(self, dt: datetime) -> bool:
        """Check if a datetime falls within market hours (9:30-16:00 ET, weekdays)."""
        if dt.weekday() >= 5:
            return False
        market_open_minutes = self._config.market_open_hour * 60 + self._config.market_open_minute
        market_close_minutes = self._config.market_close_hour * 60 + self._config.market_close_minute
        current_minutes = dt.hour * 60 + dt.minute
        return market_open_minutes <= current_minutes < market_close_minutes
