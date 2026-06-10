# AWS DevOps Agent Workshop

A hands-on workshop demonstrating how AWS DevOps Agent autonomously investigates and identifies root causes of operational incidents across a microservices trading platform.

## What You'll Learn

- How AWS DevOps Agent correlates telemetry from CloudWatch, IAM, and GitHub
- Different failure modes: build failures, IAM issues, code defects, service discovery problems
- End-to-end incident response: detect → alert → investigate → root cause → mitigation plan

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  GitHub     │────▶│ GitHub       │────▶│  ECS Fargate     │
│  (Code)     │     │ Actions CI/CD│     │  (6 services)    │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ DevOps Agent│◀────│  Lambda      │◀────│ EventBridge      │
│ (Investigates)    │  (Webhook)   │     │ (Routes alarms)  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │ CloudWatch       │
                                          │ (Logs + Alarms)  │
                                          └─────────────────┘
```

## Labs Overview

| Lab | Failure Type | Trigger | What Agent Finds |
|-----|-------------|---------|-----------------|
| 1 | Bad Docker image | Pipeline fails | Identifies bad image tag in commit |
| 2 | IAM policy removed | Runtime (CLI) | Missing DynamoDB permissions on task role |
| 3 | Wrong DynamoDB table | Runtime (code commit) | Correlates error with specific commit |
| 4 | Wrong service endpoint | Runtime (code commit) | Cascading timeouts + commit correlation |

---

## Prerequisites

- AWS account with admin access
- AWS CLI v2 installed and configured
- Node.js 20+ (for CDK and frontend)
- Python 3.11+ (for CDK and services)
- Docker (for building service images)
- GitHub account (for pipeline + DevOps Agent integration)
- AWS CDK CLI (`npm install -g aws-cdk`)

---

## Setup (One-Time, ~30 minutes)

### Step 1: Fork and Clone the Repository

```bash
# Fork this repo to your GitHub account, then:
git clone https://github.com/YOUR_USERNAME/trading-platform.git
cd trading-platform
```

### Step 2: Deploy the Trading Application (CDK)

```bash
cd infra
pip install -r requirements.txt
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
cdk deploy
```

Note the CDK outputs — you'll need the ECS cluster name, service names, ALB DNS, log group names, etc.

### Step 3: Configure GitHub Actions

1. Go to your fork → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `AWS_ACCESS_KEY_ID` — IAM user with ECR push + ECS deploy permissions
   - `AWS_SECRET_ACCESS_KEY` — corresponding secret key
3. Update `.github/workflows/deploy.yml` with your CDK output values (ECR registry, ECS cluster/service names, ALB DNS, etc.)

### Step 4: Set Up AWS DevOps Agent

Follow the [official documentation](https://docs.aws.amazon.com/devopsagent/latest/userguide/getting-started-with-aws-devops-agent-creating-an-agent-space.html) to:

1. **Create an Agent Space** — name it something descriptive (e.g., "TradingApp")
2. **Connect your AWS account** — Capabilities → Cloud Accounts → add your account + region
3. **Connect GitHub** — Capabilities → Pipeline → Add → GitHub → authorize and select your fork
4. **Create a Webhook** — Capabilities → Webhooks → Add → save the URL and secret

Reference: [Building an end-to-end agentic SRE using AWS DevOps Agent](https://aws.amazon.com/blogs/devops/building-an-end-to-end-agentic-sre-using-aws-devops-agent/)

### Step 5: Configure Workshop Settings

```bash
cp setup/config.env.example setup/config.env
# Edit setup/config.env with your values from Steps 2-4
```

### Step 6: Deploy Lab Infrastructure

```bash
chmod +x setup/deploy-lab-infra.sh
./setup/deploy-lab-infra.sh
```

This creates: CloudWatch metric filters, alarms, EventBridge rules, and the Lambda webhook function.

### Step 7: Verify Setup

- [ ] Trading app is running (visit your ALB DNS in browser)
- [ ] GitHub Actions pipeline passes on push
- [ ] DevOps Agent space shows "Connected" for AWS account and GitHub
- [ ] Webhook URL and secret are in `config.env`

---

## Running the Labs

### Lab 1: Build Failure — Bad Docker Image

**Story**: A developer changes the Dockerfile base image to one that doesn't exist.

```bash
./demo/lab1-dockerfile-bad-image/inject.sh
```

**What happens**: Pipeline fails at build stage → GitHub Actions failure webhook → DevOps Agent investigates → identifies bad image tag in commit diff.

**Fix**:
```bash
./demo/lab1-dockerfile-bad-image/fix.sh
```

---

### Lab 2: Runtime Failure — IAM Policy Deleted

**Story**: An IAM change removes DynamoDB permissions. Service keeps running but can't write data.

```bash
./demo/lab2-iam-policy-deleted/inject.sh
```

**What happens**: Errors appear in 1-2 min → CloudWatch Alarm → EventBridge → Lambda → DevOps Agent → reads logs, checks IAM → identifies missing policy.

**Fix**:
```bash
./demo/lab2-iam-policy-deleted/fix.sh
```

---

### Lab 3: Bad Code Commit — Wrong DynamoDB Table Name

**Story**: A developer "refactors" and hardcodes a wrong table name. Pipeline passes but runtime fails.

```bash
./demo/lab3-bad-code-commit/inject.sh
```

**What happens**: Pipeline passes → deploy → AccessDeniedException on wrong table → Alarm → DevOps Agent → **correlates the error with the git commit that caused it**.

**UI symptom**: Price charts stop updating (stale data).

**Fix**:
```bash
./demo/lab3-bad-code-commit/fix.sh
```

---

### Lab 4: Service Discovery Failure — Cascading Timeouts

**Story**: A developer updates a service endpoint to a non-existent internal hostname.

```bash
./demo/lab4-service-endpoint/inject.sh
```

**What happens**: Pipeline passes → deploy → Order Service can't reach Portfolio Service → orders fail → Alarm → DevOps Agent → correlates with commit.

**UI symptom**: Placing orders fails (shows "Insufficient funds" because portfolio check returns $0).

**Fix**:
```bash
./demo/lab4-service-endpoint/fix.sh
```

---

## Cleanup

```bash
# Remove lab infrastructure (keeps trading app running)
./setup/teardown-lab-infra.sh

# Destroy trading app entirely
cd infra && cdk destroy
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Alarm doesn't fire | Check metric filter matches log group name. Wait 60-90s for metric evaluation. |
| Lambda not invoked | Verify EventBridge rule has Lambda permission (`aws lambda get-policy`) |
| DevOps Agent shows "Pending" | Wait 2-5 min. Agent investigations can take time to start. |
| Pipeline fails on push | Check GitHub Secrets are set. Verify ECR/ECS names in deploy.yml. |
| Orders still work after Lab 4 inject | Wait for pipeline to deploy new container (~3-5 min) |

---

## Cost Estimate

Running this workshop costs approximately:
- ECS Fargate (6 services): ~$15/day
- RDS PostgreSQL (if used): ~$2/day
- ElastiCache Redis: ~$3/day
- DynamoDB: ~$1/day
- DevOps Agent: Free trial (first 2 months)
- **Total: ~$20-25/day**

Tear down after the workshop to avoid ongoing charges.
