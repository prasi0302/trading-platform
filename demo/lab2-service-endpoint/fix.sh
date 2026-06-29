#!/bin/bash
# Lab 2: Fix Service Endpoint Misconfiguration — Switch Order service back to
# the previously known-good task definition saved by inject.sh. Used by the FSI
# Autonomous Incident Response workshop (Module 1, Lab 2).

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
STATE_DIR="${HOME}/.trading-app-lab2"
LAST_GOOD_FILE="$STATE_DIR/last-known-good-taskdef.txt"

echo "Lab 2: Fixing Service Endpoint Misconfiguration"
echo "================================================"
echo

if [ ! -f "$LAST_GOOD_FILE" ]; then
    echo "  ERROR: $LAST_GOOD_FILE not found." >&2
    echo "  This script needs the task definition ARN that inject.sh saved." >&2
    exit 1
fi

LAST_GOOD_TASK_DEF=$(cat "$LAST_GOOD_FILE")
echo "Restoring to: $LAST_GOOD_TASK_DEF"
echo

CLUSTER_ARN=$(aws ecs list-clusters --region "$REGION" \
    --query "clusterArns[?contains(@,'TradingCluster')]|[0]" --output text)
CLUSTER_NAME=$(echo "$CLUSTER_ARN" | awk -F/ '{print $NF}')

SERVICE_ARN=$(aws ecs list-services --region "$REGION" --cluster "$CLUSTER_NAME" \
    --query "serviceArns[?contains(@,'OrderService') && !contains(@,'WsGateway')]|[0]" --output text)
SERVICE_NAME=$(echo "$SERVICE_ARN" | awk -F/ '{print $NF}')

echo "  cluster: $CLUSTER_NAME"
echo "  service: $SERVICE_NAME"
echo

aws ecs update-service --region "$REGION" \
    --cluster "$CLUSTER_NAME" --service "$SERVICE_NAME" \
    --task-definition "$LAST_GOOD_TASK_DEF" \
    --force-new-deployment > /dev/null

echo "Switched back to the previous task definition."
echo
echo "Expected recovery:"
echo "  1. New Order task starts with the correct PORTFOLIO_SERVICE_URL"
echo "  2. Orders that call portfolio start succeeding within ~1-2 min"
echo "  3. Alarm 'TradingApp-Order-ServiceTimeout' returns to OK"

rm -f "$LAST_GOOD_FILE"
rmdir "$STATE_DIR" 2>/dev/null || true
