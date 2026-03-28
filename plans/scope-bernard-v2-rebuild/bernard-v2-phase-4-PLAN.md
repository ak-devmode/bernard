# Plan: Phase 4 — Digest & Phase 2 Skills

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Ready to execute
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §9 Phase 2, §11 (skills backlog)

---

## Phase 4: Digest & Phase 2 Skills

### Task 4.1: Build Daily Digest Template
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §9 Phase 2 (digest format), §5.3 (digest diff tracking), FEEDBACK.md
- **Action**:
  Create `openclaw/workspace/DIGEST.md` — instructions Bernard follows for daily digest:

  **Digest structure** (terse prose, voice-ready, no bullet points):
  1. Top 3 priorities today — pulled from knowledge/priorities/current.md, cross-referenced with calendar
  2. Dropped balls — items from previous days that had no follow-up or response
  3. Relationship nudge — one person from knowledge/people/ who hasn't been contacted beyond their cadence
  4. Whimsy item — one thing from knowledge/ideas/ or a serendipitous connection

  **Format rules**:
  - Terse prose paragraphs, not bullets or tables
  - Numbered sections so Alex can reply "expand 2" or "skip 4"
  - Voice-ready: written as if it will be spoken aloud
  - Max 200 words total unless Alex asks for detail

  **Digest-diff tracking**:
  - After digest delivery, Bernard notes in `learning/digest-log.md` which items Alex responded to, asked about, or ignored
  - Over time, this informs what belongs in top 3 vs noise
- **Output**: `openclaw/workspace/DIGEST.md`, `openclaw/workspace/learning/digest-log.md` (empty, with header)
- **Acceptance**: Digest template produces output Alex finds useful. Format is voice-ready.

### Task 4.2: Dropped Ball Tracking Skill
- **Type**: AI
- **Input**: PRD §11 (dropped ball tracking and nudges)
- **Action**:
  Create `openclaw/workspace/knowledge/skills/dropped-balls.md`:
  - **What it does**: Tracks commitments Alex made (in messages, meetings, digests) and flags when follow-up hasn't happened
  - **Data source**: Daily conversations, email summaries (when ingestion is live), calendar
  - **Storage**: `knowledge/tracking/dropped-balls.md` — running list with: item, promised to whom, date committed, follow-up deadline, status
  - **Trigger**: Checked at each digest. Items >48hrs without follow-up get flagged.
  - **Tone**: "This is still open" — not "you forgot this." Never a taskmaster.
  Create `knowledge/tracking/dropped-balls.md` with header and empty table.
- **Output**: Skill instruction file + tracking file
- **Acceptance**: Bernard can identify and flag overdue items in digest

### Task 4.3: Board Meeting Topic Accumulator
- **Type**: AI
- **Input**: PRD §11 (board meeting topic accumulator)
- **Action**:
  Create `openclaw/workspace/knowledge/skills/board-topics.md`:
  - **What it does**: Accumulates topics for Kalpa and Padma board meetings as they come up in conversation
  - **Storage**: `knowledge/tracking/board-topics-kalpa.md` and `knowledge/tracking/board-topics-padma.md`
  - **Format**: Topic, source (conversation/email/observation), date noted, priority (discuss/FYI/decision-needed)
  - **Trigger**: Bernard proactively captures topics when conversations touch on strategic decisions, financial updates, or governance matters
  - **Pre-meeting**: Bernard produces a draft agenda sorted by priority 48hrs before known meeting date
  Create tracking files with headers.
- **Output**: Skill instruction file + 2 tracking files
- **Acceptance**: Topics accumulate naturally from conversation

### Task 4.4: Staff Check-in Accountability
- **Type**: AI
- **Input**: PRD §11 (staff check-in accountability — load concept, hold to schedule)
- **Action**:
  Create `openclaw/workspace/knowledge/skills/staff-checkins.md`:
  - **What it does**: Tracks scheduled check-ins with team leads, flags when they're overdue
  - **Storage**: `knowledge/tracking/staff-checkins.md` — person, role, check-in cadence, last check-in date, next due, notes
  - **Load concept**: Bernard tracks what's on each person's plate (from check-in notes) and flags when someone seems overloaded or underutilized
  - **Trigger**: Checked weekly. Overdue check-ins flagged in digest. Load summary available on request.
  - **Privacy**: No performance judgments — just schedule adherence and workload signals
  Create tracking file with template rows (Alex fills in real names).
- **Output**: Skill instruction file + tracking template
- **Acceptance**: Schedule tracking is clear, load concept is non-judgmental

### Task 4.5: Narawangsa Pricing Heuristic
- **Type**: AI
- **Input**: PRD §11 (periodic market scrape → digest)
- **Action**:
  Create `openclaw/workspace/knowledge/skills/narawangsa-pricing.md`:
  - **What it does**: Periodically checks competitor pricing on Airbnb/Booking.com for comparable Bali luxury villas
  - **Storage**: `knowledge/tracking/narawangsa-pricing.md` — date, competitor, nightly rate, occupancy signals, notes
  - **Trigger**: Weekly scrape (manual for now — automated when web tools are wired). Summary in weekly digest.
  - **Output format**: "Your current rate is X. Comparable properties are ranging Y-Z. [No recommendation — data only.]"
  - **Note**: This is an instrument panel item (Authority Class C) — factual + light encouragement, never pricing decisions
  Create tracking file with header.
- **Output**: Skill instruction file + tracking template
- **Acceptance**: Clear data-only format, no autonomous pricing decisions

### Task 4.6: House Project Ledger
- **Type**: AI
- **Input**: PRD §11 (stack ranked, blockers, last update)
- **Action**:
  Create `openclaw/workspace/knowledge/skills/house-projects.md`:
  - **What it does**: Maintains a stack-ranked list of house/villa projects with status, blockers, and last update
  - **Storage**: `knowledge/tracking/house-projects.md` — project name, priority rank, status (planned/in-progress/blocked/done), blocker, last update date, notes
  - **Trigger**: Checked weekly. Stale items (>2 weeks no update) flagged in digest.
  - **Tone**: Gentle nudge on stale items, not a project manager
  Create tracking file with template.
- **Output**: Skill instruction file + tracking template
- **Acceptance**: Ledger is scannable, stale detection works

### Task 4.7: Create Tracking Directory & Deploy
- **Type**: AI (local + SSH)
- **Input**: All tracking files from Tasks 4.2-4.6
- **Action**:
  Ensure `knowledge/tracking/` directory exists with all files.
  Ensure `learning/` directory exists with digest-log.md.
  Deploy all new files to server:
  ```bash
  git add -A && git commit -m "feat: phase 4 digest and skills" && git push
  ssh ... "sudo -u bernard bash -c 'cd ~/bernard && git pull'"
  ```
- **Output**: All Phase 4 files on server
- **Acceptance**: Bernard can reference all skill files and tracking templates

---

### CHECKPOINT: Phase 4 Complete
**Review**: Send Bernard a test message asking for a daily digest. Evaluate: does it follow the template? Is it terse prose? Does it reference vault? Use for 2 weeks to evaluate quality before proceeding to Phase 5.
**Resume**: "continue the bernard-v2 plan — Phase 4 complete, start Phase 5"
