"""API Gateway - Reverse proxy routing requests to microservices."""

import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MARKET_DATA_URL = os.getenv("MARKET_DATA_URL", "http://localhost:8001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")
PORTFOLIO_SERVICE_URL = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")
ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8004")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"api-gateway","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Route mapping: path prefix -> upstream service URL
ROUTES = {
    "/api/symbols": MARKET_DATA_URL,
    "/api/market": MARKET_DATA_URL,
    "/api/orders": ORDER_SERVICE_URL,
    "/api/portfolio": PORTFOLIO_SERVICE_URL,
    "/api/alerts": ALERT_SERVICE_URL,
}

http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("API Gateway starting...")
    http_client = httpx.AsyncClient(timeout=10.0)
    logger.info("API Gateway started")
    yield
    logger.info("API Gateway shutting down...")
    await http_client.aclose()
    logger.info("API Gateway stopped")


app = FastAPI(title="API Gateway", version="0.1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """Route requests to appropriate upstream service."""
    full_path = f"/api/{path}"

    # Find matching upstream
    upstream_url = None
    for prefix, url in ROUTES.items():
        if full_path.startswith(prefix):
            upstream_url = url
            break

    if upstream_url is None:
        return Response(
            content='{"detail": "Not found"}',
            status_code=404,
            media_type="application/json",
        )

    # Build upstream request
    target_url = f"{upstream_url}{full_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward request
    try:
        body = await request.body()
        response = await http_client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers={
                "content-type": request.headers.get("content-type", "application/json"),
            },
        )

        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "application/json"),
        )
    except httpx.RequestError as e:
        logger.error("Upstream request failed: %s -> %s", target_url, str(e))
        return Response(
            content='{"detail": "Service unavailable"}',
            status_code=503,
            media_type="application/json",
        )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}
