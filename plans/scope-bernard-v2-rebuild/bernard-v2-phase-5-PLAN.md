# Plan: Phase 5 — Ingestion Pipeline

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Draft
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** main

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §3.4, §4.2, §5.2, §9 Phase 3

---

## Phase 5: Ingestion Pipeline

### Task 5.1: Define Email Criteria List
- **Type**: AI + HUMAN_REVIEW
- **Input**: USER.md, PRD §4.2
- **Action**:
  Add to `openclaw/workspace/USER.md` an "Ingestion Criteria" section:

  **Email criteria** (Alex to review and customize):
  - Include: emails from known contacts list, emails mentioning PMG/Kalpa/Narawangsa/Padma Care, emails with action items or deadlines
  - Exclude: newsletters, marketing, automated notifications, spam
  - Strip: email addresses, phone numbers, ID numbers, financial details beyond category
  - Summarize: sender, topic, action items, deadline if any, sentiment

  **WA/Chatwoot criteria**:
  - Include: business-related threads from approved contacts/groups
  - Exclude: personal conversations, group noise
  - Strip: same PII rules as email
  - Summarize: participants (role only, not name in vault), topic, outcome, follow-up needed

  Format as clear rules Bernard can follow programmatically.
- **Output**: Updated USER.md with ingestion criteria
- **Acceptance**: Alex confirms criteria list is complete and accurate

### Task 5.2: Build Email Summarization Pipeline
- **Type**: AI
- **Input**: PRD §3.4 (input hygiene), §4.2 (ingestion pipeline)
- **Action**:
  Create `tools/ingest-email.py` (or .js — match server stack):
  1. Input: raw email text (from stdin or file)
  2. Summarize using Haiku (cheapest model, sufficient for summarization)
  3. PII strip pass: regex for emails, phones, ID numbers + LLM verification
  4. Output: structured markdown to `knowledge/comms/email/YYYY-MM-DD-{subject-slug}.md`

  Output format:
  ```markdown
  ---
  date: YYYY-MM-DD
  from: {role/relationship, not name}
  topic: {one-line summary}
  ---
  {2-3 sentence summary}
  **Action items:** {list or "none"}
  **Follow-up by:** {date or "none"}
  ```

  Include dry-run mode that shows output without writing to vault.
- **Output**: `tools/ingest-email.py` with dry-run support
- **Acceptance**: Dry run on sample email produces clean, PII-stripped summary

### Task 5.3: Build WA/Chatwoot Summarization Pipeline
- **Type**: AI
- **Input**: PRD §3.4, §4.2
- **Action**:
  Create `tools/ingest-wa.py`:
  1. Input: WA/Chatwoot conversation export (text format)
  2. Summarize using Haiku
  3. PII strip: same rules as email pipeline
  4. Output: structured markdown to `knowledge/comms/whatsapp/YYYY-MM-DD-{topic-slug}.md`

  Same output format as email but with:
  - `participants:` field (roles, not names)
  - `source: whatsapp|chatwoot`

  Include dry-run mode.
- **Output**: `tools/ingest-wa.py` with dry-run support
- **Acceptance**: Dry run on sample conversation produces clean summary

### Task 5.4: PII Stripping Utility
- **Type**: AI
- **Input**: PRD §3.4 (PII stripped before vault ingestion)
- **Action**:
  Create `tools/pii_strip.py` — shared utility used by both pipelines:
  - Regex patterns: email addresses, phone numbers (Indonesian + international), ID numbers (KTP, passport), credit card numbers
  - LLM verification pass: send stripped text to Haiku with "identify any remaining PII" prompt
  - Replace PII with category tags: `[EMAIL]`, `[PHONE]`, `[ID_NUMBER]`, `[FINANCIAL]`
  - Log stripped items count (not content) for audit

  Unit tests with sample data containing various PII formats.
- **Output**: `tools/pii_strip.py` with tests
- **Acceptance**: All known PII patterns caught, LLM verification finds no leaks

### Task 5.5: Configure ContextEngine afterTurn Hook
- **Type**: AI (SSH + research)
- **Input**: PRD §5.2 (afterTurn hook for FEEDBACK.md)
- **Action**:
  1. Research OpenClaw's ContextEngine afterTurn hook (v2026.3.7+):
     ```bash
     openclaw --version  # confirm ≥ v2026.3.7
     openclaw hooks --help 2>/dev/null
     ```
  2. If available: configure afterTurn hook that:
     - Detects dissatisfaction signals (pushback, significant edits, ignored output)
     - Writes behavioral correction to FEEDBACK.md automatically
     - Does NOT require Alex to explicitly ask Bernard to learn
  3. If not available (version too old): document the gap, create a manual "Bernard, note this" command as interim
  4. Add hook config to openclaw.json
- **Output**: afterTurn hook configured, or documented gap with workaround
- **Acceptance**: Bernard auto-learns from negative signals without explicit instruction

### Task 5.6: First Vault Ingestion Test
- **Type**: AI + HUMAN_REVIEW
- **Input**: Pipelines from Tasks 5.2-5.4
- **Action**:
  1. Alex provides 2-3 sample emails and 1 WA conversation (can be sanitized samples)
  2. Run pipelines in dry-run mode, show output
  3. Alex reviews: is the summary useful? Is PII actually stripped? Is the format right?
  4. If approved: run for real, write to vault
  5. Verify QMD picks up new files (if configured in Phase 3)
- **Output**: First real vault entries in knowledge/comms/
- **Acceptance**: Alex approves summary quality and PII handling

### Task 5.7: Deploy Pipelines to Server
- **Type**: AI (SSH)
- **Input**: All tools/ files
- **Action**:
  ```bash
  rsync -avz tools/ bernard@54.254.76.94:~/bernard/tools/
  # Install Python dependencies if needed
  ssh ... "cd ~/bernard && pip install -r tools/requirements.txt"
  ```
  Test pipelines work on server environment.
- **Output**: Pipelines functional on server
- **Acceptance**: `python3 tools/ingest-email.py --dry-run < sample.txt` works on server

---

### CHECKPOINT: Phase 5 Complete
**Review**: Run both pipelines on real data. Review vault entries for quality and PII handling. Verify afterTurn hook fires on negative signals. Check QMD indexes new entries.
**Resume**: "continue the bernard-v2 plan — Phase 5 complete, start Phase 6"
