#!/bin/bash
# Lab 2: Fix IAM Policy Failure — Restore DynamoDB permissions to task role
# This re-adds DynamoDB access to resolve AccessDeniedException

set -e

PROFILE="gfs-workshop"
REGION="us-east-1"
ROLE_NAME="TradingAppStack-TaskRole30FC0FBB-7DHBfWiR0xFW"
POLICY_NAME="TaskRoleDefaultPolicy07FC53DE"

echo "🟢 Lab 2: Fixing IAM Failure — Restoring DynamoDB Permissions"
echo "=============================================================="
echo ""
echo "Action: Restoring full inline policy on $ROLE_NAME"
echo "  Re-adding dynamodb:* actions for market-data-ticks table"
echo ""

# Restore full inline policy (DynamoDB + S3)
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "dynamodb:BatchGetItem",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:Query",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:ConditionCheckItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:DescribeTable"
        ],
        "Resource": [
          "arn:aws:dynamodb:us-east-1:288282347955:table/market-data-ticks"
        ],
        "Effect": "Allow"
      },
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
echo "✅ Fixed! DynamoDB permissions restored."
echo ""
echo "📋 Recovery behavior:"
echo "  1. Next DynamoDB operation succeeds (IAM policy change is immediate)"
echo "  2. Errors stop appearing in CloudWatch Logs"
echo "  3. CloudWatch Alarm returns to OK state (after metric drops to 0)"
echo ""
echo "🔗 Verify fix:"
echo "   curl -s http://Tradin-Tradi-VNtUgZp6acFf-284746681.us-east-1.elb.amazonaws.com/api/symbols/AAPL/history | head -c 200"
