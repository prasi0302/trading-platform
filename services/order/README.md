# Order Service

Order lifecycle management and execution service supporting market, limit, and stop-loss orders.

## Features

- Market orders: instant execution at current price
- Limit orders: execute when price reaches target
- Stop-loss orders: trigger sell when price drops to threshold
- Optimistic concurrency: no double-execution guaranteed
- In-memory price monitoring via Redis subscription
- Portfolio updates on fill (HTTP with retry)
- Fire-and-forget event publishing to Redis

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/orders | Submit a new order |
| DELETE | /api/orders/{id}?session_id= | Cancel a pending order |
| GET | /api/orders?session_id=&status= | List orders for session |
| GET | /api/orders/{id}?session_id= | Get single order |
| GET | /health | Service health check |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://... | PostgreSQL connection |
| REDIS_URL | redis://localhost:6379 | Redis for pub/sub |
| MARKET_DATA_URL | http://localhost:8001 | Market Data Service |
| PORTFOLIO_SERVICE_URL | http://localhost:8003 | Portfolio Service |
| LOG_LEVEL | INFO | Logging level |
| PORT | 8002 | Service port |
| STARTING_CASH | 100000.0 | Default starting balance |

## Local Development

```bash
docker-compose up redis localstack
cd services/order
pip install -e ".[dev]" -e ../../libs/common
pytest
uvicorn app.main:app --port 8002 --reload
```
