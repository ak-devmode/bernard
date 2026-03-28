#!/bin/bash
set -euo pipefail

# Bernard VM setup script
# Bootstraps a fresh Ubuntu VM with OpenClaw, Claude Code, and supporting tools.
# Run as root or with sudo on the target VM.

BERNARD_HOME="/home/bernard"
OPENCLAW_DIR="${BERNARD_HOME}/.openclaw"
REPO_DIR="${BERNARD_HOME}/bernard"
PINNED_VERSION=$(cat "${REPO_DIR}/infra/openclaw-version.txt" | tr -d '[:space:]')

echo "=== Bernard VM Setup ==="
echo "OpenClaw version: ${PINNED_VERSION}"

# 1. Create bernard user if not exists
if ! id bernard &>/dev/null; then
    useradd -m -s /bin/bash bernard
    echo "Created user: bernard"
fi

# 2. Install Node.js (LTS) if not present
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
    apt-get install -y nodejs
    echo "Installed Node.js $(node --version)"
fi

# 3. Install OpenClaw at pinned version
sudo -u bernard bash -c "
    mkdir -p ${BERNARD_HOME}/.npm-global
    npm config set prefix '${BERNARD_HOME}/.npm-global'
    npm install -g openclaw@${PINNED_VERSION}
"
echo "Installed OpenClaw ${PINNED_VERSION}"

# 4. Symlink workspace and config from repo
if [ -d "${REPO_DIR}/openclaw/workspace" ]; then
    ln -sfn "${REPO_DIR}/openclaw/workspace" "${OPENCLAW_DIR}/workspace"
    echo "Linked workspace"
fi

# 5. Install Python + Whisper (for voice transcription)
apt-get install -y python3 python3-venv python3-pip ffmpeg
sudo -u bernard bash -c "
    python3 -m venv ${OPENCLAW_DIR}/whisper-env
    source ${OPENCLAW_DIR}/whisper-env/bin/activate
    pip install openai-whisper
"
echo "Installed Whisper"

# 6. Install Claude Code (for remote Claude access)
# TODO: Add Claude Code installation once access method confirmed
# npm install -g @anthropic-ai/claude-code

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Copy .env to ${OPENCLAW_DIR}/.env (see infra/env.example)"
echo "  2. Copy openclaw.json to ${OPENCLAW_DIR}/openclaw.json (fill in secrets from template)"
echo "  3. Start OpenClaw: sudo -u bernard openclaw start"
