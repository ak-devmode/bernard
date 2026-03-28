# Plan: Phase 5 — Ingestion Pipeline

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Ready to execute
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2

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

### Task 5.2: Build Unified Ingestion Pipeline — ENG REVIEW: merged from separate email+WA scripts
- **Type**: AI
- **Input**: PRD §3.4 (input hygiene), §4.2 (ingestion pipeline)
- **Action**:
  Create `tools/ingest.py` — single script handling both sources via `--source` flag:
  ```bash
  python3 tools/ingest.py --source email < raw_email.txt
  python3 tools/ingest.py --source whatsapp < wa_export.txt
  python3 tools/ingest.py --source email --dry-run < raw_email.txt
  ```

  Core pipeline (shared for all sources):
  1. Input: raw text from stdin or file
  2. PII strip pass (calls `pii_strip.py`): regex for emails, phones, ID numbers + LLM verification
  3. Summarize using Haiku (cheapest model, sufficient for summarization)
  4. Dedup check: hash subject+date, skip if output file exists (CEO review addition)
  5. Output: structured markdown to `knowledge/comms/{source}/YYYY-MM-DD-{slug}.md`

  Output format (email):
  ```markdown
  ---
  date: YYYY-MM-DD
  from: {role/relationship, not name}
  topic: {one-line summary}
  source: email
  ---
  {2-3 sentence summary}
  **Action items:** {list or "none"}
  **Follow-up by:** {date or "none"}
  ```

  Output format (whatsapp/chatwoot) adds:
  - `participants:` field (roles, not names)
  - `source: whatsapp|chatwoot`

  Source-specific logic lives in `parse_input()` — the rest of the pipeline is shared.
  Include `--dry-run` mode that shows output without writing to vault.

- **Output**: `tools/ingest.py` with `--source email|whatsapp`, dry-run support, and dedup
- **Acceptance**: Dry run on sample email and WA conversation both produce clean, PII-stripped summaries. Running twice doesn't create duplicates.

### Task 5.3: Unit Tests for ingest.py — ENG REVIEW ADDITION
- **Type**: AI
- **Input**: `tools/ingest.py` from Task 5.2
- **Action**:
  Create `tools/test_ingest.py` with tests covering:
  1. `parse_input()` — email format parsed correctly, WA format parsed correctly, malformed input raises clear error
  2. `dedup_check()` — returns True when file exists, False when new
  3. `write_vault_entry()` — output file created in correct directory with correct frontmatter
  4. Bad/empty input handling — graceful failure, no partial writes
  5. `--dry-run` flag — no files written to disk

  Run with: `python3 -m pytest tools/test_ingest.py`
- **Output**: `tools/test_ingest.py` with ≥5 test cases
- **Acceptance**: All tests pass. `pytest` exits clean.

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

### Task 5.5: Configure ContextEngine afterTurn Hook — renumbered from 5.5 (was 5.6 before merge)
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
  git add -A && git commit -m "feat: phase 5 ingestion pipeline" && git push
  ssh ... "sudo -u bernard bash -c 'cd ~/bernard && git pull && pip install -r tools/requirements.txt'"
  ```
  Test pipelines work on server environment.
- **Output**: Pipelines functional on server
- **Acceptance**: `python3 tools/ingest-email.py --dry-run < sample.txt` works on server

---

### CHECKPOINT: Phase 5 Complete
**Review**: Run both pipelines on real data. Review vault entries for quality and PII handling. Verify afterTurn hook fires on negative signals. Check QMD indexes new entries.
**Resume**: "continue the bernard-v2 plan — Phase 5 complete, start Phase 6"
