"""WebSocket Gateway - Single client-facing WebSocket endpoint."""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from trading_common import RedisChannels

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PORT = int(os.getenv("PORT", "8005"))

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"ws-gateway","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket client connections and subscriptions."""

    def __init__(self):
        # client_id -> WebSocket
        self._connections: dict[str, WebSocket] = {}
        # client_id -> set of subscribed symbols
        self._subscriptions: dict[str, set[str]] = {}
        # session_id -> client_id (for targeted events)
        self._sessions: dict[str, str] = {}

    async def connect(self, client_id: str, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket
        self._subscriptions[client_id] = set()
        self._sessions[session_id] = client_id
        logger.info("Client connected: %s (session: %s)", client_id, session_id)

    def disconnect(self, client_id: str, session_id: str) -> None:
        self._connections.pop(client_id, None)
        self._subscriptions.pop(client_id, None)
        self._sessions.pop(session_id, None)
        logger.info("Client disconnected: %s", client_id)

    def subscribe(self, client_id: str, symbols: list[str]) -> None:
        if client_id in self._subscriptions:
            self._subscriptions[client_id].update(s.upper() for s in symbols)

    def unsubscribe(self, client_id: str, symbols: list[str]) -> None:
        if client_id in self._subscriptions:
            self._subscriptions[client_id] -= {s.upper() for s in symbols}

    async def broadcast_price(self, symbol: str, data: str) -> None:
        """Send price update to all clients subscribed to this symbol."""
        disconnected = []
        for client_id, subs in self._subscriptions.items():
            if symbol in subs:
                ws = self._connections.get(client_id)
                if ws:
                    try:
                        await ws.send_text(json.dumps({"type": "price", "data": json.loads(data)}))
                    except Exception:
                        disconnected.append(client_id)

        for cid in disconnected:
            self._connections.pop(cid, None)
            self._subscriptions.pop(cid, None)

    async def send_to_session(self, session_id: str, event_type: str, data: str) -> None:
        """Send event to a specific session's client."""
        client_id = self._sessions.get(session_id)
        if client_id:
            ws = self._connections.get(client_id)
            if ws:
                try:
                    await ws.send_text(json.dumps({"type": event_type, "data": json.loads(data)}))
                except Exception:
                    pass


manager = ConnectionManager()
redis_client: aioredis.Redis | None = None


async def redis_listener() -> None:
    """Subscribe to all Redis channels and route to clients."""
    global redis_client
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe(
        f"{RedisChannels.PRICE_PREFIX}*",
        f"{RedisChannels.ORDERS_PREFIX}*",
        f"{RedisChannels.ALERTS_PREFIX}*",
    )

    try:
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue

            channel = message["channel"]
            data = message["data"]

            if channel.startswith(RedisChannels.PRICE_PREFIX):
                symbol = channel.replace(RedisChannels.PRICE_PREFIX, "")
                await manager.broadcast_price(symbol, data)
            elif channel.startswith(RedisChannels.ORDERS_PREFIX):
                session_id = channel.replace(RedisChannels.ORDERS_PREFIX, "")
                await manager.send_to_session(session_id, "order", data)
            elif channel.startswith(RedisChannels.ALERTS_PREFIX):
                session_id = channel.replace(RedisChannels.ALERTS_PREFIX, "")
                await manager.send_to_session(session_id, "alert", data)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error("Redis listener error: %s", str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logger.info("WebSocket Gateway starting...")

    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    listener_task = asyncio.create_task(redis_listener(), name="redis-listener")

    logger.info("WebSocket Gateway started")
    yield

    logger.info("WebSocket Gateway shutting down...")
    listener_task.cancel()
    await redis_client.close()
    logger.info("WebSocket Gateway stopped")


app = FastAPI(title="WebSocket Gateway", version="0.1.0", lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Client WebSocket endpoint."""
    import uuid

    client_id = str(uuid.uuid4())[:8]
    # Session ID from query params
    session_id = websocket.query_params.get("session_id", client_id)

    await manager.connect(client_id, session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            if action == "subscribe":
                symbols = message.get("symbols", [])
                manager.subscribe(client_id, symbols)
                await websocket.send_text(json.dumps({"type": "subscribed", "symbols": symbols}))
            elif action == "unsubscribe":
                symbols = message.get("symbols", [])
                manager.unsubscribe(client_id, symbols)
                await websocket.send_text(json.dumps({"type": "unsubscribed", "symbols": symbols}))

    except WebSocketDisconnect:
        manager.disconnect(client_id, session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
        manager.disconnect(client_id, session_id)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ws-gateway",
        "active_connections": len(manager._connections),
    }
