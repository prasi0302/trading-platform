#!/bin/bash
# =============================================================================
# Generate deploy.yml from template using config.env values
# =============================================================================
# This creates .github/workflows/deploy.yml with your account-specific values.
#
# Usage: ./setup/generate-pipeline.sh
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load config
if [ ! -f "$SCRIPT_DIR/config.env" ]; then
    echo "❌ config.env not found."
    exit 1
fi
source "$SCRIPT_DIR/config.env"

echo "📝 Generating .github/workflows/deploy.yml..."
echo ""

# Export for envsubst
export ECR_REGISTRY AWS_REGION ECS_CLUSTER ALB_DNS CLOUDFRONT_URL S3_FRONTEND_BUCKET
export MARKET_DATA_SERVICE ORDER_SERVICE PORTFOLIO_SERVICE ALERT_SERVICE WS_GATEWAY_SERVICE

cat "$REPO_ROOT/setup/deploy.yml.template" | envsubst > "$REPO_ROOT/.github/workflows/deploy.yml"

echo "✅ Generated .github/workflows/deploy.yml"
echo ""
echo "Don't forget to set GitHub Actions secrets:"
echo "  • AWS_ACCESS_KEY_ID"
echo "  • AWS_SECRET_ACCESS_KEY"
echo "  • DEVOPS_AGENT_WEBHOOK_URL (for Lab 1 pipeline failure notification)"
echo "  • DEVOPS_AGENT_WEBHOOK_SECRET"
