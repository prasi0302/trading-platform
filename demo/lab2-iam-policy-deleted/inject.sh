#!/bin/bash
# Lab 2: Inject IAM Policy Failure — Remove DynamoDB permissions from task role
# This removes DynamoDB access, causing AccessDeniedException in Market Data Service

set -e

PROFILE="gfs-workshop"
REGION="us-east-1"
ROLE_NAME="TradingAppStack-TaskRole30FC0FBB-7DHBfWiR0xFW"
POLICY_NAME="TaskRoleDefaultPolicy07FC53DE"

echo "🔴 Lab 2: Injecting IAM Failure — Removing DynamoDB Permissions"
echo "================================================================"
echo ""
echo "Action: Replacing inline policy on $ROLE_NAME"
echo "  Removing all dynamodb:* actions (keeping S3 only)"
echo ""

# Replace inline policy with S3-only version (removes DynamoDB access)
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*",
          "s3:DeleteObject*",
          "s3:PutObject",
          "s3:PutObjectLegalHold",
          "s3:PutObjectRetention",
          "s3:PutObjectTagging",
          "s3:PutObjectVersionTagging",
          "s3:Abort*"
        ],
        "Resource": [
          "arn:aws:s3:::tradingappstack-historicalbucket277a0e99-om2ma4dtmrby",
          "arn:aws:s3:::tradingappstack-historicalbucket277a0e99-om2ma4dtmrby/*"
        ],
        "Effect": "Allow"
      }
    ]
  }' \
  --profile "$PROFILE"

echo ""
echo "✅ Injected! DynamoDB permissions removed from task role."
echo ""
echo "📋 Expected behavior:"
echo "  1. Market Data Service keeps running (existing tasks not restarted)"
echo "  2. Next DynamoDB write attempt → AccessDeniedException"
echo "  3. CloudWatch Logs show 'AccessDeniedException'"
echo "  4. Metric filter catches it → CloudWatch Alarm triggers"
echo "  5. EventBridge rule fires → Lambda sends webhook to DevOps Agent"
echo "  6. DevOps Agent auto-investigates"
echo ""
echo "⏱️  It may take 1-2 minutes for the service to hit DynamoDB and produce errors."
echo ""
echo "🔗 Check CloudWatch Logs:"
echo "   aws logs tail TradingAppStack-MarketDataTaskDefMarketDataContainerLogGroup741D6F0D-vhxYM5BrZ5Us --follow --profile $PROFILE --region $REGION"
echo ""
echo "🔗 Check Alarm state:"
echo "   aws cloudwatch describe-alarms --alarm-names TradingApp-IAM-AccessDenied --profile $PROFILE --region $REGION --query 'MetricAlarms[0].StateValue'"
