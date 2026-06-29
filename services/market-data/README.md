# Market Data Service

Simulated stock market data generation and distribution service using Geometric Brownian Motion (GBM).

## Features

- Real-time price simulation for 8 US stocks (AAPL, GOOGL, MSFT, AMZN, TSLA, JPM, NVDA, META)
- Configurable tick frequency (default: 1 second)
- Market hours enforcement (Mon-Fri 9:30 AM - 4:00 PM ET)
- Redis pub/sub for real-time price distribution
- DynamoDB for tick persistence (7-day TTL)
- On-demand historical OHLCV generation (deterministic)
- Graceful degradation when Redis is unavailable

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/symbols | List all available symbols |
| GET | /api/symbols/{symbol}/price | Get current price quote |
| GET | /api/symbols/{symbol}/history | Get historical OHLCV candles |
| GET | /api/market/status | Get market open/closed status |
| GET | /health | Service health check |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| TICK_INTERVAL_MS | 1000 | Milliseconds between price ticks |
| REDIS_URL | redis://localhost:6379 | Redis connection URL |
| DYNAMODB_TABLE | market-data-ticks | DynamoDB table name |
| S3_BUCKET | trading-app-historical | S3 bucket for historical data |
| AWS_REGION | us-east-1 | AWS region |
| AWS_ENDPOINT_URL | (none) | LocalStack endpoint for local dev |
| LOG_LEVEL | INFO | Logging level |
| PORT | 8001 | Service port |

## Local Development

```bash
# From project root
docker-compose up redis localstack
cd services/market-data
pip install -e ".[dev]" -e ../../libs/common
pytest
uvicorn app.main:app --port 8001 --reload
```

## Running Tests

```bash
pytest tests/ -v
```
