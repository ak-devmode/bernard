# Plan: Phase 1 — Foundation & Config

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Draft
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** main

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
  openclaw doctor --fix
  ```
  Update `infra/openclaw-version.txt` locally to match new version.
- **Output**: OpenClaw on latest stable, doctor issues resolved
- **Acceptance**: `openclaw --version` shows latest, `openclaw doctor` reports clean

### Task 1.3: Disable Voice (ElevenLabs + Whisper)
- **Type**: AI (local)
- **Input**: `openclaw/openclaw.json`
- **Action**:
  Remove or disable the TTS config block:
  ```json
  "tts": { "auto": "off" }
  ```
  Comment rationale: voice disabled until voice readiness gate passed (PRD §5.4).
  Do NOT remove Whisper from the server — just disable in config. May re-enable later.
- **Output**: Updated `openclaw/openclaw.json`
- **Acceptance**: No TTS triggers on message send

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

### Task 1.6: Initialize Vault Directory Structure on Server
- **Type**: AI (local + SSH)
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
  Deploy to server via rsync.
- **Output**: Vault directory tree exists locally and on server
- **Acceptance**: `ls -R` on server shows full tree

### Task 1.7: Update Context Compaction Config
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

### Task 1.8: Deploy Config to Server
- **Type**: AI (SSH)
- **Input**: Updated local files
- **Action**:
  ```bash
  rsync -avz openclaw/workspace/ bernard@54.254.76.94:.openclaw/workspace/
  # openclaw.json deployed separately — requires secret interpolation check
  ```
  Verify deployed config on server. Restart OpenClaw if needed.
- **Output**: Server reflects v2 config
- **Acceptance**: `openclaw gateway status` shows healthy, config matches local

---

### CHECKPOINT: Phase 1 Complete
**Review**: Verify on server: OC version, voice disabled, model routing, vault dirs exist, heartbeat interval
**Resume**: "continue the bernard-v2 plan — Phase 1 complete, start Phase 2"
