#!/bin/bash
# Lab 3: Fix Service Discovery Failure — Restore the env-var-driven endpoint.
# Used by the FSI Autonomous Incident Response workshop (Module 1, Lab 3).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Lab 3: Fixing Service Discovery Failure — Restoring Correct Endpoint"
echo "===================================================================="
echo
echo "Action: reverting services/order/app/config.py"
echo "  Restoring PORTFOLIO_SERVICE_URL env var lookup"
echo

sed -i.bak \
    's|PORTFOLIO_SERVICE_URL: str = "http://portfolio-v2.internal:8003"  # Updated service discovery endpoint|PORTFOLIO_SERVICE_URL: str = os.getenv("PORTFOLIO_SERVICE_URL", "http://localhost:8003")|' \
    "$REPO_ROOT/services/order/app/config.py"
rm -f "$REPO_ROOT/services/order/app/config.py.bak"

cd "$REPO_ROOT"
git add services/order/app/config.py
git commit -m "fix(order): revert portfolio service endpoint to env-var config

Reverting the hardcoded 'portfolio-v2.internal:8003' endpoint back to
env-var-driven config. The internal DNS hostname was not provisioned in
service discovery, causing ConnectError timeouts on every order
operation.

Resolves: cascading timeout failures in the Order Service"
git push

echo
echo "Fix committed and pushed. The pipeline will deploy the fix."
echo
echo "Recovery behavior:"
echo "  1. Pipeline deploys the fixed container (~3-5 min)"
echo "  2. Order service reconnects to Portfolio via the ALB"
echo "  3. Orders start succeeding again"
echo "  4. CloudWatch alarm returns to OK"
