#!/bin/bash
# Lab 1: Inject Bad Deployment — Switch MarketData service to a task definition
# that points at a non-existent ECR image tag. ECS deployment hangs, running
# tasks drain, the TradingApp-MarketData-NoRunningTasks CloudWatch alarm fires,
# and the AWS DevOps Agent investigates via the webhook chain. Used by the FSI
# Autonomous Incident Response workshop (Module 1, Lab 1).

set -euo pipefail

# Resolve cluster name and service ARN dynamically. Both are provisioned by
# the CDK stack and discoverable via the standard AWS APIs.

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"

echo "Lab 1: Injecting Bad Deployment — Non-existent ECR Image Tag"
echo "============================================================="
echo
echo "Target: MarketData ECS service in cluster TradingAppStack/TradingCluster"
echo "Region: $REGION"
echo

# -------------------------------------------------------------------------
# Resolve cluster + service ARN
# -------------------------------------------------------------------------
echo "[1/5] Locating ECS cluster and service..."

CLUSTER_ARN=$(aws ecs list-clusters --region "$REGION" \
    --query "clusterArns[?contains(@,'TradingCluster')]|[0]" --output text)

if [ -z "$CLUSTER_ARN" ] || [ "$CLUSTER_ARN" = "None" ]; then
    echo "  ERROR: could not find a TradingCluster ECS cluster in $REGION." >&2
    echo "  Make sure the Trading app stack is deployed in this account/region." >&2
    exit 1
fi

CLUSTER_NAME=$(echo "$CLUSTER_ARN" | awk -F/ '{print $NF}')

SERVICE_ARN=$(aws ecs list-services --region "$REGION" --cluster "$CLUSTER_NAME" \
    --query "serviceArns[?contains(@,'MarketDataService')]|[0]" --output text)

if [ -z "$SERVICE_ARN" ] || [ "$SERVICE_ARN" = "None" ]; then
    echo "  ERROR: could not find a MarketDataService in cluster $CLUSTER_NAME." >&2
    exit 1
fi

SERVICE_NAME=$(echo "$SERVICE_ARN" | awk -F/ '{print $NF}')

echo "  cluster: $CLUSTER_NAME"
echo "  service: $SERVICE_NAME"
echo

# -------------------------------------------------------------------------
# Capture the current task definition for rollback
# -------------------------------------------------------------------------
echo "[2/5] Capturing the current task definition (for rollback)..."

CURRENT_TASK_DEF=$(aws ecs describe-services --region "$REGION" \
    --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" \
    --query 'services[0].taskDefinition' --output text)

echo "  current task definition: $CURRENT_TASK_DEF"

# Persist for the fix script
STATE_DIR="${HOME}/.trading-app-lab1"
mkdir -p "$STATE_DIR"
echo "$CURRENT_TASK_DEF" > "$STATE_DIR/last-known-good-taskdef.txt"
echo "  saved to: $STATE_DIR/last-known-good-taskdef.txt"
echo

# -------------------------------------------------------------------------
# Build a new task definition with a bad image tag
# -------------------------------------------------------------------------
echo "[3/5] Registering a new task definition with a bad image tag..."

# Pull current task definition JSON, swap the image, drop the read-only fields,
# and register a new revision.
NEW_TASK_DEF_JSON=$(aws ecs describe-task-definition --region "$REGION" \
    --task-definition "$CURRENT_TASK_DEF" \
    --query 'taskDefinition' --output json | jq '
        .containerDefinitions[0].image =
            (.containerDefinitions[0].image | sub(":[^:/]*$"; ":nonexistent-image-tag"))
        | del(.taskDefinitionArn, .revision, .status, .requiresAttributes,
              .compatibilities, .registeredAt, .registeredBy)
    ')

NEW_TASK_DEF_ARN=$(aws ecs register-task-definition --region "$REGION" \
    --cli-input-json "$NEW_TASK_DEF_JSON" \
    --query 'taskDefinition.taskDefinitionArn' --output text)

echo "  new (bad) task definition: $NEW_TASK_DEF_ARN"
echo

# -------------------------------------------------------------------------
# Switch the service to the bad task definition
# -------------------------------------------------------------------------
echo "[4/5] Switching MarketData service to the bad task definition..."

aws ecs update-service --region "$REGION" \
    --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" \
    --task-definition "$NEW_TASK_DEF_ARN" \
    --force-new-deployment > /dev/null

echo "  switched."
echo

# -------------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------------
echo "[5/5] Done. Expected behavior:"
echo
echo "  1. ECS attempts to pull '$NEW_TASK_DEF_ARN' (manifest not found)"
echo "  2. The deployment hangs in IN_PROGRESS"
echo "  3. Running task count drops to 0 within ~1-2 min"
echo "  4. Alarm 'TradingApp-MarketData-NoRunningTasks' fires"
echo "  5. SNS -> webhook Lambda -> AWS DevOps Agent investigation"
echo
echo "Watch the agent's investigation in your DevOps Agent space."
echo "Roll back when ready:"
echo "    ./demo/lab1-bad-deployment/fix.sh"
