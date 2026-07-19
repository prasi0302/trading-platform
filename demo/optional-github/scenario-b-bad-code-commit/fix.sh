#!/bin/bash
# Lab 2: Fix Bad Code Commit — Restore the env-var-driven DynamoDB table name.
# Used by the FSI Autonomous Incident Response workshop (Module 1, Lab 2).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "Lab 2: Fixing Bad Code Commit — Restoring Correct Table Name"
echo "============================================================"
echo
echo "Action: reverting services/market-data/app/config.py"
echo "  Restoring env var lookup with default 'market-data-ticks'"
echo

sed -i.bak \
    's|DYNAMODB_TABLE: str = "market-data-ticks-v2"  # Migrating to new table|DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "market-data-ticks")|' \
    "$REPO_ROOT/services/market-data/app/config.py"
rm -f "$REPO_ROOT/services/market-data/app/config.py.bak"

cd "$REPO_ROOT"
git add services/market-data/app/config.py
git commit -m "fix(market-data): revert DynamoDB table name to correct value

Reverting table name from 'market-data-ticks-v2' back to env-var-driven
config with default 'market-data-ticks'. The v2 table was not provisioned
and the IAM policy does not grant access to it.

Resolves: AccessDeniedException on dynamodb:BatchWriteItem"
git push

echo
echo "Fix committed and pushed. The pipeline will deploy the fix."
echo
echo "Recovery behavior:"
echo "  1. Pipeline deploys the fixed container (~3-5 min)"
echo "  2. New container uses the correct table name"
echo "  3. DynamoDB writes succeed again"
echo "  4. Price charts resume updating"
echo "  5. CloudWatch alarm returns to OK"
