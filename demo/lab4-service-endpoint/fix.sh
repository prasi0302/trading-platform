#!/bin/bash
# Lab 4: Fix Service Discovery Failure — Restore correct Market Data endpoint
# Reverts config.py to use the env var with correct default, commits, and pushes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🟢 Lab 4: Fixing Service Discovery Failure — Restoring Correct Endpoint"
echo "========================================================================"
echo ""
echo "Action: Reverting services/order/app/config.py"
echo "  Restoring PORTFOLIO_SERVICE_URL env var lookup"
echo ""

# Restore the correct config
sed -i '' 's|PORTFOLIO_SERVICE_URL: str = "http://portfolio-v2.internal:8003"  # Updated service discovery endpoint|PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")|' "$REPO_ROOT/services/order/app/config.py"

# Commit and push
cd "$REPO_ROOT"
git add services/order/app/config.py
git commit -m "fix(order): revert portfolio service endpoint to env-var config

Reverting hardcoded 'portfolio-v2.internal:8003' endpoint back to
env-var-driven config. The internal DNS hostname was not provisioned
in service discovery, causing ConnectError timeouts on all order
operations.

Resolves: cascading timeout failures in Order Service"

git push

echo ""
echo "✅ Fix committed & pushed! Pipeline will deploy the fix."
echo ""
echo "📋 Recovery behavior:"
echo "  1. Pipeline deploys fixed container (~3-5 min)"
echo "  2. Order Service reconnects to Market Data via ALB"
echo "  3. Orders start succeeding again"
echo "  4. CloudWatch Alarm returns to OK"
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
