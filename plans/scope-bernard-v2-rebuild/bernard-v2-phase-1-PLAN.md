# Plan: Phase 1 — Foundation & Config

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Ready to execute
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §4.1, §6, §9 Phase 1

---

## Phase 1: Foundation & Config

### Task 1.1: Check Current OpenClaw Version
- **Type**: AI (SSH)
- **Input**: Server at 54.254.76.94, bernard user
- **Action**:
  ```bash
  ssh -i ~/.ssh/awk_sandbox.pem ubuntu@54.254.76.94 \
    "sudo -u bernard bash -c 'openclaw --version 2>/dev/null || echo unknown'"
  ```
  Compare to latest stable. Check if ≥ v2026.2.23 (compaction bug fix threshold).
- **Output**: Version number logged, upgrade decision made
- **Acceptance**: Version is known and documented

### Task 1.2: Upgrade OpenClaw to Latest Stable
- **Type**: AI (SSH) — skip if already current
- **Input**: Current version from Task 1.1
- **Action**:
  ```bash
  # As bernard user on server:
  npm install -g openclaw@latest
  openclaw --version
  openclaw doctor  # READ ONLY — never use --fix, it nukes config sections
  ```
  Update `infra/openclaw-version.txt` locally to match new version.
  **NOTE**: `openclaw doctor --fix` is permanently banned — it wiped tools.web and pairing state on 2026-03-28. Diagnostics only.
- **Output**: OpenClaw on latest stable, doctor diagnostics reviewed
- **Acceptance**: `openclaw --version` shows latest, any doctor warnings documented (not auto-fixed)

### Task 1.3: Fix openclaw.json Structure + Disable Voice
- **Type**: AI (local) — ENG REVIEW ADDITION: fix duplicate `tools` key
- **Input**: `openclaw/openclaw.json`
- **Action**:
  1. **Fix duplicate `tools` key** — current file has two top-level `tools` blocks (web search at line ~41 and media/audio at line ~107). Merge into a single `tools` block containing both `web` and `media` sections. This is invalid JSON causing silent config loss.
  2. **Disable TTS** — set `"tts": { "auto": "off" }` in the messages block. Voice disabled until voice readiness gate passed (PRD §5.4). Do NOT remove Whisper from the server — just disable in config.
- **Output**: Valid openclaw.json with merged tools block and voice disabled
- **Acceptance**: `jq . openclaw.json` validates without error. No TTS triggers.

### Task 1.4: Configure Model Routing Tiers
- **Type**: AI (local)
- **Input**: `openclaw/openclaw.json`, PRD §6.1 model routing table
- **Action**:
  Update agents.defaults.model to match PRD tier structure:
  - Primary: Sonnet via OpenRouter (persona-holding, reasoning)
  - Heartbeat: Haiku via OpenRouter (low stakes, frequent)
  - Subagents: Haiku (cost-appropriate)
  - Fallback chain: Sonnet → DeepSeek v3.2
  Add heartbeat config: 3hr interval, Haiku model, prompt from PRD §9.
- **Output**: Updated `openclaw/openclaw.json` with tiered model config
- **Acceptance**: Config validates, model tiers match PRD §6.1

### Task 1.5: Set Token Budget Cap
- **Type**: AI (local)
- **Input**: `openclaw/openclaw.json`
- **Action**:
  Research OpenClaw's token budget config options. Add hard cap before ambient tasks run.
  If OpenClaw doesn't support native token caps, document the gap and rely on OpenRouter's spend limit as the control.
- **Output**: Budget cap in config or documented workaround
- **Acceptance**: Cost control mechanism is active

### Task 1.6: Set Up Git+Symlinks Deployment Model
- **Type**: AI (SSH) — CEO REVIEW ADDITION
- **Input**: Server access, GitHub repo URL
- **Action**:
  Replace rsync deployment with git+symlinks. This is the new standard deploy model.
  ```bash
  # On server as bernard user:
  cd ~
  git clone git@github.com:ak-devmode/bernard.git  # or HTTPS

  # Symlink OpenClaw workspace and config to repo
  rm -rf ~/.openclaw/workspace  # remove old copy
  ln -sf ~/bernard/openclaw/workspace ~/.openclaw/workspace
  ln -sf ~/bernard/openclaw/openclaw.json ~/.openclaw/openclaw.json

  # Secure .env
  cp ~/bernard/infra/env.example ~/bernard/.env
  # Edit .env with production API keys
  chmod 600 ~/bernard/.env
  ```
  Add SSH deploy key to GitHub repo (read+write for CC push access).
  Verify OpenClaw picks up symlinked files correctly.

  **From now on, deploy = `git pull` on server. No more rsync.**
- **Output**: Repo cloned on server, symlinks active, .env secured
- **Acceptance**: OpenClaw starts and loads workspace files via symlinks. `git pull` updates files correctly.

### Task 1.7: Initialize Vault Directory Structure
- **Type**: AI (local)
- **Input**: PRD §4.1 vault structure
- **Action**:
  Create directory tree locally under `openclaw/workspace/`:
  ```
  knowledge/
    people/
    projects/
    priorities/
    principles/
    ideas/
    comms/
  artifacts/
  memory/
  learning/
  ```
  Add `.gitkeep` files to empty dirs. Create `knowledge/README.md` explaining the vault structure and ingestion rules.
  Commit and push. On server: `git pull` picks it up via symlinks.
- **Output**: Vault directory tree exists locally and on server
- **Acceptance**: `ls -R` on server shows full tree via symlinks

### Task 1.8: Update Context Compaction Config
- **Type**: AI (local)
- **Input**: `openclaw/openclaw.json`, PRD §9 config
- **Action**:
  Update compaction config with flush prompt from PRD:
  ```json
  "compaction": {
    "mode": "safeguard",
    "flushPrompt": "Distill this session. Keep: decisions made, tasks completed, blockers, open items. Skip: routine exchanges."
  }
  ```
- **Output**: Updated `openclaw/openclaw.json`
- **Acceptance**: Compaction config matches PRD

### Task 1.9: Deploy and Verify
- **Type**: AI (local + SSH)
- **Input**: All updated local files
- **Action**:
  ```bash
  # Local: commit and push all Phase 1 changes
  git add -A && git commit -m "feat: phase 1 foundation config" && git push

  # Server: pull and verify
  ssh ... "sudo -u bernard bash -c 'cd ~/bernard && git pull'"
  ssh ... "sudo -u bernard bash -c 'openclaw gateway status'"
  ```
  Verify: OC version, voice disabled, model routing, vault dirs, heartbeat, compaction config.
- **Output**: Server reflects v2 config via git+symlinks
- **Acceptance**: `openclaw gateway status` healthy, all configs match PRD

---

### CHECKPOINT: Phase 1 Complete
**Review**: Verify on server: OC version, voice disabled, model routing, vault dirs exist, heartbeat interval, git+symlinks working, .env permissions 600
**Resume**: "continue the bernard-v2 plan — Phase 1 complete, start Phase 2"
