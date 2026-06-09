# Lab 2: Runtime Failure — IAM Policy Deleted (DynamoDB Access Denied)

## Scenario
An IAM policy change removes DynamoDB write permissions from the ECS task role. The Market Data Service keeps running but fails every time it tries to write price ticks to DynamoDB — producing `AccessDeniedException` errors in CloudWatch Logs.

**Key difference from Lab 1**: This is a **runtime error**, not a pipeline failure. The trigger path is CloudWatch → EventBridge → Lambda → DevOps Agent webhook.

## Flow
```
IAM policy change (remove DynamoDB permissions)
  → Market Data Service writes fail
  → CloudWatch Logs: "AccessDeniedException"
  → Metric Filter catches pattern
  → CloudWatch Alarm triggers (≥1 error in 60s)
  → EventBridge rule fires
  → Lambda sends webhook to DevOps Agent
  → DevOps Agent auto-investigates
```

## What the DevOps Agent does
- Receives webhook (CloudWatch Alarm source)
- Reads CloudWatch Logs → sees "AccessDeniedException" for DynamoDB
- Checks the ECS task role's attached/inline policies
- Identifies that DynamoDB permissions are missing
- Produces mitigation spec: restore the inline policy with DynamoDB actions

## Data sources correlated
- CloudWatch Logs (error pattern)
- IAM (role policies)
- ECS (task definition → task role)

## AWS Resources Created
| Resource | Name/ARN |
|----------|----------|
| Metric Filter | `IAMAccessDenied` on market-data log group |
| CloudWatch Alarm | `TradingApp-IAM-AccessDenied` |
| EventBridge Rule | `TradingApp-IAMAlarm-ToDevOps` |
| Lambda Function | `TradingApp-DevOpsWebhook` |
| IAM Role (Lambda) | `DevOpsAgentWebhookLambdaRole` |

## Scripts
- `inject.sh` — Removes DynamoDB permissions from the ECS task role
- `fix.sh` — Restores DynamoDB permissions to the ECS task role
- `lambda_function.py` — Lambda code that sends HMAC-signed webhook to DevOps Agent

## Usage
```bash
# Inject the failure
./demo/lab2-iam-policy-deleted/inject.sh

# Watch for errors (wait 1-2 min for service to hit DynamoDB)
aws logs tail TradingAppStack-MarketDataTaskDefMarketDataContainerLogGroup741D6F0D-vhxYM5BrZ5Us \
  --follow --profile gfs-workshop --region us-east-1

# Check alarm state
aws cloudwatch describe-alarms --alarm-names TradingApp-IAM-AccessDenied \
  --profile gfs-workshop --region us-east-1 \
  --query 'MetricAlarms[0].StateValue'

# After investigation, fix it
./demo/lab2-iam-policy-deleted/fix.sh
```

## Expected Timeline
1. **T+0s**: inject.sh runs (DynamoDB permissions removed)
2. **T+30-120s**: Market Data Service attempts DynamoDB write → AccessDeniedException logged
3. **T+60-180s**: Metric filter counts ≥1 → Alarm enters ALARM state
4. **T+60-180s**: EventBridge fires → Lambda invokes → webhook sent to DevOps Agent
5. **T+180-300s**: DevOps Agent produces investigation report
