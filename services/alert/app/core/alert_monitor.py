"""Alert monitoring — checks price updates against alert thresholds."""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from trading_common import Alert, AlertCondition, PriceTick, RedisChannels, TriggeredAlert

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitors price updates and triggers alerts when thresholds are crossed."""

    def __init__(self, on_trigger=None):
        self._alerts: dict[str, list[Alert]] = defaultdict(list)  # symbol -> alerts
        self._on_trigger = on_trigger  # callback for triggered alerts

    def add_alert(self, alert: Alert) -> None:
        """Add an alert to monitoring."""
        self._alerts[alert.symbol].append(alert)

    def remove_alert(self, alert_id: str, symbol: str) -> None:
        """Remove an alert from monitoring."""
        self._alerts[symbol] = [a for a in self._alerts[symbol] if a.id != alert_id]

    async def on_price_update(self, tick: PriceTick) -> None:
        """Check alerts when a new price arrives."""
        alerts = self._alerts.get(tick.symbol, [])
        if not alerts:
            return

        triggered: list[Alert] = []

        for alert in alerts:
            if self._should_trigger(alert, tick):
                triggered.append(alert)

        for alert in triggered:
            self.remove_alert(alert.id, alert.symbol)
            triggered_alert = TriggeredAlert(
                alert_id=alert.id,
                symbol=alert.symbol,
                condition=alert.condition,
                threshold=alert.threshold,
                triggered_price=tick.price,
                timestamp=datetime.now(timezone.utc),
                session_id=alert.session_id,
            )

            if self._on_trigger:
                await self._on_trigger(triggered_alert)

            logger.info(
                "Alert triggered: %s %s %.2f (price: %.2f)",
                alert.symbol,
                alert.condition,
                alert.threshold,
                tick.price,
            )

    def _should_trigger(self, alert: Alert, tick: PriceTick) -> bool:
        """Check if an alert should trigger."""
        if alert.condition == AlertCondition.ABOVE.value:
            return tick.price >= alert.threshold
        elif alert.condition == AlertCondition.BELOW.value:
            return tick.price <= alert.threshold
        return False
