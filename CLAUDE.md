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
- `openclaw/openclaw.json` uses `${ENV_VAR}` references for secrets — safe to commit. Actual keys live in systemd service `Environment=` lines on server.

## Server access
```bash
# Direct as bernard (preferred — for OpenClaw, deploy, git):
ssh -i ~/.ssh/awk_sandbox.pem bernard@54.254.76.94

# As ubuntu (only when sudo needed — firewall, system packages, etc.):
ssh -i ~/.ssh/awk_sandbox.pem ubuntu@54.254.76.94
```
Bernard runs as the `bernard` user. OpenClaw data lives at `/home/bernard/.openclaw/`.
The `bernard` user does NOT have sudo (intentional, never grant it).
The `ubuntu` user has sudo — use only for system-level operations.

## Deployment (git+symlinks)
Deploy = push to GitHub, then pull on server. No more rsync.
```bash
# From local: push and deploy (one command)
bash infra/remote-deploy.sh

# Or manually:
git push origin bernard-v2
ssh -i ~/.ssh/awk_sandbox.pem bernard@54.254.76.94 "bash ~/bernard/infra/deploy.sh"
```

Server repo: `~/bernard/` (cloned from GitHub)
Symlinks:
- `~/.openclaw/workspace` → `~/bernard/openclaw/workspace`
- `~/.openclaw/openclaw.json` → `~/bernard/openclaw/openclaw.json`

## Other commands
- Check pinned version: `cat infra/openclaw-version.txt`
- Update OpenClaw on server: `bash infra/update.sh`
- Restart gateway: `systemctl --user restart openclaw-gateway.service`
- Check gateway health: `curl -s http://127.0.0.1:18789/health`
- Check Telegram status: `openclaw channels status --probe`

## VM details
- **Node.js**: v24 via nvm (default). System node is v22 at `/usr/local/bin/node` — do NOT use for openclaw.
- **OpenClaw binary**: `/home/bernard/.npm-global/bin/openclaw` (symlinked to `/usr/local/bin/openclaw` for all users)
- **Systemd service**: `~/.config/systemd/user/openclaw-gateway.service` — uses nvm node 24 path in ExecStart. Env vars (API keys) are set here.
- **Egress firewall**: `/etc/iptables/setup-egress.sh` — whitelist-based OUTPUT rules. The `-o lo -j ACCEPT` rule MUST be present or loopback breaks entirely. Re-run with `sudo bash /etc/iptables/setup-egress.sh` after changes.

## Credentials & env vars
- API keys are set as `Environment=` lines in the systemd service file
- `openclaw.json` uses `${ENV_VAR}` references — do NOT hardcode secrets in it
- Keys needed: `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `GATEWAY_AUTH_TOKEN`, `BRAVE_API_KEY`, `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`
- Telegram allowlist: `~/.openclaw/credentials/telegram-default-allowFrom.json` (Alex's Telegram ID: `8522147628`)

## Known gotchas
- **NEVER run `openclaw doctor --fix`** — permanently banned. On 2026-03-28 it wiped tools.web config and pairing state. Use `openclaw doctor` (read-only) for diagnostics only.
- **Never strip keys from openclaw.json then upgrade** — the upgrade reads the stripped config and wipes pairing/auth state
- **Config workflow**: edit `openclaw/openclaw.json` locally (with `${ENV_VAR}` refs) → commit → rsync to server. Use `infra/openclaw.json.template` for the gitignored version.
- **Telegram pairing**: if pairing CLI hangs, manually edit `~/.openclaw/credentials/telegram-default-allowFrom.json` instead
- **Loopback debugging**: if `ping 127.0.0.1` fails, check `dmesg | grep DROPPED-EGRESS` — the egress firewall script may be missing the loopback ACCEPT rule
