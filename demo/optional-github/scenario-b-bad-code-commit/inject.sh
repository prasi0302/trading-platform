#!/bin/bash
# Lab 2: Inject Bad Code Commit — Wrong DynamoDB table name
# Modifies the Market Data service to hardcode a DynamoDB table name that the
# IAM policy does not allow. The pipeline passes (tests mock DynamoDB); the
# service fails at runtime with AccessDeniedException. Used by the FSI
# Autonomous Incident Response workshop (Module 1, Lab 2).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "Lab 2: Injecting Bad Code Commit — Wrong DynamoDB Table Name"
echo "============================================================"
echo
echo "Action: modifying services/market-data/app/config.py"
echo "  Hardcoding table name to 'market-data-ticks-v2' (not in IAM policy)"
echo

sed -i.bak \
    's|DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "market-data-ticks")|DYNAMODB_TABLE: str = "market-data-ticks-v2"  # Migrating to new table|' \
    "$REPO_ROOT/services/market-data/app/config.py"
rm -f "$REPO_ROOT/services/market-data/app/config.py.bak"

cd "$REPO_ROOT"
git add services/market-data/app/config.py
git commit -m "refactor(market-data): migrate to new DynamoDB table naming convention

Updating table name to follow the new v2 naming convention for
consistency with other services. The new table 'market-data-ticks-v2'
aligns with the updated data model."
git push

echo
echo "Committed and pushed. The pipeline will run."
echo
echo "Expected behavior:"
echo "  1. Pipeline test-market-data PASSES (tests mock DynamoDB)"
echo "  2. Pipeline build-market-data PASSES (code compiles)"
echo "  3. Pipeline deploy-market-data PASSES (container starts)"
echo "  4. Runtime: service tries to write to 'market-data-ticks-v2'"
echo "  5. Runtime: AccessDeniedException (IAM only allows 'market-data-ticks')"
echo "  6. CloudWatch alarm fires; AWS DevOps Agent investigates"
echo
echo "Pipeline takes ~3-5 min. Errors start after deploy."
