"""Alert Service - FastAPI application entry point."""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from trading_common import Alert, AlertCondition, PriceTick, RedisChannels, TriggeredAlert

from app.config import LOG_LEVEL, REDIS_URL
from app.core.alert_monitor import AlertMonitor

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"alert","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


class AlertRequest(BaseModel):
    session_id: str
    symbol: str
    condition: str  # "above" or "below"
    threshold: float


@dataclass
class AppState:
    alert_monitor: AlertMonitor = field(default=None)
    redis_client: aioredis.Redis = field(default=None)
    alerts_store: dict = field(default_factory=dict)  # alert_id -> Alert


app_state = AppState()


async def on_alert_triggered(triggered: TriggeredAlert) -> None:
    """Publish triggered alert to Redis."""
    if app_state.redis_client:
        try:
            channel = RedisChannels.alerts(triggered.session_id)
            await app_state.redis_client.publish(channel, triggered.model_dump_json())
        except Exception as e:
            logger.warning("Failed to publish alert trigger: %s", str(e))

    # Mark alert as inactive
    if triggered.alert_id in app_state.alerts_store:
        app_state.alerts_store[triggered.alert_id].active = False


async def price_listener() -> None:
    """Listen to price updates from Redis and feed to alert monitor."""
    import asyncio
    try:
        pubsub = app_state.redis_client.pubsub()
        await pubsub.psubscribe(f"{RedisChannels.PRICE_PREFIX}*")

        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            try:
                data = json.loads(message["data"])
                tick = PriceTick(**data)
                await app_state.alert_monitor.on_price_update(tick)
            except Exception as e:
                logger.warning("Error processing price for alerts: %s", str(e))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Price listener error: %s", str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    logger.info("Alert Service starting...")

    app_state.redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    app_state.alert_monitor = AlertMonitor(on_trigger=on_alert_triggered)

    listener_task = asyncio.create_task(price_listener(), name="alert-price-listener")

    logger.info("Alert Service started")
    yield

    logger.info("Alert Service shutting down...")
    listener_task.cancel()
    await app_state.redis_client.close()
    logger.info("Alert Service stopped")


app = FastAPI(title="Alert Service", version="0.1.0", lifespan=lifespan)


@app.post("/api/alerts", response_model=Alert, status_code=201)
async def create_alert(request: AlertRequest):
    """Create a new price alert."""
    try:
        AlertCondition(request.condition)
    except ValueError:
        raise HTTPException(status_code=400, detail="Condition must be 'above' or 'below'")

    alert = Alert(
        id=str(uuid.uuid4()),
        session_id=request.session_id,
        symbol=request.symbol.upper(),
        condition=request.condition,
        threshold=request.threshold,
        active=True,
        created_at=datetime.now(timezone.utc),
    )

    app_state.alerts_store[alert.id] = alert
    app_state.alert_monitor.add_alert(alert)
    return alert


@app.get("/api/alerts", response_model=list[Alert])
async def list_alerts(session_id: str = Query(...)):
    """Get all alerts for a session."""
    return [a for a in app_state.alerts_store.values() if a.session_id == session_id]


@app.delete("/api/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: str):
    """Delete an alert."""
    alert = app_state.alerts_store.pop(alert_id, None)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    app_state.alert_monitor.remove_alert(alert_id, alert.symbol)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "alert"}
