#!/bin/bash
# Lab 3: Inject Bad Code Commit — Wrong DynamoDB table name
# Changes config.py to hardcode a wrong table name, commits, and pushes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔴 Lab 3: Injecting Bad Code Commit — Wrong DynamoDB Table Name"
echo "================================================================"
echo ""
echo "Action: Modifying services/market-data/app/config.py"
echo "  Hardcoding table name to 'market-data-ticks-v2' (doesn't exist in IAM policy)"
echo ""

# Change the table name in config.py
sed -i '' 's/DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "market-data-ticks")/DYNAMODB_TABLE: str = "market-data-ticks-v2"  # Migrating to new table/' "$REPO_ROOT/services/market-data/app/config.py"

# Commit and push
cd "$REPO_ROOT"
git add services/market-data/app/config.py
git commit -m "refactor(market-data): migrate to new DynamoDB table naming convention

Updating table name to follow new v2 naming convention for
consistency with other services. The new table 'market-data-ticks-v2'
aligns with the updated data model."

git push

echo ""
echo "✅ Committed & pushed! Pipeline will run."
echo ""
echo "📋 Expected behavior:"
echo "  1. Pipeline: test-market-data PASSES (tests mock DynamoDB)"
echo "  2. Pipeline: build-market-data PASSES (code compiles fine)"
echo "  3. Pipeline: deploy-market-data PASSES (container starts)"
echo "  4. Runtime: Service tries to write to 'market-data-ticks-v2'"
echo "  5. Runtime: AccessDeniedException (IAM only allows 'market-data-ticks')"
echo "  6. CloudWatch Alarm fires → DevOps Agent investigates"
echo ""
echo "⏱️  Pipeline takes ~3-5 min. Errors start after deploy."
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
