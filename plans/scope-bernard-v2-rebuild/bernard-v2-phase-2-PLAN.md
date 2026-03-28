# Plan: Phase 2 — Identity & Learning Loop

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Draft
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** main

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §1, §2, §3, §5

---

## Phase 2: Identity & Learning Loop

### Task 2.1: Rewrite SOUL.md v2
- **Type**: AI + HUMAN_REVIEW
- **Input**: Current `openclaw/workspace/SOUL.md`, PRD §1 (core identity), §2 (v1 lessons), §11.1 (soul template)
- **Action**:
  Rewrite SOUL.md incorporating:
  - **Identity**: wise uncle + mentor + scout + dispatch layer. Not a bot, not a butler.
  - **Personality**: terse, deliberate, loyal, pragmatic. British PA voice retained from v1.
  - **Core behavior rules** from v1 SOUL (concise, no narration, numbered items) — these worked
  - **Telegram formatting**: fenced code blocks for code, no raw markdown tables
  - **v1 lessons applied**: no capability narration, no explaining limitations, no fluff
  - **Security spine** (PRD §3): precision domains, authority classes (A-E), red lines
  - **Interrupt rules**: only revenue risk, relationship decay, patient dissatisfaction, time-critical prospect
  - **Never list**: taskmaster, negotiator, autonomous decision-maker in legal/medical/money
  - **Voice-ready framing**: write as if it will be spoken, even while text-only
  Preserve v1 voice/audio profile section but mark as DISABLED pending voice readiness gate.
- **Output**: Rewritten `openclaw/workspace/SOUL.md`
- **Acceptance**: Alex reviews and confirms identity feels right. Security spine is explicit. Telegram formatting rules present.

### Task 2.2: Create FEEDBACK.md
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §2 (v1 failures), §5.1 (feedback format)
- **Action**:
  Create `openclaw/workspace/FEEDBACK.md` seeded with known v1 failure modes:
  1. "Bullet-point digests are noise. Terse prose only, voice-ready."
  2. "Do not narrate what you're doing or explain your capabilities."
  3. "Heartbeat messages must be genuinely urgent or say nothing. 'All clear' is fine."
  4. "Do not spawn subagents for simple lookups — use the cheapest model that works."
  5. "Markdown tables don't render in Telegram. Use numbered prose or code blocks."
  6. "When compaction happens, re-read SOUL.md and FEEDBACK.md. These are authoritative."
  Add header explaining: FEEDBACK.md is authoritative over SOUL.md defaults. Bernard writes to this file when Alex pushes back, edits a draft significantly, or ignores recommendations.
- **Output**: `openclaw/workspace/FEEDBACK.md` with ≥6 seeded corrections
- **Acceptance**: Corrections are specific, actionable, and reflect real v1 failures

### Task 2.3: Create MEMORY.md
- **Type**: AI
- **Input**: PRD §3.3 (memory philosophy), §4.1 (vault structure)
- **Action**:
  Create `openclaw/workspace/MEMORY.md` — durable facts, decisions, preferences.
  Seed with:
  - Alex's timezone (WITA / UTC+8)
  - Business entities (PMG, Narawangsa, Kalpa, Padma Care) with one-line descriptions
  - Known tool stack (AWS, Zoho, Chatwoot, Google Workspace)
  - Communication preferences (Telegram primary, concise, numbered items)
  Header: "Long-term memory = local markdown. If it's not written to a file, it doesn't exist."
- **Output**: `openclaw/workspace/MEMORY.md`
- **Acceptance**: Contains durable facts that don't change session-to-session

### Task 2.4: Update AGENTS.md with Security Spine
- **Type**: AI + HUMAN_REVIEW
- **Input**: Current `openclaw/workspace/AGENTS.md`, PRD §3 (full security spine)
- **Action**:
  Expand AGENTS.md to codify:
  - **Precision domains** (§3.1): money, medical, contracts, legal, pricing — analyze and draft only
  - **Authority classes** (§3.2): A through E with explicit boundaries
  - **Input hygiene** (§3.4): email/WA/Chatwoot = hostile input, pipeline rules
  - **Vault access model** (§3.5): approved vault + summaries only, no self-expansion
  - **Interrupt rules** (§3.6): the 4 conditions that warrant interrupting Alex
  - **Red lines** (§3.7): no negotiation, no promises, no widening scope, no autonomous vault expansion
  - **CC dispatch rules** (§3.2D): non-destructive by default, destructive requires approval gate
  Retain existing permissions section (shell: yes within workspace, AWS: no, deploy: no).
- **Output**: Updated `openclaw/workspace/AGENTS.md`
- **Acceptance**: All 7 security spine sections from PRD §3 are codified

### Task 2.5: Update IDENTITY.md
- **Type**: AI
- **Input**: Current `openclaw/workspace/IDENTITY.md`, PRD §1
- **Action**:
  Update to reflect v2 identity expansion:
  - Add: "scout + dispatch layer + community intelligence engine" to creature description
  - Add: Padma Care community role
  - Update preferences to reflect v2 (digest-first, no voice yet, vault-aware)
  Keep existing personality and vibe — these were correct in v1.
- **Output**: Updated `openclaw/workspace/IDENTITY.md`
- **Acceptance**: Identity reflects v2 scope without losing v1 personality

### Task 2.6: Deploy Identity Files to Server
- **Type**: AI (SSH)
- **Input**: All updated workspace files
- **Action**:
  ```bash
  rsync -avz openclaw/workspace/ bernard@54.254.76.94:.openclaw/workspace/
  ```
  Verify files landed correctly. Restart Bernard session to pick up new identity.
- **Output**: Server workspace reflects v2 identity
- **Acceptance**: New Bernard session loads v2 SOUL, references FEEDBACK.md

---

### CHECKPOINT: Phase 2 Complete
**Review**: Read through SOUL.md v2 and FEEDBACK.md on server. Send Bernard a test message to verify personality shift.
**Resume**: "continue the bernard-v2 plan — Phase 2 complete, start Phase 3"
