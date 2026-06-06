#!/bin/bash
echo "Initializing LocalStack resources..."

# Create DynamoDB table
awslocal dynamodb create-table \
  --table-name market-data-ticks \
  --attribute-definitions \
    AttributeName=symbol,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=symbol,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

# Enable TTL
awslocal dynamodb update-time-to-live \
  --table-name market-data-ticks \
  --time-to-live-specification Enabled=true,AttributeName=ttl

# Create S3 bucket
awslocal s3 mb s3://trading-app-historical

echo "LocalStack initialization complete."
