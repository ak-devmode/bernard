# Plan: Phase 3 — Vault & QMD

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Draft
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** main

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §4.1-4.4

---

## Phase 3: Vault & QMD

### Task 3.1: Pre-populate Project Knowledge Files
- **Type**: AI + HUMAN_REVIEW
- **Input**: CLAUDE.md, USER.md, PRD context
- **Action**:
  Create pre-populated files in `openclaw/workspace/knowledge/projects/`:
  - `pmg.md` — Padma Medical Group: Bali + Surabaya operations, director role, 17 years, healthcare for overseas workers
  - `kalpa.md` — Kalpa Inovasi Digital: healthcare SaaS (WellMed), Go/PHP/AWS stack, founder role
  - `narawangsa.md` — Narawangsa Villas: luxury short-term rentals Bali, operator role
  - `padma-care.md` — Padma Care: medical advocacy for expats in Bali, growth stage
  Each file: one-paragraph description, key facts, current status, known team members.
- **Output**: 4 project files in knowledge/projects/
- **Acceptance**: Alex reviews for accuracy. No sensitive data included.

### Task 3.2: Create Principles & Priorities Templates
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §1, USER.md working style
- **Action**:
  Create `knowledge/principles/decision-frameworks.md`:
  - Pre-populate: "practical over perfect", "control over convenience", "evidence-based", "skeptical of vendor claims"
  - Add section headers for Alex to fill: risk tolerance, delegation philosophy, communication preferences
  Create `knowledge/priorities/current.md`:
  - Template with slots for top 5 priorities, last updated date
  - Instruction: Bernard references this every digest and heartbeat
- **Output**: Principles file (partially populated), priorities template
- **Acceptance**: Structure is useful, pre-populated content is accurate

### Task 3.3: Create People & Ideas Templates
- **Type**: AI
- **Input**: PRD §4.1
- **Action**:
  Create template files (empty structures, not pre-populated — sensitive):
  - `knowledge/people/TEMPLATE.md` — name, relationship, context, last contact, follow-up cadence, notes
  - `knowledge/people/README.md` — explains the people vault and how Bernard uses it for relationship nudges
  - `knowledge/ideas/TEMPLATE.md` — idea title, source, category (whimsy/business/sabbatical), status, notes
  - `knowledge/ideas/README.md` — explains the whimsy pool concept
- **Output**: Template files in people/ and ideas/
- **Acceptance**: Templates are clear enough that Alex can fill them in without further instruction

### Task 3.4: Create Comms Directory Structure
- **Type**: AI
- **Input**: PRD §4.2 (ingestion pipeline)
- **Action**:
  Create structure for `knowledge/comms/`:
  - `email/` — will hold summarized email entries (populated by Phase 5 pipeline)
  - `whatsapp/` — will hold summarized WA entries
  - `chatwoot/` — will hold flagged conversation summaries
  - `README.md` — explains: these are summaries only, never raw input. PII stripped. Criteria list in USER.md.
  Add `.gitkeep` files. This is prep for Phase 5 ingestion pipeline.
- **Output**: Comms directory structure
- **Acceptance**: Directories exist, README explains the rules

### Task 3.5: Research & Configure QMD Backend
- **Type**: AI (SSH + research)
- **Input**: PRD §4.3 QMD config, OpenClaw docs
- **Action**:
  1. SSH into server, check if QMD is available:
     ```bash
     openclaw --help | grep -i qmd
     openclaw memory --help 2>/dev/null
     ```
  2. If built-in: add QMD config to openclaw.json per PRD §4.3 (BM25 + vector + LLM reranking, 5m update interval, 6 max results)
  3. If separate: research installation method, install, configure
  4. If neither: document the gap, evaluate alternatives (simple file search as fallback)
  Point QMD at `workspace/knowledge/` as the indexed directory.
- **Output**: QMD configured and indexing vault, or documented gap with fallback
- **Acceptance**: `openclaw` can search vault content and return relevant results

### Task 3.6: Write Daily Curation Loop Template
- **Type**: AI
- **Input**: PRD §4.4 (daily vault curation loop)
- **Action**:
  Create `openclaw/workspace/CURATION.md` — instructions Bernard follows at end of day:
  1. Shape summary: who communicated with Alex today, topic categories only
  2. Top 10 additions: types of information that would improve vault context
  3. Pruning candidates: personal, irrelevant, or out-of-scope items to remove
  4. Vault health score: is the vault growing in a useful direction?
  Format: terse prose, no bullets (per FEEDBACK.md). Alex reviews and approves.
  Add curation trigger to HEARTBEAT.md (end-of-day check).
- **Output**: CURATION.md template, updated HEARTBEAT.md
- **Acceptance**: Template is actionable. Bernard can follow it without additional context.

### Task 3.7: Update USER.md for Vault Awareness
- **Type**: AI + HUMAN_REVIEW
- **Input**: Current `openclaw/workspace/USER.md`, PRD §4.2
- **Action**:
  Update USER.md to include:
  - Vault reference: "Bernard's knowledge base lives in workspace/knowledge/. Search it before reasoning from scratch."
  - Placeholder sections for ingestion criteria (email criteria list, WA criteria list) — to be filled in Phase 5
  - Current priorities section (template for Alex to fill)
  - Key contacts section (template for Alex to fill)
  Retain existing roles and tools sections.
- **Output**: Updated `openclaw/workspace/USER.md`
- **Acceptance**: USER.md references vault and has placeholder sections for Phase 5

### Task 3.8: Update HEARTBEAT.md for Vault
- **Type**: AI
- **Input**: Current `openclaw/workspace/HEARTBEAT.md`, PRD §11.3
- **Action**:
  Update HEARTBEAT.md to include:
  - Reference vault/priorities for heartbeat checks
  - End-of-day curation trigger (reference CURATION.md)
  - "If nothing urgent: 'All clear [time]' — no noise" rule retained
  - Digest-diff tracking instruction: note which items Alex acted on vs ignored
- **Output**: Updated `openclaw/workspace/HEARTBEAT.md`
- **Acceptance**: Heartbeat instructions reference vault and curation loop

### Task 3.9: Deploy Vault to Server
- **Type**: AI (SSH)
- **Input**: All vault files created in this phase
- **Action**:
  ```bash
  rsync -avz openclaw/workspace/ bernard@54.254.76.94:.openclaw/workspace/
  ```
  Verify vault structure on server. Test QMD indexing if configured.
- **Output**: Vault live on server, QMD indexing
- **Acceptance**: `ls -R workspace/knowledge/` shows full tree, QMD returns results

---

### CHECKPOINT: Phase 3 Complete
**Review**: Browse vault on server. Verify QMD search works. Review project files for accuracy. Fill in people/ templates and priorities.
**Resume**: "continue the bernard-v2 plan — Phase 3 complete, start Phase 4"
