# Lab 3: Bad Code Commit — Wrong DynamoDB Table Name (Pipeline Passes, Runtime Fails)

## Scenario
A developer "refactors" the Market Data Service and accidentally hardcodes a wrong DynamoDB table name. The pipeline passes (unit tests mock DynamoDB), the deploy succeeds, but the service can't write price ticks at runtime — producing `AccessDeniedException` because the IAM policy only grants access to the original table.

**Key difference from Lab 2**: This is a **code-level failure** triggered by a git commit. The DevOps Agent correlates the runtime error with the specific commit that caused it.

## Flow
```
Bad commit (hardcodes wrong table name)
  → Pipeline passes (tests mock DynamoDB)
  → Deploy succeeds (container starts fine)
  → Service tries to write to 'market-data-ticks-v2'
  → IAM denies access (policy only allows 'market-data-ticks')
  → CloudWatch Logs: "AccessDeniedException"
  → Metric Filter → CloudWatch Alarm → EventBridge → Lambda → DevOps Agent
  → Agent investigates: reads logs + checks recent GitHub commits
  → Root cause: commit changed table name, IAM policy doesn't cover new table
```

## What the DevOps Agent does
- Receives webhook (CloudWatch Alarm source)
- Reads CloudWatch Logs → sees "AccessDeniedException" for DynamoDB
- Notes the table name in error is 'market-data-ticks-v2' (not the expected table)
- Checks GitHub → sees recent commit that modified `config.py` with table name change
- **Correlates timeline**: errors started immediately after that commit was deployed
- Root cause: "Commit `abc123` changed DynamoDB table name to one not covered by IAM policy"
- Mitigation: revert the commit or update IAM policy

## What the audience sees in the UI
- The app loads normally
- Price charts **stop updating** (stale/frozen data)
- Subtle degradation — not a hard crash

## Data sources correlated
- CloudWatch Logs (error pattern + table name in error message)
- GitHub (recent commit diff showing the table name change)
- IAM (policy only allows original table)

## Scripts
- `inject.sh` — Changes table name in code, commits, pushes (triggers pipeline + deploy)
- `fix.sh` — Reverts the commit, pushes (triggers clean deploy)

## Usage
```bash
# Inject the failure (commits and pushes)
./demo/lab3-bad-code-commit/inject.sh

# Wait for pipeline to pass + deploy (~3-5 min)
# Then errors start appearing in CloudWatch Logs

# Watch for alarm
aws cloudwatch describe-alarms --alarm-names TradingApp-IAM-AccessDenied \
  --profile gfs-workshop --region us-east-1 --query 'MetricAlarms[0].StateValue'

# After investigation, fix it (commits and pushes)
./demo/lab3-bad-code-commit/fix.sh
```

## Expected Timeline
1. **T+0s**: inject.sh commits + pushes
2. **T+1-3min**: Pipeline passes (test → build → deploy)
3. **T+3-5min**: New container deployed, starts writing to wrong table
4. **T+3-5min**: AccessDeniedException errors appear in logs
5. **T+4-6min**: CloudWatch Alarm triggers → webhook → DevOps Agent
6. **T+5-10min**: Agent investigation complete — correlates error with the commit
