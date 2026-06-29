#!/bin/bash
# Lab 3: Inject Service Discovery Failure — Wrong Portfolio Service endpoint.
# Updates Order Service config to point to a non-existent internal hostname,
# causing cascading timeouts on every order. Used by the FSI Autonomous
# Incident Response workshop (Module 1, Lab 3).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Lab 3: Injecting Service Discovery Failure — Wrong Endpoint"
echo "==========================================================="
echo
echo "Action: modifying services/order/app/config.py"
echo "  Changing PORTFOLIO_SERVICE_URL to 'http://portfolio-v2.internal:8003' (non-existent)"
echo

sed -i.bak \
    's|PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")|PORTFOLIO_SERVICE_URL: str = "http://portfolio-v2.internal:8003"  # Updated service discovery endpoint|' \
    "$REPO_ROOT/services/order/app/config.py"
rm -f "$REPO_ROOT/services/order/app/config.py.bak"

cd "$REPO_ROOT"
git add services/order/app/config.py
git commit -m "refactor(order): update portfolio service discovery endpoint

Migrating to internal DNS-based service discovery. Updated
PORTFOLIO_SERVICE_URL to use the new internal hostname
'portfolio-v2.internal' for better service mesh integration."
git push

echo
echo "Committed and pushed. The pipeline will run."
echo
echo "Expected behavior:"
echo "  1. Pipeline test-order PASSES (tests mock HTTP calls)"
echo "  2. Pipeline build-order PASSES (code compiles)"
echo "  3. Pipeline deploy-order PASSES (container starts)"
echo "  4. Runtime: Order service can't resolve 'portfolio-v2.internal'"
echo "  5. Runtime: httpx.ConnectError on every order that checks portfolio"
echo "  6. UI: placing orders fails with connection timeout"
echo "  7. CloudWatch alarm fires; AWS DevOps Agent investigates"
echo
echo "Pipeline takes ~3-5 min. Errors start when a user places an order."
