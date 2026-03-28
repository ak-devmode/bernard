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
