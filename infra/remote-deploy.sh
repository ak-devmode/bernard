#!/usr/bin/env bash
# remote-deploy.sh — Push and deploy to server from local machine.
# Usage: bash infra/remote-deploy.sh

set -euo pipefail

SERVER="54.251.203.204"
SSH_KEY="$HOME/.ssh/awk_sandbox.pem"

echo "=== Pushing to GitHub ==="
git push

echo "=== Deploying on server ==="
ssh -i "$SSH_KEY" bernard@$SERVER "bash ~/bernard/infra/deploy.sh"
