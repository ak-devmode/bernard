#!/bin/bash
set -euo pipefail

# Update OpenClaw to the version pinned in openclaw-version.txt
# Only upgrades on minor/major version changes.

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PINNED_VERSION=$(cat "${REPO_DIR}/infra/openclaw-version.txt" | tr -d '[:space:]')

CURRENT_VERSION=$(openclaw --version 2>/dev/null || echo "unknown")

echo "Current: ${CURRENT_VERSION}"
echo "Pinned:  ${PINNED_VERSION}"

if [ "${CURRENT_VERSION}" = "${PINNED_VERSION}" ]; then
    echo "Already at pinned version. Nothing to do."
    exit 0
fi

echo "Updating OpenClaw to ${PINNED_VERSION}..."
npm install -g "openclaw@${PINNED_VERSION}"

echo "Updated. Restart OpenClaw to apply:"
echo "  openclaw restart"
