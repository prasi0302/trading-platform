#!/bin/bash
# Lab 4: Inject Service Discovery Failure — Wrong Market Data endpoint
# Changes MARKET_DATA_URL to a non-existent host, causing cascading timeouts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔴 Lab 4: Injecting Service Discovery Failure — Wrong Endpoint"
echo "==============================================================="
echo ""
echo "Action: Modifying services/order/app/config.py"
echo "  Changing PORTFOLIO_SERVICE_URL to 'http://portfolio-v2.internal:8003' (non-existent)"
echo ""

# Change the portfolio service URL to a non-existent host
sed -i '' 's|PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")|PORTFOLIO_SERVICE_URL: str = "http://portfolio-v2.internal:8003"  # Updated service discovery endpoint|' "$REPO_ROOT/services/order/app/config.py"

# Commit and push
cd "$REPO_ROOT"
git add services/order/app/config.py
git commit -m "refactor(order): update portfolio service discovery endpoint

Migrating to internal DNS-based service discovery. Updated
PORTFOLIO_SERVICE_URL to use the new internal hostname
'portfolio-v2.internal' for better service mesh integration."

git push

echo ""
echo "✅ Committed & pushed! Pipeline will run."
echo ""
echo "📋 Expected behavior:"
echo "  1. Pipeline: test-order PASSES (tests mock HTTP calls)"
echo "  2. Pipeline: build-order PASSES (code compiles fine)"
echo "  3. Pipeline: deploy-order PASSES (container starts)"
echo "  4. Runtime: Order Service can't resolve 'portfolio-v2.internal'"
echo "  5. Runtime: httpx.ConnectError on every order that checks portfolio"
echo "  6. UI: Placing orders fails with connection timeout"
echo "  7. CloudWatch Alarm fires → DevOps Agent investigates"
echo ""
echo "⏱️  Pipeline takes ~3-5 min. Errors start when user places an order."
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
echo ""
echo "💡 To trigger errors after deploy, place an order:"
echo "   curl -X POST http://Tradin-Tradi-VNtUgZp6acFf-284746681.us-east-1.elb.amazonaws.com/api/orders -H 'Content-Type: application/json' -d '{\"session_id\":\"test\",\"symbol\":\"AAPL\",\"side\":\"buy\",\"type\":\"market\",\"quantity\":10}'"
