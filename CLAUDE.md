# Bernard

Bernard is Alex Knecht's AI personal assistant, running on OpenClaw on an AWS EC2 instance (Ubuntu, 54.254.76.94).

## What this repo is
- **Config & identity layer** for Bernard's OpenClaw instance — not a fork of OpenClaw itself
- **Obsidian vault** (`vault/`) — Bernard's long-term memory and knowledge base
- **Custom tools & pipelines** (`tools/`) — summarization, prioritization, relationship tracking, digests
- **Infrastructure scripts** (`infra/`) — VM setup, OpenClaw version pinning, update management

## Architecture
- OpenClaw is installed via npm at a pinned version (see `infra/openclaw-version.txt`)
- Bernard's personality lives in `openclaw/workspace/` (SOUL.md, IDENTITY.md, etc.)
- Secrets (API keys, tokens, credentials) are gitignored — see `infra/env.example` and `infra/openclaw.json.template`
- The `openclaw/openclaw.json` in this repo contains live tokens — **do not commit changes to it without sanitizing first**

## Server access
```
ssh -i ~/.ssh/awk_sandbox.pem ubuntu@54.254.76.94
```
Bernard runs as the `bernard` user. OpenClaw data lives at `/home/bernard/.openclaw/`.

## Key commands
- Deploy workspace changes: `rsync -avz openclaw/workspace/ bernard@server:.openclaw/workspace/`
- Check pinned version: `cat infra/openclaw-version.txt`
- Update OpenClaw on server: `bash infra/update.sh`
