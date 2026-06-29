# Lab 3 — Service discovery failure: cascading timeouts

A developer updates the Order Service to use a "new internal DNS" endpoint for the Portfolio Service, but the hostname does not exist. The pipeline passes and the deploy succeeds, but every order operation that needs portfolio data times out, causing cascading failures across the trading flow.

This lab demonstrates **cross-service failure correlation** and **user-visible impact** (orders fail). The error type is different from Lab 2 (`ConnectError`/`Timeout` instead of `AccessDenied`).

## Flow

```
Bad commit (hardcodes non-existent service URL)
  -> Pipeline passes (tests mock HTTP)
  -> Deploy succeeds (container starts fine)
  -> User places an order
  -> Order Service tries to reach 'portfolio-v2.internal:8003'
  -> DNS resolution fails / connection refused
  -> httpx.ConnectError in Order Service logs
  -> CloudWatch metric filter catches "ConnectError"
  -> CloudWatch alarm -> EventBridge -> Lambda -> AWS DevOps Agent
  -> Agent investigates: reads logs and GitHub commits
  -> Root cause: commit changed the service endpoint to a non-existent host
```

## What the agent does

- Receives the webhook (CloudWatch alarm source)
- Reads Order Service CloudWatch logs and sees `ConnectError` or `TimeoutException`
- Notes the target host `portfolio-v2.internal:8003` does not resolve
- Checks GitHub and finds the recent commit that modified `config.py` with the endpoint change
- Correlates the timeline: errors started after that commit was deployed
- Root cause: "Commit changed `PORTFOLIO_SERVICE_URL` to a non-existent internal hostname"
- Mitigation: revert the endpoint or provision the DNS record

## What the audience sees in the UI

- The app loads normally; price charts update (Market Data is fine)
- Try to **place an order** — the request hangs for several seconds, then fails
- A classic cascading failure: broken inter-service communication

## Scripts

- `inject.sh` — changes `PORTFOLIO_SERVICE_URL` to a non-existent host, commits, and pushes
- `fix.sh` — reverts to env-var config, commits, and pushes

## Usage

```bash
# Inject the failure (commits and pushes)
./demo/lab3-service-endpoint/inject.sh

# Wait for the pipeline to deploy (~3-5 min), then trigger an order from the UI
# or via curl:
curl -X POST "http://$ALB_DNS/api/orders" \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"test","symbol":"AAPL","side":"buy","type":"market","quantity":1}'

# Watch the alarm
aws cloudwatch describe-alarms \
  --alarm-names TradingApp-Order-ServiceTimeout \
  --query 'MetricAlarms[0].StateValue' --output text

# After investigation, fix it
./demo/lab3-service-endpoint/fix.sh
```

## Expected timeline

| T+ | Event |
|---|---|
| 0s | `inject.sh` commits and pushes |
| 1-3 min | Pipeline passes (test, build, deploy) |
| 3-5 min | New container deployed with the bad endpoint |
| 3-5 min | First order attempt -> `ConnectError` |
| 4-6 min | CloudWatch alarm triggers; webhook reaches AWS DevOps Agent |
| 5-10 min | Investigation complete; agent correlates the timeout with the commit |
