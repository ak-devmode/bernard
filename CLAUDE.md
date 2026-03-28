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
sudo su - bernard
source ~/.nvm/nvm.sh   # needed for openclaw/node commands
```
Bernard runs as the `bernard` user (password saved in password manager). OpenClaw data lives at `/home/bernard/.openclaw/`.

The `ubuntu` user has sudo. The `bernard` user does NOT have sudo (intentional).

## Key commands
- Deploy workspace changes: `rsync -avz -e "ssh -i ~/.ssh/awk_sandbox.pem" openclaw/workspace/ ubuntu@54.254.76.94:/tmp/workspace/ && ssh ... sudo cp -r /tmp/workspace/ /home/bernard/.openclaw/workspace/`
- Deploy config: `rsync -avz -e "ssh -i ~/.ssh/awk_sandbox.pem" openclaw/openclaw.json ubuntu@54.254.76.94:/tmp/openclaw.json && ssh ... sudo cp /tmp/openclaw.json /home/bernard/.openclaw/openclaw.json && sudo chown bernard:bernard ...`
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
- **Never run `openclaw doctor --fix` casually** — it can wipe config sections (tools.web, pairing state, etc.)
- **Never strip keys from openclaw.json then upgrade** — the upgrade reads the stripped config and wipes pairing/auth state
- **Config workflow**: edit `openclaw/openclaw.json` locally (with `${ENV_VAR}` refs) → commit → rsync to server. Use `infra/openclaw.json.template` for the gitignored version.
- **Telegram pairing**: if pairing CLI hangs, manually edit `~/.openclaw/credentials/telegram-default-allowFrom.json` instead
- **Loopback debugging**: if `ping 127.0.0.1` fails, check `dmesg | grep DROPPED-EGRESS` — the egress firewall script may be missing the loopback ACCEPT rule
