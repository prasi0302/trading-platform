#!/bin/bash
# Lab 1: Fix Build Failure — Restore valid Docker base image
# This reverts the Dockerfile to use python:3.11-slim

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🟢 Lab 1: Fixing Build Failure — Restoring Valid Image"
echo "======================================================"
echo ""
echo "Action: Reverting services/market-data/Dockerfile"
echo "  FROM python:3.12-nonexistent → python:3.11-slim"
echo ""

# Fix the image
sed -i '' 's/FROM python:3.12-nonexistent/FROM python:3.11-slim/' "$REPO_ROOT/services/market-data/Dockerfile"

# Commit and push
cd "$REPO_ROOT"
git add services/market-data/Dockerfile
git commit -m "fix: restore valid Docker base image python:3.11-slim

Reverts invalid image tag 'python:3.12-nonexistent' back to
'python:3.11-slim' per DevOps Agent mitigation spec.

Resolves: build-market-data job failure (manifest not found)"

git push

echo ""
echo "✅ Fixed! Pipeline should go green now."
echo ""
echo "🔗 Check pipeline: https://github.com/prasi0302/trading-platform/actions"
