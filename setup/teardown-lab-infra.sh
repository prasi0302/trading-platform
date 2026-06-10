#!/bin/bash
# =============================================================================
# AWS DevOps Agent Workshop — Teardown Lab Infrastructure
# =============================================================================
# Removes all resources created by deploy-lab-infra.sh
# Does NOT destroy the CDK stack (trading app itself).
#
# Usage: ./setup/teardown-lab-infra.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load config
if [ ! -f "$SCRIPT_DIR/config.env" ]; then
    echo "❌ config.env not found."
    exit 1
fi
source "$SCRIPT_DIR/config.env"

echo "🧹 Tearing Down Lab Infrastructure"
echo "===================================="
echo ""

# EventBridge rules
echo "Removing EventBridge rules..."
aws events remove-targets --rule "TradingApp-IAMAlarm-ToDevOps" --ids DevOpsWebhookLambda --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
aws events delete-rule --name "TradingApp-IAMAlarm-ToDevOps" --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
aws events remove-targets --rule "TradingApp-OrderTimeout-ToDevOps" --ids DevOpsWebhookLambda --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
aws events delete-rule --name "TradingApp-OrderTimeout-ToDevOps" --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
echo "  ✅ EventBridge rules removed"

# Lambda
echo "Removing Lambda function..."
aws lambda delete-function --function-name TradingApp-DevOpsWebhook --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
echo "  ✅ Lambda removed"

# IAM role
echo "Removing IAM role..."
aws iam detach-role-policy --role-name TradingApp-WebhookLambdaRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --profile "$AWS_PROFILE" 2>/dev/null || true
aws iam delete-role --role-name TradingApp-WebhookLambdaRole --profile "$AWS_PROFILE" 2>/dev/null || true
echo "  ✅ IAM role removed"

# CloudWatch alarms
echo "Removing CloudWatch alarms..."
aws cloudwatch delete-alarms --alarm-names "TradingApp-IAM-AccessDenied" "TradingApp-Order-ServiceTimeout" --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
echo "  ✅ Alarms removed"

# Metric filters
echo "Removing metric filters..."
aws logs delete-metric-filter --log-group-name "$MARKET_DATA_LOG_GROUP" --filter-name "IAMAccessDenied" --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
aws logs delete-metric-filter --log-group-name "$ORDER_LOG_GROUP" --filter-name "OrderServiceConnectTimeout" --profile "$AWS_PROFILE" --region "$AWS_REGION" 2>/dev/null || true
echo "  ✅ Metric filters removed"

echo ""
echo "✅ Lab infrastructure teardown complete."
echo ""
echo "To also destroy the trading app: cd infra && cdk destroy"
