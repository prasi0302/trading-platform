#!/bin/bash
# Lab 1: Fix Bad Deployment — Switch MarketData service back to the previously
# known-good task definition saved by inject.sh. Used by the FSI Autonomous
# Incident Response workshop (Module 1, Lab 1).

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
STATE_DIR="${HOME}/.trading-app-lab1"
LAST_GOOD_FILE="$STATE_DIR/last-known-good-taskdef.txt"

echo "Lab 1: Fixing Bad Deployment — Restoring Previous Task Definition"
echo "================================================================="
echo

if [ ! -f "$LAST_GOOD_FILE" ]; then
    echo "  ERROR: $LAST_GOOD_FILE not found." >&2
    echo "  This script needs the task definition ARN that inject.sh saved." >&2
    echo "  If you ran inject.sh on another machine, set the ARN manually:" >&2
    echo "    echo 'arn:aws:ecs:...:task-definition/TradingAppStack-...:N' > $LAST_GOOD_FILE" >&2
    exit 1
fi

LAST_GOOD_TASK_DEF=$(cat "$LAST_GOOD_FILE")
echo "Restoring to: $LAST_GOOD_TASK_DEF"
echo

# Resolve cluster + service ARN exactly the same way as inject.sh
CLUSTER_ARN=$(aws ecs list-clusters --region "$REGION" \
    --query "clusterArns[?contains(@,'TradingCluster')]|[0]" --output text)
CLUSTER_NAME=$(echo "$CLUSTER_ARN" | awk -F/ '{print $NF}')

SERVICE_ARN=$(aws ecs list-services --region "$REGION" --cluster "$CLUSTER_NAME" \
    --query "serviceArns[?contains(@,'MarketDataService')]|[0]" --output text)
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
echo "  1. ECS pulls the working image"
echo "  2. New task starts within ~1-2 min"
echo "  3. Running task count returns to >=1"
echo "  4. Alarm 'TradingApp-MarketData-NoRunningTasks' returns to OK"

# Clean up state
rm -f "$LAST_GOOD_FILE"
rmdir "$STATE_DIR" 2>/dev/null || true
