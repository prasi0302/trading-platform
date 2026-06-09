#!/bin/bash
# Lab 1: Inject Build Failure — Bad Docker base image
# This changes the market-data Dockerfile to use a non-existent image tag

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔴 Lab 1: Injecting Build Failure — Bad Docker Image"
echo "=================================================="
echo ""
echo "Action: Changing services/market-data/Dockerfile"
echo "  FROM python:3.11-slim → python:3.12-nonexistent"
echo ""

# Inject the bad image
sed -i '' 's/FROM python:3.11-slim/FROM python:3.12-nonexistent/' "$REPO_ROOT/services/market-data/Dockerfile"

# Commit and push
cd "$REPO_ROOT"
git add services/market-data/Dockerfile
git commit -m "feat: upgrade market-data base image to python:3.12-nonexistent

Upgrading base image for better performance."

git push

echo ""
echo "✅ Injected! Pipeline will fail at build-market-data job."
echo ""
echo "📋 Expected behavior:"
echo "  1. Test stage passes"
echo "  2. build-market-data FAILS (manifest not found)"
echo "  3. Deploy/Verify stages skipped"
echo "  4. DevOps Agent webhook fires"
echo "  5. Automated investigation starts"
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
echo "🔗 Check DevOps Agent: (your agent space web app URL)"
