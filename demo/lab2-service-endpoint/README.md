# Lab 2 — Service Endpoint Misconfiguration

The `Order` service is updated with a new task definition where
`PORTFOLIO_SERVICE_URL` is overridden to a hostname that does not resolve.
Every order that triggers a portfolio check times out, log lines emit
`ConnectError` / `Name or service not known`, the
`TradingApp-Order-ServiceTimeout` CloudWatch alarm fires, the alarm SNS topic
invokes the webhook Lambda, and the AWS DevOps Agent investigates.

This lab uses **AWS APIs only**. It does not modify source code or push to
git, so it works against the public `aws-samples` deployment without a
participant fork.

## Flow

```
aws ecs update-service (new task def with bad PORTFOLIO_SERVICE_URL env)
  -> Order service starts on the new task definition
  -> Every portfolio call from the order path: DNS lookup fails
  -> Log lines emit "ConnectError" and "Name or service not known"
  -> CloudWatch metric filter increments OrderServiceTimeoutErrors
  -> Alarm: TradingApp-Order-ServiceTimeout fires
  -> SNS topic -> Lambda -> AWS DevOps Agent webhook
  -> Agent investigates
```

## What the agent does

- Reads the failing CloudWatch alarm and the metric filter that drives it
- Reads the Order service log group, identifies the connection-error pattern
- Reads the Order task definition's environment variables
- Identifies the `PORTFOLIO_SERVICE_URL` mismatch against the Portfolio
  service's actual ALB target
- Recommends rolling back to the previous task definition revision

## Data sources correlated

- CloudWatch alarms, metric filters, and CloudWatch Logs Insights queries
- ECS service / task definition environment overrides
- ALB target groups and listener rules (to identify the correct endpoint)
- CloudTrail (who issued the `ecs:UpdateService`, when)

## Expected output

Inline analysis: identifies the bad environment value, the offending task
definition revision, the previous-known-good revision, and the AWS CLI command
to roll back.

## Scripts

- `inject.sh` — registers a new task definition with
  `PORTFOLIO_SERVICE_URL=http://wrong.host:8003` and switches the `Order`
  service to it
- `fix.sh` — switches the service back to the previous task definition

## Prerequisites

Same as Lab 1: stack deployed, Module 0 webhook configured, AWS CLI access in
CloudShell.

## Usage

```bash
# Inject the failure
./demo/lab2-service-endpoint/inject.sh

# Trigger order traffic to surface the timeout (any order POST will work):
curl -X POST https://<your-cloudfront-domain>/api/orders \
     -H "Content-Type: application/json" \
     -d '{"symbol":"AAPL","quantity":1,"side":"buy","type":"market"}'

# Watch the agent's investigation in your DevOps Agent space
# (allow ~3-5 minutes for the alarm to fire and the webhook to deliver)

# Roll back when ready
./demo/lab2-service-endpoint/fix.sh
```
