# Trading Platform — AWS DevOps Agent sample application

A real-time stock trading microservices application that demonstrates [AWS DevOps Agent](https://docs.aws.amazon.com/devopsagent/latest/userguide/) autonomous incident response. It powers Module 1 of the **Autonomous Incident Response with AWS DevOps Agent** workshop, alongside the [ClaimFlow](https://github.com/aws-samples/sample-claimflow-devops-agent-workshop) and [PaymentPro](https://github.com/aws-samples/sample-paymentpro-devops-agent-workshop) sample applications.

The repository contains:

- **Six microservices** (Python/FastAPI) and a **React/TypeScript dashboard**, deployed to **Amazon ECS Fargate**
- **AWS CDK** infrastructure in `infra/` (VPC, ALB, RDS, ElastiCache, DynamoDB, S3, CloudFront, CloudWatch alarms, SNS topic, and a webhook Lambda)
- **GitHub Actions** CI/CD with OIDC federation in `.github/workflows/deploy.yml` (used by the optional GitHub-correlation lab)
- **Demo lab scripts** in `demo/` that intentionally inject failures so the AWS DevOps Agent can investigate them

> **Note**: This sample is for **demonstration and learning purposes**. It is not intended for production use as-is. Review the [Security](#security) and [Known limitations](#known-limitations) sections before deploying.

## Architecture

```
                                     +--------------+
                                     |  CloudFront  |
                                     +-------+------+
                                             |
                                             v
+-----------+      +-------+         +-------+--------+
|  Browser  +----->+  ALB  +-------->+  ECS Fargate   |
+-----------+      +---+---+         |  6 microservices|
                       |             +---+--------+---+
                       |                 |        |
                       |          +------+--+  +--+------+
                       |          |  Redis  |  | Postgres|
                       |          +---------+  +---------+
                       |                 |
                       v                 v
              +--------+--------+   +----+-----+
              |   DynamoDB      |   |    S3    |
              +-----------------+   +----------+

  CloudWatch alarm -----> SNS topic -----> Lambda -----> AWS DevOps Agent webhook
```

| Service | Port | Description |
|---|---|---|
| API Gateway | 8000 | REST request routing |
| Market Data | 8001 | Simulated price generation (geometric Brownian motion) |
| Order | 8002 | Order lifecycle management |
| Portfolio | 8003 | Portfolio tracking and P&L |
| Alert | 8004 | Price alert monitoring |
| WebSocket Gateway | 8005 | Real-time event streaming |

## Prerequisites

- An AWS account with administrator access
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), configured
- [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) (`npm install -g aws-cdk`)
- Node.js 20+ (for the frontend and CDK)
- Python 3.11+ (for services and CDK)
- Docker (for building service images locally — optional)
- A GitHub account is required **only** for the optional Lab 3 (GitHub Actions correlation). Labs 1 and 2 do not need GitHub.

## Deploy

### 1. Bootstrap and deploy the CDK stack

```bash
cd infra
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap aws://<ACCOUNT_ID>/<REGION>

# Optional: configure DevOps Agent webhook integration
cdk deploy \
  -c devops_agent_webhook_url="<your-devops-agent-webhook-url>" \
  -c devops_agent_webhook_secret="<your-devops-agent-webhook-secret>"

# Or deploy without the webhook (Lambda short-circuits at invocation):
cdk deploy
```

The deployment takes about 12-18 minutes. Note the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name TradingAppStack \
  --query "Stacks[0].Outputs" \
  --output table
```

Key outputs:

- `CloudFrontUrl` — the public application URL
- `EcsClusterName` — used by the pipeline to deploy
- `GitHubDeployRoleArn` — the OIDC role for the optional Lab 3 GitHub Actions workflow
- `FrontendBucketName`, `DistributionId`, `AlbUrl`
- `WebhookLambdaName`, `AlarmTopicArn`

### 2. Sync the frontend SPA

The CDK provisions the S3 frontend bucket but does not deploy assets to it. After the stack is created, build and sync the frontend:

```bash
cd ../frontend
npm ci
npm run build
aws s3 sync dist/ s3://<FrontendBucketName>/ --delete
aws cloudfront create-invalidation \
  --distribution-id <DistributionId> --paths "/*"
```

Open the `CloudFrontUrl` in your browser to see live price updates.

### 3. (Optional) Set up the GitHub Actions path for Lab 3

If you intend to do the optional Lab 3 (GitHub Actions correlation), fork this repository and configure the following in your fork's **Settings** > **Secrets and variables** > **Actions**.

**Secrets:**

| Name | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `GitHubDeployRoleArn` from the CDK output |
| `DEVOPS_AGENT_WEBHOOK_URL` | The webhook URL from your AWS DevOps Agent space |
| `DEVOPS_AGENT_WEBHOOK_SECRET` | The webhook secret from your AWS DevOps Agent space |

**Variables:**

| Name | Value |
|---|---|
| `AWS_REGION` | `us-east-1` (or your deployment region) |
| `ECR_REGISTRY` | `<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com` |
| `ECS_CLUSTER` | `EcsClusterName` from the CDK output |
| `ALB_DNS` | The DNS portion of `AlbUrl` (without `http://`) |
| `CF_URL` | `CloudFrontUrl` from the CDK output |
| `FRONTEND_BUCKET` | `FrontendBucketName` from the CDK output |
| `CF_DISTRIBUTION_ID` | `DistributionId` from the CDK output |

Trigger the first deployment from your fork to verify the wiring:

```bash
git commit --allow-empty -m "trigger initial deployment"
git push origin main
```

Watch the **Actions** tab. Subsequent pushes to `main` redeploy automatically; that's what the optional Lab 3 inject scripts rely on.

## Local development

A `docker-compose.yml` is included for running individual services against local Redis and LocalStack:

```bash
cp .env.example .env       # adjust values as needed
docker compose up -d redis localstack
docker compose up market-data
```

See `services/<name>/README.md` for per-service local development notes.

> **Note**: services that talk to the database (`order`, `portfolio`, `alert`) require `DB_PASSWORD` to be set in your environment for local development. In production, `DB_PASSWORD` is injected via the ECS task definition's `secrets` block from AWS Secrets Manager and you do not set it manually.

## Demo labs

The `demo/` directory contains three failure-injection scenarios. Two are required and run via AWS APIs only; the third is optional and uses GitHub Actions to demonstrate the agent's git-history correlation capability.

### Required Lab 1 — Bad deployment (`demo/lab1-bad-deployment/`)

Switches the `MarketData` ECS service to a task definition pointing at a non-existent ECR image tag. The deployment hangs, running tasks drain, the `TradingApp-MarketData-NoRunningTasks` CloudWatch alarm fires, and the agent investigates.

### Required Lab 2 — Service endpoint misconfiguration (`demo/lab2-service-endpoint/`)

Overrides the `Order` service's `PORTFOLIO_SERVICE_URL` env var with a hostname that does not resolve. Orders cascade-timeout, the `TradingApp-Order-ServiceTimeout` alarm fires, and the agent investigates.

### Optional Lab 3 — GitHub Actions correlation (`demo/optional-github/`)

Three sub-scenarios that demonstrate the agent correlating GitHub commits and Actions runs with AWS state. Requires a forked repo and per-fork GitHub Actions secrets (see [step 3](#3-optional-set-up-the-github-actions-path-for-lab-3)). Sub-scenarios:

- `scenario-a-bad-build/` — bad Dockerfile base image; GitHub Actions build fails
- `scenario-b-bad-code-commit/` — wrong DynamoDB table name; pipeline passes, runtime IAM AccessDenied
- `scenario-c-service-endpoint/` — wrong service URL; cascading timeouts (git-pushed equivalent of required Lab 2)

See `demo/README.md` for the structure and `demo/<lab>/README.md` for individual lab flow diagrams.

## Cleanup

To tear down all resources created by `cdk deploy`:

```bash
cd infra && cdk destroy --force
```

The CDK destroys the CloudWatch alarms, SNS topic, the webhook Lambda, and (when configured) the Secrets Manager webhook secret along with the application stack.

## Estimated cost

Approximate monthly cost in `us-east-1` while the stack is running (workshop-defaults: single-AZ, smallest practical instance sizes):

| Component | Approximate monthly cost (USD) |
|---|---|
| NAT Gateway (1) | $33 |
| RDS PostgreSQL `db.t3.micro` (single-AZ, 20 GB gp3) | $15 |
| ElastiCache Redis `cache.t3.micro` (1 node) | $12 |
| 5 Fargate services (0.25 vCPU / 0.5 GB each, 24×7) | $36 |
| ALB | $17 |
| CloudFront + S3 (minimal traffic) | $1–$5 |
| CloudWatch logs / alarms / metrics | $2–$5 |
| **Total** | **~$120/month** |

These are list-price estimates for an idle deployment with no participant traffic; real workshop usage stays in the same band because the simulator is synthetic. Terminate the stack with `cdk destroy --force` when not in use to avoid charges.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for information about reporting security issues.

This sample uses simulated market data and is intended for demonstration. When adapting it, you should:

- Restrict the API Gateway CORS allowlist via the `CORS_ALLOWED_ORIGINS` environment variable (the default is local development origins only).
- Tighten the GitHub OIDC trust to your specific fork. The CDK defaults to `repo:*:ref:refs/heads/main` (any GitHub repo) so workshop participants can deploy without modification, but a production deployment should narrow it. Override at deploy time:

  ```bash
  cdk deploy -c github_repo_pattern="repo:<OWNER>/<REPO>:ref:refs/heads/main"
  ```

- Add WAF or authentication to the public ALB and CloudFront distribution.
- Pin Docker base images to digests for production reproducibility (see Known limitations below).

## Known limitations

This is sample code optimized for ease of reading and short-lived demo use. The following items are known and accepted in that context; harden them before any production use:

- **Public ALB serves HTTP only (no HTTPS).** The ALB security group allows `0.0.0.0/0` on port 80 and the ALB has no HTTPS listener; CloudFront fronts the ALB and customer-facing traffic uses CloudFront's default HTTPS, but ALB-direct traffic is unencrypted. Add an ACM certificate and an HTTPS-only listener for production.
- **No application-level authentication.** Order placement, portfolio queries, and price-alert configuration accept any caller that reaches the public ALB. Add API Gateway authoriser or Cognito before exposing the deployment beyond a sandbox account.
- **GitHub OIDC trust pattern is `repo:*:ref:refs/heads/main` by default.** This intentionally accepts deployments from any fork on the `main` branch so workshop participants can deploy without modification. Narrow it via the `github_repo_pattern` CDK context variable (see Security section above) before any non-workshop use.
- **Dockerfile base images are not SHA-pinned.** Each `Dockerfile` uses a floating tag (for example `python:3.11-slim`, `node:20-alpine`, `nginx:alpine`) rather than `<image>@sha256:...`. Container builds are therefore reproducible only as long as the upstream tag is stable. Pin to digests if you fork this for a longer-lived environment.
- **Vite dev-server advisory (`GHSA-4w7w-66w2-5vf9`).** The frontend pins Vite to 5.4.x for stability; the path-traversal fix in `.map` handling lands in Vite 6.4.3+ (a major-version bump). Vite is a development-only dependency — it is not in the production container image, which ships the pre-built static bundle via nginx. Bump to Vite 7.x when forking for active development.
- **`pytest` `tmpdir` advisory (CVE-2025-71176).** All services include `pytest` in their `[dev]` extras. The advisory is upstream-unfixed at the time of writing (see [pytest-dev/pytest#13669](https://github.com/pytest-dev/pytest/issues/13669)) and reflects a local-privilege-escalation race against `/tmp/pytest-of-{user}` on multi-user UNIX hosts. `pytest` is a development-only dependency — it is not installed in the production container images — so the advisory does not apply to the deployed application. Run tests on a single-user workstation or CI runner to avoid the local-attacker scenario.
- **Workshop-only configuration.** The CDK uses `removal_policy=DESTROY` and `deletion_protection=False` on RDS, DynamoDB, and the frontend S3 bucket so the stack tears down cleanly between demos. Flip these to `RETAIN` and enable RDS deletion protection before running the stack against any data you care about.
- **Local development uses LocalStack with literal `test`/`test` AWS credentials.** The `.env.example` and `docker-compose.yml` set `AWS_ACCESS_KEY_ID=test` and `AWS_SECRET_ACCESS_KEY=test` — these are LocalStack's documented stub values, not real credentials. Production deployments use the IAM task roles provisioned by the CDK; no static AWS credentials are needed at runtime.
- **Demo lab scripts intentionally degrade the running app.** Scripts under `demo/lab*/` and `demo/optional-github/scenario-*/` modify the deployed ECS service state (Labs 1 and 2 via AWS APIs) or push code changes that trigger pipeline failures (optional Lab 3 via git). Each lab includes a matching `fix.sh` that reverts the change. Run only against a dedicated demo / sandbox account.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
