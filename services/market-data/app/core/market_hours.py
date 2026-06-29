"""Market hours management for Eastern Time trading schedule."""

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from trading_common import MarketStatus, SimulationConfig

ET = ZoneInfo("America/New_York")


class MarketHoursManager:
    """Controls simulation based on US market hours (Mon-Fri 9:30 AM - 4:00 PM ET)."""

    def __init__(self, config: SimulationConfig):
        self._config = config
        self._market_open = time(config.market_open_hour, config.market_open_minute)
        self._market_close = time(config.market_close_hour, config.market_close_minute)

    def is_market_open(self, now: datetime | None = None) -> bool:
        """Check if the market is currently open."""
        now_et = self._to_et(now)

        # Weekends are closed
        if now_et.weekday() >= 5:
            return False

        current_time = now_et.time()
        return self._market_open <= current_time < self._market_close

    def get_status(self, now: datetime | None = None) -> MarketStatus:
        """Get current market status with next open/close times."""
        now_et = self._to_et(now)
        is_open = self.is_market_open(now)

        next_open = None
        next_close = None

        if is_open:
            next_close = now_et.replace(
                hour=self._market_close.hour,
                minute=self._market_close.minute,
                second=0,
                microsecond=0,
            )
        else:
            next_open = self._find_next_open(now_et)

        return MarketStatus(
            is_open=is_open,
            next_open=next_open,
            next_close=next_close,
            current_time_et=now_et,
        )

    def _find_next_open(self, now_et: datetime) -> datetime:
        """Find the next market open time."""
        candidate = now_et

        # If before market open today (weekday), open is today
        if candidate.weekday() < 5 and candidate.time() < self._market_open:
            return candidate.replace(
                hour=self._market_open.hour,
                minute=self._market_open.minute,
                second=0,
                microsecond=0,
            )

        # Otherwise, find next weekday
        candidate += timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)

        return candidate.replace(
            hour=self._market_open.hour,
            minute=self._market_open.minute,
            second=0,
            microsecond=0,
        )

    def _to_et(self, dt: datetime | None) -> datetime:
        """Convert datetime to Eastern Time."""
        if dt is None:
            return datetime.now(ET)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ET)
