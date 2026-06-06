# Trading Application

Real-time stock trading web application with simulated market data, order management, portfolio tracking, and price alerts.

## Architecture

- **Frontend**: React + TypeScript
- **Backend**: Python (FastAPI) microservices
- **Database**: RDS PostgreSQL + DynamoDB
- **Cache/PubSub**: Redis (ElastiCache)
- **Storage**: S3 + CloudFront
- **Deployment**: AWS ECS Fargate

## Services

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | REST request routing |
| Market Data | 8001 | Simulated price generation |
| Order | 8002 | Order lifecycle management |
| Portfolio | 8003 | Portfolio tracking and P&L |
| Alert | 8004 | Price alert monitoring |
| WebSocket Gateway | 8005 | Real-time event streaming |

## Quick Start (Local Development)

```bash
# Start infrastructure (Redis, DynamoDB Local, S3)
docker-compose up -d redis localstack

# Start Market Data Service
docker-compose up market-data
```

## Project Structure

```
Trading_application/
├── libs/common/          # Shared models, constants, utilities
├── services/
│   ├── market-data/      # Price simulation and distribution
│   ├── order/            # Order management
│   ├── portfolio/        # Portfolio tracking
│   ├── alert/            # Price alerts
│   ├── ws-gateway/       # WebSocket gateway
│   └── api-gateway/      # REST routing
├── frontend/             # React trading dashboard
├── docker-compose.yml    # Local development
└── scripts/              # Setup and utility scripts
```

## Environment Variables

See `.env.example` for all configuration options.
