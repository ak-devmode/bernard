#!/usr/bin/env bash
# deploy.sh — Pull latest from GitHub and restart OpenClaw gateway.
# Run as bernard user on server: bash ~/bernard/infra/deploy.sh
# Or remotely: ssh ... "sudo -u bernard bash ~/bernard/infra/deploy.sh"

set -euo pipefail

REPO_DIR="$HOME/bernard"
OPENCLAW_BIN="$HOME/.npm-global/bin/openclaw"

cd "$REPO_DIR"

echo "=== Pulling latest from GitHub ==="
git pull --ff-only

echo "=== Restarting OpenClaw gateway ==="
systemctl --user restart openclaw-gateway.service

echo "=== Verifying gateway health ==="
sleep 2
if curl -sf http://127.0.0.1:18789/health > /dev/null 2>&1; then
  echo "✓ Gateway healthy"
else
  echo "✗ Gateway health check failed — check logs with: journalctl --user -u openclaw-gateway.service -n 50"
  exit 1
fi

echo "=== Deploy complete ==="
