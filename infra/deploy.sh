#!/usr/bin/env bash
# deploy.sh — Pull latest from GitHub and restart OpenClaw gateway.
# Run as bernard user on server: bash ~/bernard/infra/deploy.sh
# Or remotely: ssh ... "sudo -u bernard bash ~/bernard/infra/deploy.sh"

set -euo pipefail

REPO_DIR="$HOME/bernard"

# Ensure XDG_RUNTIME_DIR is set (required for systemctl --user via sudo)
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

cd "$REPO_DIR"

echo "=== Pulling latest from GitHub ==="
git pull --ff-only

echo "=== Restarting OpenClaw gateway ==="
systemctl --user restart openclaw-gateway.service

echo "=== Verifying gateway health (may take ~10s) ==="
HEALTHY=false
for i in $(seq 1 6); do
  sleep 3
  if curl -sf http://127.0.0.1:18789/health > /dev/null 2>&1; then
    HEALTHY=true
    break
  fi
done

if $HEALTHY; then
  echo "✓ Gateway healthy"
else
  echo "✗ Gateway health check failed after 18s"
  echo "  Check logs: journalctl --user -u openclaw-gateway.service -n 50"
  exit 1
fi

echo "=== Deploy complete ==="
