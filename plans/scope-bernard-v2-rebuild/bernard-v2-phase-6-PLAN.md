# Plan: Phase 6 — CC Dispatch (ACP Bridge)

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Ready to execute
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §7, §9 Phase 4
- `bernard-cc-bridge-module.md` (referenced in PRD — full detail doc)

---

## Phase 6: CC Dispatch (ACP Bridge)

### Task 6.1: Install Claude Code on Server
- **Type**: AI (SSH)
- **Input**: Server access, Node.js already installed
- **Action**:
  ```bash
  ssh -i ~/.ssh/awk_sandbox.pem ubuntu@54.254.76.94
  # As bernard user:
  sudo -u bernard bash -c 'npm install -g @anthropic-ai/claude-code'
  # Verify:
  sudo -u bernard bash -c 'claude --version'
  ```
  If auth is needed: document the auth flow for Alex to complete interactively.
  Claude Code needs an Anthropic API key — add to `.env`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ```
- **Output**: Claude Code installed and authenticated on server
- **Acceptance**: `claude --version` returns a version, auth is configured

### Task 6.2: Install acpx & Configure ACP in openclaw.json — ENG REVIEW: added config block
- **Type**: AI (SSH + local)
- **Input**: PRD §7 (ACP dispatch), §9 Phase 4
- **Action**:
  Install acpx:
  ```bash
  sudo -u bernard bash -c 'npm install -g acpx@latest'
  # Verify:
  sudo -u bernard bash -c 'acpx --version'
  ```
  If acpx doesn't exist as a standalone package, research the correct ACP bridge method:
  - Check OpenClaw docs for native ACP support
  - Check if `openclaw exec` is the native command
  - Fall back to custom bridge script if needed

  Add ACP config block to `openclaw/openclaw.json`:
  ```json
  "acp": {
    "enabled": true,
    "dispatch": {
      "enabled": true,
      "backend": "acpx"
    }
  }
  ```
  Verify config validates with `jq . openclaw.json`.
- **Output**: ACP bridge tool installed, openclaw.json updated with ACP config
- **Acceptance**: A working command exists to dispatch tasks from OpenClaw to CC. Config validates.

### Task 6.3: Test Basic ACP Dispatch
- **Type**: AI (SSH)
- **Input**: Working ACP tool from Task 6.2
- **Action**:
  Run a simple, non-destructive test:
  ```bash
  acpx openclaw exec "summarize the current session state"
  # Or whatever the correct invocation is
  ```
  Verify:
  - Task dispatches to CC
  - CC executes and returns result
  - Result is captured and available to Bernard
  Document the exact invocation syntax that works.
- **Output**: Confirmed working dispatch command, documented syntax
- **Acceptance**: Round-trip dispatch works: Bernard → CC → result → Bernard

### Task 6.4: Wire ACP Dispatch into Bernard's AGENTS.md
- **Type**: AI
- **Input**: Working dispatch syntax from Task 6.3, PRD §3.2D (authority class D)
- **Action**:
  Update `openclaw/workspace/AGENTS.md` to include CC dispatch instructions:
  - When Alex requests a dev task, Bernard dispatches via ACP
  - Non-destructive operations (read, search, create PR, create branch): dispatch immediately
  - Destructive operations (push, deploy, merge, delete): require explicit ACK from Alex before proceeding
  - Log format: timestamped JSONL under session

  Add dispatch examples to AGENTS.md:
  - "Create a PR" → dispatch, return URL
  - "Fix this bug" → dispatch, return diff for review
  - "Deploy to staging" → STOP, ask Alex for explicit approval
- **Output**: Updated AGENTS.md with dispatch rules and examples
- **Acceptance**: Authority class D rules are explicit and unambiguous

### Task 6.5: Test PR Creation End-to-End
- **Type**: AI + HUMAN_REVIEW
- **Input**: Working dispatch, a test repo
- **Action**:
  Test the full PRD §7.1 use case:
  1. Send Bernard a Telegram message: "Create a PR for [test-repo], feat/test-branch targeting develop, standard template"
  2. Bernard dispatches to CC via ACP
  3. CC creates branch, makes a trivial change, creates PR
  4. PR URL returned to Bernard
  5. Bernard delivers URL via Telegram

  If no test repo available: use the bernard repo itself with a test branch.
  Document the full flow and any issues.
- **Output**: End-to-end PR creation tested, flow documented
- **Acceptance**: PR URL arrives in Telegram from Bernard

### Task 6.6: Configure Approval Gate
- **Type**: AI
- **Input**: PRD §7 (approval gate for destructive ops)
- **Action**:
  Implement approval gate mechanism:
  - Before destructive operations, Bernard sends Alex a confirmation request via Telegram
  - Format: "CC wants to: [action description]. Approve? (yes/no)"
  - Timeout: 10 minutes, then abort with message
  - Log all approval requests and responses

  Implementation depends on OpenClaw's native capabilities:
  - If OpenClaw has built-in approval flows: configure them
  - If not: add approval logic to AGENTS.md as behavioral instruction + create a simple approval script in tools/
- **Output**: Approval gate working for destructive ops
- **Acceptance**: Destructive operation blocked until Alex confirms

### Task 6.7: Configure JSONL Logging
- **Type**: AI (SSH)
- **Input**: PRD §7 (log format)
- **Action**:
  Ensure ACP dispatch sessions produce timestamped JSONL logs.
  Check if OpenClaw/CC handle this natively. If not, create a wrapper:
  ```bash
  # tools/cc-dispatch.sh — wrapper that logs before/after
  ```
  Log location: under OpenClaw's session directory (follows existing pattern).
- **Output**: JSONL logging active for all CC dispatches
- **Acceptance**: After a dispatch, JSONL log file exists with task, result, timestamps

### Task 6.8: Deploy & Verify
- **Type**: AI (SSH)
- **Input**: All Phase 6 files
- **Action**:
  Deploy updated AGENTS.md and any tools/ scripts to server.
  Run a final end-to-end test of the full dispatch flow.
  Update `infra/env.example` to include ANTHROPIC_API_KEY placeholder.
- **Output**: CC dispatch fully operational on server
- **Acceptance**: Full flow works: Telegram → Bernard → CC → result → Telegram

---

### CHECKPOINT: Phase 6 Complete
**Review**: Test 2-3 real dispatch scenarios. Verify approval gate blocks destructive ops. Check JSONL logs are clean.
**Resume**: "continue the bernard-v2 plan — Phase 6 complete, start Phase 7"
