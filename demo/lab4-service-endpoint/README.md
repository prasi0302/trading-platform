# Lab 4: Non-Existent Service Endpoint — Cascading Timeouts

## Scenario
A developer updates the Order Service to use a "new internal DNS" endpoint for the Market Data Service — but the hostname doesn't exist. The pipeline passes, deploy succeeds, but every order operation that needs price data times out. This causes **cascading failures** across the trading flow.

**Key difference from previous labs**: This demonstrates **cross-service failure correlation** and **user-visible impact** (orders fail with timeouts). The error type is different (ConnectError/Timeout vs AccessDenied).

## Story Arc
```
Lab 1: Build failure (pipeline breaks)
Lab 2: Permission failure (IAM removed via CLI)
Lab 3: Bad code commit (wrong resource name)
Lab 4: Service discovery failure (cascading timeouts) ← YOU ARE HERE
```

## Flow
```
Bad commit (hardcodes non-existent service URL)
  → Pipeline passes (tests mock HTTP)
  → Deploy succeeds (container starts fine)
  → User places an order
  → Order Service tries to reach 'market-data-v2.internal:8001'
  → DNS resolution fails / connection refused
  → httpx.ConnectError in Order Service logs
  → CloudWatch Metric Filter catches "ConnectError"
  → CloudWatch Alarm triggers → EventBridge → Lambda → DevOps Agent
  → Agent investigates: reads logs + checks GitHub commits
  → Root cause: commit changed service endpoint to non-existent host
```

## What the DevOps Agent does
- Receives webhook (CloudWatch Alarm source)
- Reads Order Service CloudWatch Logs → sees `ConnectError` or `TimeoutException`
- Notes the target host `market-data-v2.internal:8001` doesn't resolve
- Checks GitHub → sees recent commit that modified `config.py` with endpoint change
- **Correlates timeline**: errors started after that commit was deployed
- Root cause: "Commit changed MARKET_DATA_URL to non-existent internal hostname"
- Mitigation: revert the endpoint or provision the DNS record

## What the audience sees in the UI
- App loads normally, price charts update (Market Data itself is fine)
- Try to **place an order** → hangs for several seconds → fails
- Classic cascading failure: broken inter-service communication

## AWS Resources Created
| Resource | Name |
|----------|------|
| Metric Filter | `OrderServiceConnectTimeout` on Order Service log group |
| CloudWatch Alarm | `TradingApp-Order-ServiceTimeout` |
| EventBridge Rule | `TradingApp-OrderTimeout-ToDevOps` |

## Scripts
- `inject.sh` — Changes MARKET_DATA_URL to non-existent host, commits, pushes
- `fix.sh` — Reverts to env-var config, commits, pushes

## Usage
```bash
# Inject the failure (commits and pushes)
./demo/lab4-service-endpoint/inject.sh

# Wait for pipeline to deploy (~3-5 min)
# Then trigger errors by placing an order in the UI, or:
curl -X POST http://Tradin-Tradi-VNtUgZp6acFf-284746681.us-east-1.elb.amazonaws.com/api/orders \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"test","symbol":"AAPL","side":"buy","order_type":"market","quantity":10}'

# Watch alarm
aws cloudwatch describe-alarms --alarm-names TradingApp-Order-ServiceTimeout \
  --profile gfs-workshop --region us-east-1 --query 'MetricAlarms[0].StateValue'

# After investigation, fix it
./demo/lab4-service-endpoint/fix.sh
```

## Expected Timeline
1. **T+0s**: inject.sh commits + pushes
2. **T+1-3min**: Pipeline passes (test → build → deploy)
3. **T+3-5min**: New container deployed with bad endpoint
4. **T+3-5min**: First order attempt → ConnectError (immediate, or wait for order)
5. **T+4-6min**: CloudWatch Alarm triggers → webhook → DevOps Agent
6. **T+5-10min**: Agent investigation complete — correlates timeout with the commit
