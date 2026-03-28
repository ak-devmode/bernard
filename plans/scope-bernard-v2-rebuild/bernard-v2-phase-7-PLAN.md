# Plan: Phase 7 — Padma Care Community Engine

**Version:** 0.1
**Date:** 2026-03-28
**Author:** Alex
**Status:** Ready to execute
**Parent scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2

## Related Docs
- `plans/scope-bernard-v2-rebuild/scope.md` — parent scope
- `plans/scope-bernard-v2-rebuild/progress.md` — progress tracker
- PRD: bernard-master-plan-v2 §10 (entire section)

---

## Phase 7: Padma Care Community Engine

### Task 7.1: Codify Padma Care Voice
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §10.3 (voice principles)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/voice.md`:

  Voice principles (from PRD, Alex to refine):
  1. Lead with domain knowledge, not with the brand
  2. Answer the specific question directly and completely
  3. Be clear about where free answer ends and paid engagement begins — professional, not apologetic
  4. Never pitch in response to an emergency thread — help first, always
  5. The line: free = general guidance, triage, what questions to ask; paid = advocacy, accompaniment, direct coordination

  Include tone examples for each response type:
  - Direct answer example
  - Triage guidance example
  - Soft referral example
  - Pass (flag for human) example

  Add: "Bernard loads this file for every community response draft."
- **Output**: `knowledge/padma-care/voice.md`
- **Acceptance**: Alex confirms voice feels right — authoritative but warm, clear about scope

### Task 7.2: Document Free/Paid Line
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §10.4
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/free-paid-line.md`:

  **The competitive moat**: Most healthcare providers either don't participate in community forums or pitch immediately. Consistent, knowledgeable presence with clear scope builds compounding reputation.

  **Free** (community responses):
  - General healthcare guidance for Bali context
  - Triage advice: what questions to ask, what to watch for
  - BPJS navigation basics
  - Hospital/clinic recommendations (general)
  - Insurance coverage general guidance

  **Paid — Healthcare Advocacy**:
  - In-hospital navigation and accompaniment
  - BPJS complexity handling
  - Dealing with Indonesian medical bureaucracy
  - Diagnosis explanation and second opinion coordination
  - Emergency coordination

  **Paid — Healthcare Concierge**:
  - Ongoing GP/specialist coordination
  - Health check planning
  - Preventive care scheduling
  - Medical records management
  - Peace of mind retainer

  **The transition phrase**: "That's exactly the kind of thing we help with professionally — here's how to engage us: [contact]"

  Bernard loads this for every community response draft.
- **Output**: `knowledge/padma-care/free-paid-line.md`
- **Acceptance**: Line is clear, defensible, and non-apologetic

### Task 7.3: Create Community Platform List
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §10.2 (target platforms)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/platforms.md`:

  Ranked platform list (Alex to confirm and prioritize):

  **Tier 1 — High volume, open access**:
  - Facebook: Bali Expats (size, access type, healthcare question frequency)
  - Reddit: r/bali (size, access type)
  - TripAdvisor: Bali forums

  **Tier 2 — High quality, requires presence**:
  - Facebook: Seminyak/Canggu/Ubud community groups (specific groups TBD by Alex)
  - Internations Bali

  **Tier 3 — Closed, requires team member**:
  - WhatsApp: business networks, expat communities (human summarizes → Bernard gets digest)
  - Facebook: neighborhood-specific groups

  For each: platform name, group/channel name, estimated audience, access method (open/closed/team-member-needed), healthcare question frequency estimate, notes.

  Mark which groups Alex or team is already in vs need to join.
- **Output**: `knowledge/padma-care/platforms.md`
- **Acceptance**: At least 5 platforms ranked, access method clear for each

### Task 7.4: Create Community Monitoring Template
- **Type**: AI
- **Input**: PRD §10.2 (daily community digest format)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/monitoring-template.md`:

  **Daily community digest format** (Bernard produces this):

  For each thread worth joining:
  1. Platform and group name
  2. Thread topic (one line)
  3. Urgency: EMERGENCY / ACTIVE_CONFUSION / PLANNING_QUESTION
  4. Conversion potential: ADVOCACY / CONCIERGE / GENERAL
  5. Approximate audience (thread views/replies)
  6. Pain point category
  7. Recommended response type: DIRECT_ANSWER / TRIAGE / SOFT_REFERRAL / PASS
  8. Draft response (loaded from voice.md and free-paid-line.md)

  Sorted by: urgency first, then conversion potential.

  **Important**: Human reviews and edits before posting. Nothing goes live without approval.
- **Output**: `knowledge/padma-care/monitoring-template.md`
- **Acceptance**: Template is clear enough for Bernard to fill and Alex to act on

### Task 7.5: Create Response Drafting Instructions
- **Type**: AI
- **Input**: PRD §10.3 (response types)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/response-drafting.md`:

  Instructions Bernard follows when drafting community responses:

  1. Load `voice.md` and `free-paid-line.md` before every draft
  2. Match response type to situation:
     - **Direct answer**: specific question with knowable answer → draft fully
     - **Triage guidance**: complex situation → "here's how to think about this"
     - **Soft referral**: clearly needs professional support → gentle "this is what we do" with contact
     - **Pass**: out of scope, politically sensitive, requires medical judgment → flag for human only, do NOT draft
  3. Never use medical jargon without explanation
  4. Never provide specific medical advice (diagnosis, treatment recommendations)
  5. Always include: "I work with Padma Care" disclosure when relevant
  6. For emergency threads: help first, brand second. Always.
  7. Max response length: 150 words for community posts (people don't read walls)
- **Output**: `knowledge/padma-care/response-drafting.md`
- **Acceptance**: Instructions produce responses that match Padma Care's voice

### Task 7.6: Create Pipeline Tracking
- **Type**: AI
- **Input**: PRD §10.5 (pipeline tracking)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/community-pipeline.md`:

  Tracking table:
  - Date
  - Platform/group
  - Thread topic
  - Response type used
  - Response posted (yes/no/edited)
  - Generated DMs or inquiries (yes/no, count)
  - Conversion (inquiry → client: yes/no)
  - Voice notes (what framing worked or didn't)

  Bernard updates this after each response is posted (Alex confirms).

  Monthly summary section: which platforms/response patterns converted, voice refinement notes.
- **Output**: `knowledge/padma-care/community-pipeline.md`
- **Acceptance**: Pipeline tracker is functional, produces useful conversion data over time

### Task 7.7: Create Content Flywheel Queue
- **Type**: AI
- **Input**: PRD §10.6 (content flywheel)
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/content-queue.md`:

  Every recurring community question = content brief.

  Format:
  - Pain point (verbatim from community thread)
  - Frequency signal (how often this comes up — Bernard tracks)
  - Recommended format: FAQ_ANSWER / LONG_FORM_GUIDE / SHORT_EXPLAINER
  - Draft brief (2-3 sentences describing the content piece)
  - Status: BRIEF_ONLY / DRAFTED / PUBLISHED
  - URL (once published)

  Published content feeds back into community responses — link instead of drafting from scratch.

  Seed with likely first entries based on common expat healthcare questions in Bali (Alex to validate):
  1. "How does BPJS work for foreigners?"
  2. "What should I know about healthcare before moving to Bali?"
  3. "Best hospitals in Bali for expats"
  4. "Does travel insurance cover [X] in Indonesia?"
  5. "What to do in a medical emergency in Bali"
- **Output**: `knowledge/padma-care/content-queue.md` with 5 seeded briefs
- **Acceptance**: Queue is useful, seeded topics are accurate

### Task 7.8: SEO Basics Checklist
- **Type**: AI + HUMAN_REVIEW
- **Input**: PRD §10.7, site URL: padmacare.pbmcgroup.com
- **Action**:
  Create `openclaw/workspace/knowledge/padma-care/seo-checklist.md`:

  One-time tasks (not ongoing):
  - [ ] Meta titles and descriptions on all key pages
  - [ ] Structured data markup: healthcare organization (Schema.org LocalBusiness + MedicalOrganization)
  - [ ] Page speed audit (Lighthouse) — fix obvious issues
  - [ ] Google Search Console configured and verified
  - [ ] Sitemap.xml submitted
  - [ ] Mobile responsiveness verified
  - [ ] Content answers specific questions clearly (GEO / AI citation optimization)
  - [ ] Internal linking between service pages and FAQ/content pages

  Weekly monitoring (Bernard does this):
  - Search Console: new queries → surface as content opportunities
  - Ranking changes on target terms
  - New backlinks

  Include note: "The goal is technical soundness so content can rank and be cited by AI assistants. Not chasing authority scores."
- **Output**: `knowledge/padma-care/seo-checklist.md`
- **Acceptance**: Checklist is actionable, one-time tasks are completable in a single session

### Task 7.9: Create Padma Care Directory & Deploy
- **Type**: AI (local + SSH)
- **Input**: All files from Tasks 7.1-7.8
- **Action**:
  Ensure `knowledge/padma-care/` directory structure:
  ```
  knowledge/padma-care/
    voice.md
    free-paid-line.md
    platforms.md
    monitoring-template.md
    response-drafting.md
    community-pipeline.md
    content-queue.md
    seo-checklist.md
  ```
  Deploy to server:
  ```bash
  git add -A && git commit -m "feat: phase 7 padma care community engine" && git push
  ssh ... "sudo -u bernard bash -c 'cd ~/bernard && git pull'"
  ```
  Verify QMD indexes the new files via symlinked workspace.
- **Output**: Full Padma Care knowledge base on server
- **Acceptance**: All 8 files on server, QMD can search them

---

### CHECKPOINT: Phase 7 Complete
**Review**: Read through all Padma Care files. Test: ask Bernard to draft a response to a sample community thread. Verify it loads voice.md and free-paid-line.md. Check SEO checklist against live site.

**Post-Phase 7**: Bernard v2 rebuild is complete. Begin 2-week text-only evaluation period. Track digest quality, FEEDBACK.md growth, and first community monitoring cycles. Voice readiness gate starts now.
