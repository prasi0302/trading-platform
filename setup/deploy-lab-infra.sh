#!/bin/bash
# =============================================================================
# AWS DevOps Agent Workshop — Deploy Lab Infrastructure
# =============================================================================
# This script creates the CloudWatch metric filters, alarms, EventBridge rules,
# and Lambda webhook function needed for Labs 2, 3, and 4.
#
# Prerequisites:
#   1. CDK stack deployed (cdk deploy in infra/)
#   2. config.env filled in with your values
#   3. DevOps Agent space created with webhook URL/secret
#
# Usage: ./setup/deploy-lab-infra.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load config
if [ ! -f "$SCRIPT_DIR/config.env" ]; then
    echo "❌ config.env not found. Copy config.env.example to config.env and fill in your values."
    exit 1
fi
source "$SCRIPT_DIR/config.env"

# Validate required values
for var in AWS_ACCOUNT_ID AWS_REGION AWS_PROFILE MARKET_DATA_LOG_GROUP ORDER_LOG_GROUP DEVOPS_AGENT_WEBHOOK_URL DEVOPS_AGENT_WEBHOOK_SECRET TASK_ROLE_NAME; do
    if [ -z "${!var}" ] || [[ "${!var}" == PASTE_* ]] || [[ "${!var}" == YOUR_* ]]; then
        echo "❌ $var is not set in config.env. Please fill it in."
        exit 1
    fi
done

echo "🚀 Deploying Lab Infrastructure"
echo "================================"
echo "Account: $AWS_ACCOUNT_ID"
echo "Region:  $AWS_REGION"
echo "Profile: $AWS_PROFILE"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 1. CloudWatch Metric Filters
# ─────────────────────────────────────────────────────────────────────────────
echo "📊 Creating CloudWatch Metric Filters..."

# Lab 2 & 3: AccessDeniedException on Market Data log group
aws logs put-metric-filter \
    --log-group-name "$MARKET_DATA_LOG_GROUP" \
    --filter-name "IAMAccessDenied" \
    --filter-pattern "AccessDeniedException" \
    --metric-transformations metricName=IAMAccessDeniedCount,metricNamespace=TradingApp,metricValue=1 \
    --profile "$AWS_PROFILE" --region "$AWS_REGION"
echo "  ✅ IAMAccessDenied filter (Market Data)"

# Lab 4: Connection/timeout errors on Order Service log group
aws logs put-metric-filter \
    --log-group-name "$ORDER_LOG_GROUP" \
    --filter-name "OrderServiceConnectTimeout" \
    --filter-pattern "?ConnectError ?TimeoutException ?ConnectTimeout ?\"Name or service not known\" ?\"Portfolio update error\"" \
    --metric-transformations metricName=OrderServiceTimeoutErrors,metricNamespace=TradingApp,metricValue=1 \
    --profile "$AWS_PROFILE" --region "$AWS_REGION"
echo "  ✅ OrderServiceConnectTimeout filter (Order)"

# ─────────────────────────────────────────────────────────────────────────────
# 2. CloudWatch Alarms
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "🔔 Creating CloudWatch Alarms..."

aws cloudwatch put-metric-alarm \
    --alarm-name "TradingApp-IAM-AccessDenied" \
    --alarm-description "Market Data Service IAM access denied errors" \
    --metric-name IAMAccessDeniedCount \
    --namespace TradingApp \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --treat-missing-data notBreaching \
    --profile "$AWS_PROFILE" --region "$AWS_REGION"
echo "  ✅ TradingApp-IAM-AccessDenied alarm"

aws cloudwatch put-metric-alarm \
    --alarm-name "TradingApp-Order-ServiceTimeout" \
    --alarm-description "Order Service connection timeout errors - possible service discovery misconfiguration" \
    --metric-name OrderServiceTimeoutErrors \
    --namespace TradingApp \
    --statistic Sum \
    --period 60 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --treat-missing-data notBreaching \
    --profile "$AWS_PROFILE" --region "$AWS_REGION"
echo "  ✅ TradingApp-Order-ServiceTimeout alarm"

# ─────────────────────────────────────────────────────────────────────────────
# 3. Lambda Webhook Function
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "⚡ Creating Lambda Webhook Function..."

# Create IAM role for Lambda
ROLE_ARN=$(aws iam create-role \
    --role-name TradingApp-WebhookLambdaRole \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --profile "$AWS_PROFILE" \
    --query 'Role.Arn' --output text 2>/dev/null || \
    aws iam get-role --role-name TradingApp-WebhookLambdaRole --profile "$AWS_PROFILE" --query 'Role.Arn' --output text)

aws iam attach-role-policy \
    --role-name TradingApp-WebhookLambdaRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    --profile "$AWS_PROFILE" 2>/dev/null || true

echo "  ✅ Lambda IAM role: $ROLE_ARN"
echo "  ⏳ Waiting 10s for IAM propagation..."
sleep 10

# Package Lambda
cd "$REPO_ROOT/setup"
cp "$REPO_ROOT/demo/lab2-iam-policy-deleted/lambda_function.py" /tmp/webhook_lambda.py
cd /tmp && zip -j webhook_lambda.zip webhook_lambda.py > /dev/null 2>&1

# Create or update Lambda
LAMBDA_ARN=$(aws lambda create-function \
    --function-name TradingApp-DevOpsWebhook \
    --runtime python3.11 \
    --role "$ROLE_ARN" \
    --handler webhook_lambda.handler \
    --zip-file fileb:///tmp/webhook_lambda.zip \
    --timeout 30 \
    --environment "Variables={WEBHOOK_URL=$DEVOPS_AGENT_WEBHOOK_URL,WEBHOOK_SECRET=$DEVOPS_AGENT_WEBHOOK_SECRET}" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" \
    --query 'FunctionArn' --output text 2>/dev/null || \
    (aws lambda update-function-code \
        --function-name TradingApp-DevOpsWebhook \
        --zip-file fileb:///tmp/webhook_lambda.zip \
        --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null 2>&1 && \
     aws lambda update-function-configuration \
        --function-name TradingApp-DevOpsWebhook \
        --environment "Variables={WEBHOOK_URL=$DEVOPS_AGENT_WEBHOOK_URL,WEBHOOK_SECRET=$DEVOPS_AGENT_WEBHOOK_SECRET}" \
        --profile "$AWS_PROFILE" --region "$AWS_REGION" \
        --query 'FunctionArn' --output text 2>/dev/null))

echo "  ✅ Lambda function: TradingApp-DevOpsWebhook"

rm -f /tmp/webhook_lambda.py /tmp/webhook_lambda.zip

# ─────────────────────────────────────────────────────────────────────────────
# 4. EventBridge Rules
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "📡 Creating EventBridge Rules..."

LAMBDA_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:TradingApp-DevOpsWebhook"

# Rule for IAM Access Denied alarm (Labs 2 & 3)
aws events put-rule \
    --name "TradingApp-IAMAlarm-ToDevOps" \
    --event-pattern "{\"source\":[\"aws.cloudwatch\"],\"detail-type\":[\"CloudWatch Alarm State Change\"],\"detail\":{\"alarmName\":[\"TradingApp-IAM-AccessDenied\"]}}" \
    --description "Routes IAM access denied alarm to DevOps Agent webhook Lambda" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null

aws events put-targets \
    --rule "TradingApp-IAMAlarm-ToDevOps" \
    --targets "Id=DevOpsWebhookLambda,Arn=$LAMBDA_ARN" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null

aws lambda add-permission \
    --function-name TradingApp-DevOpsWebhook \
    --statement-id EventBridgeInvokeIAM \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn "arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/TradingApp-IAMAlarm-ToDevOps" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null 2>&1 || true

echo "  ✅ TradingApp-IAMAlarm-ToDevOps rule"

# Rule for Order Service timeout alarm (Lab 4)
aws events put-rule \
    --name "TradingApp-OrderTimeout-ToDevOps" \
    --event-pattern "{\"source\":[\"aws.cloudwatch\"],\"detail-type\":[\"CloudWatch Alarm State Change\"],\"detail\":{\"alarmName\":[\"TradingApp-Order-ServiceTimeout\"]}}" \
    --description "Routes Order Service timeout alarm to DevOps Agent webhook Lambda" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null

aws events put-targets \
    --rule "TradingApp-OrderTimeout-ToDevOps" \
    --targets "Id=DevOpsWebhookLambda,Arn=$LAMBDA_ARN" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null

aws lambda add-permission \
    --function-name TradingApp-DevOpsWebhook \
    --statement-id EventBridgeInvokeOrderTimeout \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn "arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/TradingApp-OrderTimeout-ToDevOps" \
    --profile "$AWS_PROFILE" --region "$AWS_REGION" > /dev/null 2>&1 || true

echo "  ✅ TradingApp-OrderTimeout-ToDevOps rule"

# ─────────────────────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "✅ Lab infrastructure deployed successfully!"
echo "============================================"
echo ""
echo "Resources created:"
echo "  • Metric Filter: IAMAccessDenied ($MARKET_DATA_LOG_GROUP)"
echo "  • Metric Filter: OrderServiceConnectTimeout ($ORDER_LOG_GROUP)"
echo "  • Alarm: TradingApp-IAM-AccessDenied"
echo "  • Alarm: TradingApp-Order-ServiceTimeout"
echo "  • Lambda: TradingApp-DevOpsWebhook"
echo "  • IAM Role: TradingApp-WebhookLambdaRole"
echo "  • EventBridge Rule: TradingApp-IAMAlarm-ToDevOps"
echo "  • EventBridge Rule: TradingApp-OrderTimeout-ToDevOps"
echo ""
echo "Next steps:"
echo "  1. Set up GitHub Actions secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
echo "  2. Update .github/workflows/deploy.yml with your resource names"
echo "  3. Run Lab 1: ./demo/lab1-dockerfile-bad-image/inject.sh"
