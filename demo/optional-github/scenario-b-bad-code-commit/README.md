# Lab 2 — Bad code commit: wrong DynamoDB table name (pipeline passes, runtime fails)

A developer "refactors" the Market Data service and accidentally hardcodes a wrong DynamoDB table name. The pipeline passes (unit tests mock DynamoDB), the deploy succeeds, but at runtime the service can't write price ticks because the IAM policy only grants access to the original table. The result is a stream of `AccessDeniedException` errors.

This is a **code-level failure** triggered by a git commit. The agent's job is to correlate the runtime error with the specific commit that caused it.

## Flow

```
Bad commit (hardcodes wrong table name)
  -> Pipeline passes (tests mock DynamoDB)
  -> Deploy succeeds (container starts fine)
  -> Service tries to write to 'market-data-ticks-v2'
  -> IAM denies access (policy only allows 'market-data-ticks')
  -> CloudWatch logs: "AccessDeniedException"
  -> Metric filter -> CloudWatch alarm -> EventBridge -> Lambda -> AWS DevOps Agent
  -> Agent investigates: reads logs and recent GitHub commits
  -> Root cause: commit changed the table name; IAM policy does not cover it
```

## What the agent does

- Receives the webhook (CloudWatch alarm source)
- Reads CloudWatch logs and notes the table name in the error message is `market-data-ticks-v2`
- Checks GitHub and finds the recent commit that modified `config.py` with the table name change
- Correlates the timeline: errors started immediately after that commit was deployed
- Root cause: "Commit `<sha>` changed the DynamoDB table name to one not covered by the IAM policy"
- Mitigation: revert the commit or update the IAM policy

## What the audience sees in the UI

- The app loads normally
- Price charts **stop updating** (stale, frozen data)
- Subtle degradation, not a hard crash

## Data sources correlated

- CloudWatch logs (error pattern + table name in error message)
- GitHub (recent commit diff showing the table name change)
- IAM (policy only allows the original table)

## Scripts

- `inject.sh` — changes the table name in code, commits, and pushes (triggers pipeline + deploy)
- `fix.sh` — reverts the commit and pushes (triggers a clean deploy)

## Usage

```bash
# Inject the failure (commits and pushes)
./demo/lab2-bad-code-commit/inject.sh

# Wait for the pipeline to pass + deploy (~3-5 min); errors start appearing.

# Watch the alarm
aws cloudwatch describe-alarms \
  --alarm-names TradingApp-IAM-AccessDenied \
  --query 'MetricAlarms[0].StateValue' \
  --output text

# After investigation, fix it
./demo/lab2-bad-code-commit/fix.sh
```

## Expected timeline

| T+ | Event |
|---|---|
| 0s | `inject.sh` commits and pushes |
| 1-3 min | Pipeline passes (test, build, deploy) |
| 3-5 min | New container deployed; starts writing to the wrong table |
| 3-5 min | `AccessDeniedException` errors appear in logs |
| 4-6 min | CloudWatch alarm triggers; webhook reaches AWS DevOps Agent |
| 5-10 min | Investigation complete; agent correlates the error with the commit |
