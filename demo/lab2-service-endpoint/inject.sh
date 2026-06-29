#!/bin/bash
# Lab 2: Inject Service Endpoint Misconfiguration — Override Order service's
# PORTFOLIO_SERVICE_URL environment variable with a hostname that does not
# resolve, causing cascading timeouts. Used by the FSI Autonomous Incident
# Response workshop (Module 1, Lab 2).

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
BAD_URL="http://wrong.host:8003"

echo "Lab 2: Injecting Service Endpoint Misconfiguration"
echo "==================================================="
echo
echo "Target: Order ECS service in cluster TradingAppStack/TradingCluster"
echo "Region: $REGION"
echo "Override: PORTFOLIO_SERVICE_URL=$BAD_URL"
echo

# -------------------------------------------------------------------------
# Resolve cluster + service ARN
# -------------------------------------------------------------------------
echo "[1/5] Locating ECS cluster and service..."

CLUSTER_ARN=$(aws ecs list-clusters --region "$REGION" \
    --query "clusterArns[?contains(@,'TradingCluster')]|[0]" --output text)

if [ -z "$CLUSTER_ARN" ] || [ "$CLUSTER_ARN" = "None" ]; then
    echo "  ERROR: could not find a TradingCluster ECS cluster in $REGION." >&2
    exit 1
fi

CLUSTER_NAME=$(echo "$CLUSTER_ARN" | awk -F/ '{print $NF}')

SERVICE_ARN=$(aws ecs list-services --region "$REGION" --cluster "$CLUSTER_NAME" \
    --query "serviceArns[?contains(@,'OrderService') && !contains(@,'WsGateway')]|[0]" --output text)

if [ -z "$SERVICE_ARN" ] || [ "$SERVICE_ARN" = "None" ]; then
    echo "  ERROR: could not find an OrderService in cluster $CLUSTER_NAME." >&2
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

STATE_DIR="${HOME}/.trading-app-lab2"
mkdir -p "$STATE_DIR"
echo "$CURRENT_TASK_DEF" > "$STATE_DIR/last-known-good-taskdef.txt"
echo "  saved to: $STATE_DIR/last-known-good-taskdef.txt"
echo

# -------------------------------------------------------------------------
# Build a new task definition with overridden PORTFOLIO_SERVICE_URL
# -------------------------------------------------------------------------
echo "[3/5] Registering a new task definition with bad PORTFOLIO_SERVICE_URL..."

NEW_TASK_DEF_JSON=$(aws ecs describe-task-definition --region "$REGION" \
    --task-definition "$CURRENT_TASK_DEF" \
    --query 'taskDefinition' --output json | jq --arg URL "$BAD_URL" '
        .containerDefinitions[0].environment = (
            (.containerDefinitions[0].environment // [])
            | map(select(.name != "PORTFOLIO_SERVICE_URL"))
            | . + [{"name": "PORTFOLIO_SERVICE_URL", "value": $URL}]
        )
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
echo "[4/5] Switching Order service to the bad task definition..."

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
echo "  1. New Order task starts in ~1-2 min with the bad env value"
echo "  2. Every order that calls portfolio fails with DNS error"
echo "  3. Log lines emit 'ConnectError' / 'Name or service not known'"
echo "  4. Metric filter increments TradingApp/OrderServiceTimeoutErrors"
echo "  5. Alarm 'TradingApp-Order-ServiceTimeout' fires within ~1-2 min"
echo "     after the first failed order"
echo "  6. SNS -> webhook Lambda -> AWS DevOps Agent investigation"
echo
echo "Tip: trigger an order via the UI or curl to surface the failure faster."
echo
echo "Roll back when ready:"
echo "    ./demo/lab2-service-endpoint/fix.sh"
