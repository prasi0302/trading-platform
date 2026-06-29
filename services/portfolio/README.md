# Portfolio Service

Portfolio tracking and P&L calculation service.

## Features

- Lazy portfolio initialization ($100,000 starting cash)
- Position tracking with weighted average cost
- Buy/sell fill processing
- Portfolio reset functionality
- Transaction audit log

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/portfolio?session_id= | Get portfolio state |
| POST | /api/portfolio/fill | Update on order fill (called by Order Service) |
| POST | /api/portfolio/reset?session_id= | Reset to initial state |
| GET | /health | Service health check |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://... | PostgreSQL connection |
| MARKET_DATA_URL | http://localhost:8001 | Market Data Service |
| STARTING_CASH | 100000.0 | Initial cash balance |
| LOG_LEVEL | INFO | Logging level |
| PORT | 8003 | Service port |
