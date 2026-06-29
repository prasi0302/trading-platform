# Trading Platform demo labs

Three reproducible failure-injection scenarios used by **Module 1** of the
*Autonomous Incident Response with AWS DevOps Agent* workshop.

## Required labs (AWS-API only)

These two labs work against the public `aws-samples` deployment **without a
participant fork or any GitHub access**. They use AWS APIs to mutate the
deployed ECS service state and rely on the CloudWatch alarm chain wired by
`infra/trading_stack.py` to trigger the AWS DevOps Agent.

| Lab | Target | What breaks |
|---|---|---|
| `lab1-bad-deployment/` | `MarketData` ECS service | Task definition switched to a non-existent ECR image tag — deployment hangs, running tasks drain |
| `lab2-service-endpoint/` | `Order` ECS service | `PORTFOLIO_SERVICE_URL` env var overridden with a hostname that does not resolve — orders cascade-timeout |

Run from AWS CloudShell in the workshop account:

```bash
git clone https://github.com/aws-samples/sample-trading-devops-agent-workshop.git
cd sample-trading-devops-agent-workshop
./demo/lab1-bad-deployment/inject.sh
# observe agent investigation
./demo/lab1-bad-deployment/fix.sh
```

Each lab's `README.md` documents the failure mode, the alarm that fires, and
the data sources the agent correlates.

## Optional Lab (GitHub Actions correlation)

`optional-github/` contains the original git-driven labs. They demonstrate the
DevOps Agent correlating **GitHub commits and Actions runs** with AWS state,
which is a richer story than the AWS-API-only path. The trade-off: each
participant must:

1. Fork `aws-samples/sample-trading-devops-agent-workshop` to their personal
   GitHub.
2. Configure GitHub Actions secrets (`AWS_DEPLOY_ROLE_ARN`,
   `DEVOPS_AGENT_WEBHOOK_URL`, `DEVOPS_AGENT_WEBHOOK_SECRET`) and variables
   (per the README).
3. Trigger the first deployment from their fork.
4. Run `inject.sh` from a clone of their fork (which performs `sed`,
   `git commit`, `git push` against their fork — not against `aws-samples`).

Optional Lab is intentionally a single optional unit covering three
sub-scenarios:

| Sub-scenario | Failure mode |
|---|---|
| `optional-github/scenario-a-bad-build/` | Bad Dockerfile base image → GitHub Actions build job fails |
| `optional-github/scenario-b-bad-code-commit/` | Wrong DynamoDB table name → pipeline passes, runtime IAM AccessDenied |
| `optional-github/scenario-c-service-endpoint/` | Wrong service URL → cascading timeouts (git-pushed equivalent of required Lab 2) |

See each sub-scenario's `README.md` for the flow diagrams.

## Why is Lab 3 optional?

All three Module 1 labs (and Modules 2/3 in the wider workshop) demonstrate
the AWS DevOps Agent investigating a runtime incident triggered by a
CloudWatch alarm. Lab 3 *additionally* demonstrates the agent correlating
GitHub commits and Actions runs with the AWS state — a richer multi-system
story but one that requires per-participant GitHub setup. We made it optional
so the common workshop path stays uniform with Modules 2 and 3, while
participants who want the deeper demo can opt in.
