#!/bin/bash
# Lab 3: Fix Bad Code Commit — Revert to correct DynamoDB table name
# Reverts config.py to use the env var with correct default, commits, and pushes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🟢 Lab 3: Fixing Bad Code Commit — Restoring Correct Table Name"
echo "================================================================"
echo ""
echo "Action: Reverting services/market-data/app/config.py"
echo "  Restoring env var lookup with default 'market-data-ticks'"
echo ""

# Restore the correct config
sed -i '' 's/DYNAMODB_TABLE: str = "market-data-ticks-v2"  # Migrating to new table/DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "market-data-ticks")/' "$REPO_ROOT/services/market-data/app/config.py"

# Commit and push
cd "$REPO_ROOT"
git add services/market-data/app/config.py
git commit -m "fix(market-data): revert DynamoDB table name to correct value

Reverting table name change from 'market-data-ticks-v2' back to
env-var-driven config with default 'market-data-ticks'.
The v2 table was not provisioned and IAM policy doesn't grant access.

Resolves: AccessDeniedException on dynamodb:BatchWriteItem"

git push

echo ""
echo "✅ Fix committed & pushed! Pipeline will deploy the fix."
echo ""
echo "📋 Recovery behavior:"
echo "  1. Pipeline deploys fixed container (~3-5 min)"
echo "  2. New container uses correct table name"
echo "  3. DynamoDB writes succeed again"
echo "  4. Price charts resume updating"
echo "  5. CloudWatch Alarm returns to OK"
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
