# Progress Log: Phase 1 — Foundation & Config

## Session: 2026-03-28T16:00:00+08:00

### Phase 0: Pre-flight
- **Status**: ✅ DONE
- **Completed**: 2026-03-28T16:30:00+08:00
- **Paths verified**: scope.md, progress.md exist. PRD reference is external (not file path).
- **Parent scope**: plans/scope-bernard-v2-rebuild/scope.md
- **Branch**: bernard-v2 (created and checked out)
- **Issues**: None

### Task 1.1: Check Current OpenClaw Version
- **Status**: ✅ DONE
- **Started**: 2026-03-28T15:30:00+08:00
- **Completed**: 2026-03-28T15:35:00+08:00
- **What was done**: Server already on v2026.3.24 (upgraded earlier today). Above compaction bug fix threshold (≥v2026.2.23). Version pin updated locally.
- **Files modified**: `infra/openclaw-version.txt`
- **Issues**: None

### Task 1.2: Upgrade OpenClaw to Latest Stable
- **Status**: ⏭️ SKIPPED
- **What was done**: Server already on v2026.3.24 (latest). No upgrade needed. `openclaw doctor --fix` permanently banned — it wiped tools.web config and pairing state on 2026-03-28. Diagnostics-only policy documented in plan and CLAUDE.md.
- **Issues**: doctor --fix incident documented as known gotcha

### Task 1.6: Set Up Git+Symlinks Deployment Model
- **Status**: ✅ DONE
- **Started**: 2026-03-28T15:40:00+08:00
- **Completed**: 2026-03-28T16:10:00+08:00
- **What was done**: Generated SSH deploy key for bernard user. Added to GitHub as deploy key. Configured SSH over port 443 (github.com → ssh.github.com:443) to work with egress firewall. Cloned repo at ~/bernard/ on server. Created symlinks: ~/.openclaw/workspace → repo, ~/.openclaw/openclaw.json → repo. Created deploy.sh and remote-deploy.sh. Tested full push → pull → restart → health check cycle. SSH direct as bernard (not sudo).
- **Files modified**: `infra/deploy.sh`, `infra/remote-deploy.sh`, `CLAUDE.md`, server: `~/.ssh/config`, `~/.ssh/id_ed25519*`, `~/.openclaw/workspace` (symlink), `~/.openclaw/openclaw.json` (symlink)
- **Issues**: Initial deploy.sh had insufficient health check timeout (fixed). sudo -u bernard lacks DBUS session bus for systemctl --user (resolved by SSHing directly as bernard).

### Task 1.3: Fix openclaw.json Structure + Disable Voice
- **Status**: ✅ DONE
- **Started**: 2026-03-28T16:15:00+08:00
- **Completed**: 2026-03-28T16:20:00+08:00
- **What was done**: Duplicate `tools` key already fixed in prep commit (merged web + media into single block). TTS disabled: `tts.auto` set to `"off"`, ElevenLabs config removed. Voice stays off until readiness gate (2 weeks useful text digests).
- **Files modified**: `openclaw/openclaw.json`
- **Issues**: None

### Task 1.4: Configure Model Routing Tiers
- **Status**: ✅ DONE
- **Started**: 2026-03-28T16:20:00+08:00
- **Completed**: 2026-03-28T16:25:00+08:00
- **What was done**: Primary: Claude Sonnet 4. Heartbeat: Claude Haiku 4. Subagents: Claude Haiku 4. Added Haiku and DeepSeek v3 to model aliases. Fallback chain (Sonnet → DeepSeek) documented in AGENTS.md — `agents.defaults.fallback` not supported by OpenClaw schema.
- **Files modified**: `openclaw/openclaw.json`
- **Issues**: `fallback`, `heartbeat.interval`, `compaction.flushPrompt` all rejected by OpenClaw v2026.3.24 strict schema. Removed invalid keys to restore gateway. Fallback and flush prompt handled via workspace instructions instead.

### Task 1.5: Set Token Budget Cap
- **Status**: ✅ DONE (documented gap)
- **Started**: 2026-03-28T16:25:00+08:00
- **Completed**: 2026-03-28T16:26:00+08:00
- **What was done**: OpenClaw has no native token/spend budget config. Cost control relies on: (1) OpenRouter spend limit at openrouter.ai, (2) Haiku for heartbeat + subagents, (3) AGENTS.md cost awareness rules.
- **Files modified**: None
- **Issues**: No native budget support — acceptable, OpenRouter limit is the control.

### Task 1.7: Initialize Vault Directory Structure
- **Status**: ✅ DONE
- **Started**: 2026-03-28T16:26:00+08:00
- **Completed**: 2026-03-28T16:28:00+08:00
- **What was done**: Created knowledge/ (people, projects, priorities, principles, ideas, comms), artifacts/, memory/, learning/ under openclaw/workspace/. Added .gitkeep to all dirs. Created knowledge/README.md with structure docs, ingestion rules, naming conventions.
- **Files modified**: `openclaw/workspace/knowledge/README.md`, 9x `.gitkeep` files
- **Issues**: None

### Task 1.8: Update Context Compaction Config
- **Status**: ⏭️ ADJUSTED
- **Started**: 2026-03-28T16:28:00+08:00
- **Completed**: 2026-03-28T16:30:00+08:00
- **What was done**: `compaction.flushPrompt` is not a recognized OpenClaw config key. Compaction stays at `"mode": "safeguard"` (default). Flush prompt will be implemented via workspace instructions (HEARTBEAT.md or AGENTS.md) in Phase 2 instead.
- **Files modified**: `openclaw/openclaw.json` (added then removed flushPrompt)
- **Issues**: OpenClaw schema doesn't support flushPrompt. Deferred to workspace-level instructions.

### Task 1.9: Deploy and Verify
- **Status**: ✅ DONE
- **Started**: 2026-03-28T16:30:00+08:00
- **Completed**: 2026-03-28T16:35:00+08:00
- **What was done**: Pushed all Phase 1 changes via `bash infra/remote-deploy.sh`. Verified on server: OC v2026.3.24, gateway healthy, TTS off, Sonnet primary, Haiku for heartbeat+subagents, compaction safeguard, all vault dirs present, symlinks active.
- **Files modified**: None (deploy only)
- **Issues**: First deploy attempt crashed gateway due to invalid config keys (fallback, heartbeat.interval, flushPrompt). Fixed and redeployed successfully.

## Session: 2026-03-28T21:00:00+08:00

### Post-Phase-1: Infra fixes
- **VM crash recovery**: Instance crashed during heartbeat config exploration. Force-stopped, restarted. IP changed (was not EIP).
- **Elastic IP**: Associated orphaned EIP `54.251.203.204` to Bernard instance. Tagged as "Bernard-EIP". Updated all repo IP references. Tagged all 8 EIPs across the account for clarity.
- **Heartbeat interval**: Discovered correct config key is `heartbeat.every` (not `interval`). Source: `heartbeat-summary-DvQBtBZ6.js`. Default was `30m`, set to `3h`. Verified in logs — no schema errors, heartbeat running clean.
- **DNS**: Alex updated `bernard.finengine.co` to point to new EIP.
- **OpenClaw config schema lessons**: Valid heartbeat keys: `every`, `model`, `prompt`, `target`, `ackMaxChars`, `activeHours`. Duration format: `parseDurationMs()` with default unit minutes (e.g., "3h", "30m", "1d").

### Phase 1: COMPLETE
All tasks done. Gateway healthy. Ready for Phase 2.
