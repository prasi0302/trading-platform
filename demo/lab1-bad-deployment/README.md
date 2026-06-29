# Lab 1 — Bad Deployment: ECS pulls a non-existent image

A new task definition is registered for the `MarketData` service that points
to an ECR image tag the registry doesn't have. ECS rolls the deployment out,
fails to pull the image, and the running task count drains to zero. The
`TradingApp-MarketData-NoRunningTasks` CloudWatch alarm fires within ~2
minutes, the alarm SNS topic invokes the webhook Lambda, and the AWS DevOps
Agent investigates.

This lab uses **AWS APIs only**. It does not modify source code or push to
git, so it works against the public `aws-samples` deployment without a
participant fork.

## Flow

```
aws ecs update-service (new task def with bad image tag)
  -> ECS deployment IN_PROGRESS
  -> ECR pull fails ("image manifest not found")
  -> Running task count drops below 1
  -> CloudWatch alarm: TradingApp-MarketData-NoRunningTasks fires
  -> SNS topic -> Lambda -> AWS DevOps Agent webhook
  -> Agent investigates
```

## What the agent does

- Reads the failing CloudWatch alarm (alarm description and metric)
- Reads ECS service events (sees `CannotPullContainerError` / image-not-found)
- Reads the failing task definition's container image URI
- Reads ECR for the image's tag list
- Identifies the image tag mismatch
- Recommends rolling back to the previous task definition revision

## Data sources correlated

- CloudWatch alarms and ECS metrics
- ECS service / task / task definition state
- ECR image repository contents
- CloudTrail (who issued the `ecs:UpdateService` call, when)

## Expected output

Inline analysis: identifies the bad image tag, the offending task definition
revision, the previous-known-good revision, and the AWS CLI command to roll
back.

## Scripts

- `inject.sh` — registers a new task definition pointing at
  `:nonexistent-image-tag` and switches the `MarketData` service to it
- `fix.sh` — switches the service back to the previous task definition

## Prerequisites

- The Trading app stack is deployed (workshop provisioning step)
- The DevOps Agent webhook is configured in CDK context (Module 0)
- AWS credentials with `ecs:DescribeServices`, `ecs:DescribeTaskDefinition`,
  `ecs:RegisterTaskDefinition`, `ecs:UpdateService` (the workshop participant
  role has these by default in CloudShell)

## Usage

Open AWS CloudShell in the workshop account, then:

```bash
git clone https://github.com/aws-samples/sample-trading-devops-agent-workshop.git
cd sample-trading-devops-agent-workshop

# Inject the failure
./demo/lab1-bad-deployment/inject.sh

# Watch the agent's investigation in your DevOps Agent space
# (allow ~3-5 minutes for the alarm to fire)

# Roll back when ready
./demo/lab1-bad-deployment/fix.sh
```
