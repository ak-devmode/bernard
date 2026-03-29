# Bernard Master Plan v2

**Status:** Draft  
**Version:** 2.0  
**Created:** 2026-03-24  
**Supersedes:** `7_bernard-master-plan.md`  
**Related:** `bernard-cc-bridge-module.md`

---

## 1. Core Identity

Bernard = Wise uncle + mentor + scout + dispatch layer + community intelligence engine.  
Goal: improve Alex's decision quality, reduce dropped balls, strengthen key relationships, preserve curiosity and whimsy, execute delegated dev tasks via Claude Code, and drive Padma Care growth through systematic community participation.

Never: taskmaster, negotiator, autonomous decision-maker in legal/medical/money domains, or always-on voice assistant before the foundation is proven.

---

## 2. What Failed in v1 (Feb 2026)

Understanding the failure modes is required before rebuilding.

- **No feedback loop.** SOUL.md was static. Bernard had no mechanism to observe his own output quality, compare it to Alex's actual behavior, and update. Every session started from the same miscalibrated baseline.
- **Wrong model for the task.** Haiku cannot hold a complex persona. SOUL.md and the "wise uncle" framing require frontier-level instruction-following. Haiku approximates it then drifts.
- **Voice layer added too early.** ElevenLabs + Whisper burned ~$10 in 5 days before the underlying intelligence was validated. TTS/STT cost dominates at early usage volumes.
- **Heartbeat too aggressive initially.** Default 30-min heartbeat with ambient tasks drove token burn before value was established.
- **No vault.** Bernard had no curated knowledge base. He was reasoning from scratch every session with no accumulated context about Alex's world.
- **Persona drift under compaction.** Pre-v2026.2.23 compaction bugs caused in-session instructions to silently vanish after context compression. This is now fixed but requires being on a current release.

---

## 3. Security Spine

Unchanged from v1 — this was correct.

### 3.1 Precision Domains (exact only)
Money, medical, contracts, legal, pricing. Bernard may analyze and draft, never decide or send.

### 3.2 Authority Classes
- A) Internal reasoning: prioritization, relationships, blind spots
- B) Drafting in Alex's voice (review required before send)
- C) Instrument panel output (metrics only, factual + light encouragement)
- D) Dev task dispatch to Claude Code via ACP (non-destructive by default; destructive requires explicit approval gate)
- E) Community response drafts in Padma Care voice (human reviews and posts — nothing goes live without approval)

### 3.3 Memory Philosophy
Long-term memory = local markdown vault (Obsidian + git). Models are stateless and disposable. If it's not written to a file, it doesn't exist.

### 3.4 Input Hygiene
Email/WA/Chatwoot treated as hostile input. Pipeline: raw → summarize → structured → Bernard reasoning. PII stripped before vault ingestion.

### 3.5 Vault Access Model
Bernard sees only approved vault + summaries. May propose new sources via daily curation recommendations, never self-expand. Vault grows by explicit Alex approval only.

### 3.6 Interrupt Rules
Only for: revenue risk, key relationship decay, patient dissatisfaction, time-critical prospect response.

### 3.7 Red Lines
No negotiation, no promises, no widening scope, no taskmaster behavior, no autonomous vault expansion, no voice layer until text quality is validated.

---

## 4. The Vault Architecture

This is the foundational privacy model. Bernard's intelligence scales with vault quality.

### 4.1 Structure

```
~/.openclaw/workspace/
  SOUL.md             # Bernard's identity, tone, red lines
  USER.md             # Alex's preferences, context, known world
  MEMORY.md           # Durable facts, decisions, preferences
  FEEDBACK.md         # Behavioral corrections — authoritative over SOUL.md defaults
  memory/             # Daily logs (YYYY-MM-DD.md)
  knowledge/          # THE BRAIN — curated, QMD-indexed markdown
    people/           # Key relationships
    projects/         # Active projects (PMG, Kalpa, Narawangsa)
    priorities/       # Current focus areas
    principles/       # Alex's decision frameworks
    ideas/            # Whimsy pool, sabbatical ideas, kid magic
    comms/            # Approved email/WA summaries (stripped)
  artifacts/          # Raw binaries — ignored by QMD
```

### 4.2 Ingestion Pipeline (opt-in only)

Inputs that may flow into `knowledge/comms/`:
- Email: matching approved criteria list → summarize → strip PII → structured md → vault
- WhatsApp: business-related threads → summarize → strip PII → structured md → vault
- Chatwoot: flagged conversations → summary only

Bernard never sees raw input. Always sees summaries. Criteria list lives in `USER.md` and is Alex-maintained.

### 4.3 QMD Backend

QMD (Query Markdown Documents) provides hybrid search — BM25 keyword + vector semantic + LLM reranking — over the vault. Runs entirely locally on the VM.

```yaml
memory:
  backend: qmd
  citations: auto
  qmd:
    includeDefaultMemory: true
    update:
      interval: 5m
      debounceMs: 15000
      onBoot: true
    limits:
      maxResults: 6
      maxSnippetChars: 700
      timeoutMs: 4000
```

### 4.4 Daily Vault Curation Loop

At end of day, Bernard produces a curation report (text only, no bullets):

- **Shape summary:** who communicated with Alex today, topic categories only — no content
- **Top 10 additions:** types of information that would improve Bernard's context if added to vault
- **Pruning candidates:** anything that felt personal, irrelevant, or out of scope that should be removed
- **Vault health score:** simple signal of whether current vault is growing in a useful direction

Alex reviews, approves additions, confirms pruning. Vault evolves by explicit consent.

---

## 5. The Learning Loop

This was the critical miss in v1. Bernard must have a mechanism to improve.

### 5.1 FEEDBACK.md

A durable behavioral correction file. Bernard is instructed to write to it when:
- Alex explicitly pushes back on output quality or format
- Alex edits a draft significantly before using it
- Alex ignores a recommendation repeatedly

Format: plain prose corrections. "Alex finds bullet-point digests annoying. Terse prose only." FEEDBACK.md is authoritative over SOUL.md defaults and loaded every session.

### 5.2 ContextEngine afterTurn Hook (v2026.3.7+)

A lightweight background process runs after each turn and writes behavioral signal to FEEDBACK.md when Alex expresses dissatisfaction or ignores output. Does not require Alex to explicitly ask Bernard to learn — the hook fires automatically.

### 5.3 Digest Diff Tracking

Bernard maintains a `learning/digest-log.md` that tracks which daily digest items Alex acted on vs. ignored. Over time this informs what kinds of items belong in the top 3 vs. noise.

### 5.4 Voice Readiness Gate

Before voice is re-enabled: two consecutive weeks of daily text digests that Alex finds useful enough to act on. This is the explicit validation gate. No ElevenLabs until this is passed.

---

## 6. Model Routing

### 6.1 Tier Structure

| Task | Model | Rationale |
|---|---|---|
| Daily digest, prioritization, blind spot analysis | Sonnet (via OpenRouter) | Requires persona-holding and reasoning |
| Vault curation recommendations | Sonnet | Nuanced judgment |
| Simple acknowledgments, channel routing | Haiku | Cost-appropriate |
| Heartbeat ambient tasks | Haiku | Low stakes, frequent |
| CC task dispatch, multi-step dev work | Sonnet | Complex instruction following |

### 6.2 Cost Controls

- Heartbeat interval: 3 hours (already set)
- Voice (ElevenLabs + Whisper): disabled until voice readiness gate passed
- Hard token budget cap in config — set before revival
- Digest-first behavior: Bernard surfaces, does not act autonomously, until vault is established

---

## 7. CC Dispatch (New in v2)

Bernard can dispatch dev tasks to Claude Code on the VM via ACP without modifying CC's existing skill/settings setup.

Full detail in `bernard-cc-bridge-module.md`. Summary:

- **Primary path:** `acpx openclaw exec "<task>"` — OpenClaw's native ACP bridge to CC
- **Approval gate:** pre-destructive steps (push, deploy, merge) require explicit ACK before proceeding
- **Fallback:** custom `bernard-cc-bridge.js` shell-out script if ACP proves insufficient
- **Log format:** timestamped JSONL under `<sessionId>.acp-stream.jsonl`

### 7.1 Example: PR While Driving

Alex: "Create a PR for wellmed-backbone, feat/item-catalog targeting develop, standard template."  
Bernard: dispatches via ACP → CC executes → PR URL returned → Bernard delivers via gateway.  
No approval gate needed (PR creation is reversible).

---

## 8. Gateway & Interface

### 8.1 Priority Order

| Interface | Status | Use case |
|---|---|---|
| OpenClaw WebChat (port 18789) | Evaluate first | Desktop + mobile browser, code renders correctly |
| OpenClaw Control UI | Retry — matured since Feb | Management, cron, session monitoring |
| OpenClaw iOS node app | Evaluate after WebChat | Native mobile, voice-ready surface |
| Telegram | Fallback / on-the-move | Works, Telegram-safe HTML for code blocks |

### 8.2 Telegram Code Rendering Fix

Add to SOUL.md / system prompt: "You are responding via Telegram. Always use fenced code blocks for code snippets. Never use raw markdown tables — wrap in code blocks instead."

### 8.3 Voice (Future State)

- ElevenLabs TTS + Whisper STT: disabled until voice readiness gate passed (Section 5.4)
- Target use case: commute — morning priorities discussion, evening debrief, ambient curiosity annotation
- Voice-ready digest format: conversational prose, no tables, scannable by ear
- Design for voice from day one even while text-only

---

## 9. Functional Capabilities (Phased)

### Phase 1 — Foundation (prerequisite for everything)
- [ ] Upgrade OpenClaw to latest stable (`npm install -g openclaw@latest`)
- [ ] Run `openclaw doctor --fix` — migrate browser config, repair stale settings
- [ ] Verify on v2026.2.23+ for compaction bug fixes
- [ ] Set hard token budget cap before any ambient tasks run
- [ ] Disable ElevenLabs + Whisper
- [ ] Set heartbeat to 3hr (already done — verify)
- [ ] Initialize vault structure (Section 4.1)
- [ ] Write SOUL.md v2 — wise uncle framing, Telegram code formatting rules
- [ ] Write FEEDBACK.md — seed with known v1 failure modes
- [ ] Configure QMD backend

### Phase 2 — Digest Quality
- [ ] Build daily digest template: top 3 priorities, dropped balls, 1 relationship nudge, 1 whimsy item
- [ ] Format: terse prose, voice-ready, no bullet points
- [ ] Wire vault curation report (end of day)
- [ ] Run 2 weeks text-only, evaluate digest quality
- [ ] Populate FEEDBACK.md from actual usage

### Phase 3A — Ingestion Pipeline (Context)
- [ ] Define email criteria list in USER.md
- [ ] Define WA criteria list in USER.md
- [ ] Build summarization + PII strip pipeline for email
- [ ] Build summarization + PII strip pipeline for WA (via Chatwoot)
- [ ] First vault ingestion — review output before enabling ongoing
- [ ] Implement ContextEngine afterTurn hook for FEEDBACK.md writes

### Phase 3B — Stream Watchers (Action Tracking)
- [ ] Prototype WA follow-up tracker (manual input first — Alex tells Bernard about outbound requests)
- [ ] Build automated WA follow-up detection on summary stream
- [ ] Build lead capture watcher for Bali year group → knowledge/padma-care/leads/
- [ ] Build intent-aligned todo capture from email/WA summaries
- [ ] Create stream watcher registry (knowledge/stream-watchers.md)
- [ ] Add "Waiting On", "New Leads", and "Incoming Asks" sections to daily digest template
- [ ] Wire HubSpot field draft for captured leads (copy-paste or API if available)

### Phase 4 — CC Dispatch
- [ ] Install `acpx` on VM: `npm install -g acpx@latest`
- [ ] Test: `acpx openclaw exec "summarize active session state"`
- [ ] Wire ACP dispatch into Bernard
- [ ] Test PR creation use case end-to-end
- [ ] Enable approval gate for destructive operations

### Phase 5 — Voice
- [ ] Voice readiness gate passed (2 weeks useful digests)
- [ ] Re-enable Whisper STT
- [ ] Re-enable ElevenLabs TTS
- [ ] Rewrite digest template for voice delivery
- [ ] Test commute use case — morning priorities, evening debrief

---

## 10. Padma Care Community Intelligence Engine

This is a first-class Bernard capability, not a stub. It is the highest near-term value-generating workstream and maps directly to Padma Care's growth stage. It starts as Bernard and may be spun out as a dedicated agent as it matures.

### 10.1 The Opportunity

English-speaking expats in Bali actively ask healthcare questions in community forums and groups daily. These conversations represent live pain points, prospect signals, and content briefs simultaneously. Padma Care's competitive position — domain expertise, genuine helpfulness, clear free/paid line — is precisely what these communities reward. Nobody else is doing this systematically.

The two products map differently to this channel. Healthcare Advocacy (in-hospital navigation, BPJS complexity, dealing with Indonesian medical bureaucracy) maps to the highest-anxiety conversations — someone whose family member just got admitted, someone facing a confusing diagnosis, someone being pressured to pay before treatment. Healthcare Concierge (out-of-hospital, peace of mind) maps to lower-urgency but higher-volume planning conversations — "what should I know about healthcare before moving to Bali," "recommend a good GP," "does travel insurance cover this."

### 10.2 Community Monitoring

Bernard monitors defined platforms and surfaces a daily digest of threads worth joining.

Target platforms (to be ranked and maintained in vault):
- Facebook groups: Bali Expats, Seminyak/Canggu/Ubud community groups, specific neighborhood groups
- WhatsApp groups: business networks, expat communities — requires human team member presence, agent gets summaries
- Reddit: r/bali, r/expats, r/digitalnomad, r/Bali
- TripAdvisor Bali forums
- Internations Bali

Not all groups are open. Closed groups require a team member to be present as a person, not as Padma Care. The agent monitors via that human's summarized feed. Brand participation comes after relationship equity is established.

**Daily community digest format:**
- Threads ranked by urgency (medical emergency > active confusion > planning question)
- Thread ranked by conversion potential (Advocacy > Concierge > general)
- For each thread: platform, approximate audience size, pain point category, recommended response type, draft response

### 10.3 Response Drafting

Bernard drafts community responses in Padma Care's established voice. Human reviews and edits before posting. Nothing posts without human approval — community trust is hard to build and easy to destroy.

**Voice principles (to be codified in vault under `knowledge/padma-care/voice.md`):**
- Lead with domain knowledge, not with the brand
- Answer the specific question directly and completely
- Be clear about where the free answer ends and paid engagement begins — this is not apologetic, it's professional
- Never pitch in response to an emergency thread — help first, always
- The line: free = general guidance, triage, what questions to ask; paid = advocacy, accompaniment, direct coordination

**Response types:**
- Direct answer: specific question with a knowable answer — Bernard drafts fully
- Triage guidance: complex situation, Bernard drafts a "here's how to think about this" response
- Soft referral: situation clearly needs professional support — Bernard drafts a gentle "this is what we do" with contact
- Pass: out of scope, politically sensitive, or requires medical judgment — flag for human only

### 10.4 The Free/Paid Line

This is a competitive moat and must be codified explicitly. The pattern that works:

Most healthcare providers in expat communities either don't participate or pitch immediately. Showing up consistently as the knowledgeable helpful presence who is also clear about scope builds reputation that compounds. People always test goodwill. The defense is not resentment — it's a clear, warm, non-defensive "that's exactly the kind of thing we help with professionally, here's how to engage us."

The line lives in `knowledge/padma-care/free-paid-line.md` and Bernard loads it for every community response draft.

### 10.5 Pipeline Tracking

Bernard maintains a `knowledge/padma-care/community-pipeline.md` tracking:
- Threads that generated DMs or inquiries
- Which response patterns converted vs. didn't
- Which platforms and groups produce highest quality prospects
- Voice refinement notes — what framing resonated, what fell flat

Over time this becomes an empirical voice guide, not a brand guidelines document. It reflects what actually works in the communities Alex's team is participating in.

### 10.6 Content Flywheel

Every recurring question in community monitoring is a content brief. Bernard maintains a `knowledge/padma-care/content-queue.md` with:
- Pain point (verbatim from community thread)
- Frequency signal (how often this comes up)
- Recommended content format (FAQ answer, long-form guide, short explainer)
- Draft brief
- Status (brief only / drafted / published)

Published content then feeds back into community responses — instead of drafting from scratch, Bernard links to the authoritative Padma Care page. This is how topical authority builds over time.

### 10.7 Site/SEO Basics (80/20)

The goal is not a specific authority score — it's ensuring the site is technically sound so content can rank and be cited by AI assistants. One-time tasks, not ongoing:

- [ ] Meta titles and descriptions on all key pages (Yoast or equivalent)
- [ ] Structured data markup for healthcare organization
- [ ] Page speed audit and fix obvious issues
- [ ] Google Search Console configured and monitored
- [ ] Ensure content answers specific questions clearly — GEO (AI citation) rewards direct answers more than keyword density

Bernard monitors Search Console weekly for new queries and surfaces them as content opportunities.

### 10.8 Phase Placement

This capability starts in Phase 3 (after ingestion pipeline), because it requires:
- Voice codified in vault
- Free/paid line documented
- Community platforms identified and ranked
- At least one team member active in key groups

It does not require the full vault to be mature — just the Padma Care knowledge subset.

### 10.9 Future State: Dedicated Agent

As volume grows, this may warrant spinning out from Bernard into a dedicated Padma Care community agent with its own workspace, its own vault subset, and potentially its own channel access. Bernard remains the orchestrator and Alex's personal interface. The community agent becomes a business tool that a team member (Kezia?) can interact with directly. That transition is a natural milestone, not a day-one goal.

---

## 11. Skills Backlog

Prioritized by value-to-complexity. Nothing in Phase 3+ until foundation is stable.

**High value, lower complexity (Phase 2)**
- Dropped ball tracking and nudges (relationship + followup)
- Board meeting topic accumulator (Kalpa + Padma)
- Staff check-in accountability (load concept, hold to schedule)
- Narawangsa pricing heuristic (periodic market scrape → digest)
- House project ledger (stack ranked, blockers, last update)

**High value, higher complexity (Phase 3)**
- Padma Care community intelligence engine (Section 10)
- Email/WA triage with follow-up suggestions (requires ingestion pipeline)
- Airbnb auto-suggested responses with pricing intelligence
- Kalpa weekly code change digest (branch list, commit summaries)
- Chatwoot unhappy patient flagging
- Zoho data cleanliness alerts
- Review monitoring — Google, Airbnb, Booking.com flagging + draft responses

**Aspirational (Phase 4+)**
- Sentry bug triage → CC dispatch for fix attempts
- Kalpa CI/CD weekly report
- Narawangsa competitive intelligence (scrape + trend)
- Kid magic experience planning
- Sabbatical idea research + stack ranking
- Padma Care community agent spin-out (from Section 10.9)

---

## 12. Success Criteria (90 days)

### 12.1 Foundation & Digest
- Voice readiness gate passed by day 30
- FEEDBACK.md has at least 10 behavioral corrections by day 30 (signal of active use)
- Bernard digests acted on >50% of the time by day 45

### 12.2 Knowledge Bootstrap (Sections 14–15)
- Vault contains 50+ curated knowledge files by day 30 (bootstrap is a one-time sprint)
- reference/index/ covers all significant historical docs by day 45
- reference/extracts/ contains curated insights from 10+ archive documents by day 45
- QMD search returns relevant results for all active projects and key people by day 30

### 12.3 Stream Watchers (Section 16)
- WA follow-up tracker active (manual prototype) by day 30
- Zero dropped leads between capture and HubSpot entry by day 60
- At least 3 stream watchers active by day 75
- "Waiting On" section in daily digest actively used by Alex by day 45
- Fewer forgotten follow-ups (subjective, Alex-assessed)

### 12.4 CC Dispatch & Community
- CC dispatch used for at least 5 real dev tasks by day 60
- Padma Care community monitoring active in at least 3 platforms by day 60
- At least 10 community responses drafted and posted by day 75
- At least 1 community thread converted to inquiry by day 90

### 12.5 Overall
- Calmer mental load (subjective)
- ElevenLabs re-enabled with positive ROI by day 90

---

## 13. What Bernard Is Not

- Not a replacement for Claude.ai for deep work sessions
- Not a coding agent — CC does the coding, Bernard dispatches
- Not an autonomous actor — digest-first, human-approval for consequential actions
- Not a taskmaster — surfaces and suggests, never nags
- Not always-on voice until the text foundation is proven
- Not a brand account — community participation is human-posted, Bernard drafts only

---

## 14. Knowledge Bootstrap (One-Time)

This is the initial vault population — getting Bernard from empty to useful in a single focused session. It is a deliberate, one-time exception to the reactive-first vault expansion principle (Section 3.5). Alex guides the entire process; nothing enters the vault without explicit approval.

### 14.1 Scope

Two categories of .md files exist on Alex's machine:

| Category | Location | Action |
|---|---|---|
| **Active working files** | `~/Projects/`, active CLAUDE.md files, current plans/PRDs | Copy directly into appropriate `knowledge/` bucket |
| **Everything else** | `~/Desktop/`, `~/Dropbox/`, archived projects, old startups, taxes, personal docs | Research project — classify, index, selectively extract (Section 15) |

### 14.2 Vault Topology

Not everything belongs in `knowledge/`. Bernard's vault needs two tiers:

```
~/.openclaw/workspace/
  knowledge/          # Tier 1 — WORKING MEMORY (QMD-indexed, high weight)
    people/           #   Bernard actively reasons about these every session
    projects/         #   Current, decision-relevant, frequently updated
    priorities/
    principles/
    ideas/
    comms/
    followups/        #   NEW — WA/email follow-up tracking (Section 16)
    padma-care/       #   Community intelligence, leads, voice docs
  reference/          # Tier 2 — LONG-TERM MEMORY (QMD-indexed, lower weight)
    archive/          #   Historical docs — old startups, past projects
    index/            #   Pointers to external docs (Dropbox paths, etc.)
    extracts/         #   Curated insights from archive material
```

**Tier 1 (knowledge/):** QMD searches this with full weight. Bernard treats these as active context. Files here should be current, decision-relevant, and maintained.

**Tier 2 (reference/):** QMD can search this but results are ranked lower. Bernard knows this material exists but doesn't reason about it unprompted. Contains historical context, archived decisions, and pointers to documents that live outside the vault.

### 14.3 Bootstrap Execution

A single Claude Code session with Alex present:

1. **Inventory scan.** Agent crawls `~/Projects/`, `~/Desktop/`, `~/Dropbox/` for all `.md` files. Produces a manifest: path, last modified, estimated domain, word count.
2. **Auto-classify.** Agent assigns each file to a bucket: `knowledge/{subfolder}` (copy directly), `reference/extracts/` (summarize and extract), `reference/index/` (pointer only), or `skip` (irrelevant/stale).
3. **Alex reviews.** Classification presented as a simple table. Alex approves, overrides, or skips per-file. Batch approval for obvious categories (e.g., "all active project plans → knowledge/projects/").
4. **Copy and organize.** Approved files are copied into vault with proper frontmatter (title, type, updated). Filenames normalized to lowercase-hyphenated.
5. **Extract pass.** For files classified as `reference/extracts/`, agent produces a curated .md capturing the decision-relevant insight, not the full document. Alex reviews extracts before commit.
6. **Index generation.** For files classified as `reference/index/`, agent creates pointer entries: title, original path, domain, one-line summary. Bernard can find these via QMD search and tell Alex where to look.

### 14.4 What Doesn't Enter the Vault

- Raw financial documents (taxes, invoices) — pointer only, never content
- Legal agreements — pointer only, never content (Section 3.1 precision domains)
- Personal journals, photos, non-text files — out of scope
- Duplicates of files already represented in knowledge/
- Anything Alex flags as private/out-of-scope during review

### 14.5 Success Criteria

- [ ] Inventory scan completed across all target directories
- [ ] Classification reviewed and approved by Alex
- [ ] knowledge/ contains 30+ active files across all buckets
- [ ] reference/index/ contains pointers to all significant historical docs
- [ ] reference/extracts/ contains curated insights from 10+ archive documents
- [ ] QMD search returns relevant results for: each active project, key people, current priorities
- [ ] Zero raw PII in any vault file (regex scan + manual spot check)

### 14.6 Phase Placement

Phase 2 — after foundation (Phase 1) is stable but before ingestion pipeline. This is a prerequisite for digest quality: Bernard can't surface useful priorities if the vault is empty.

---

## 15. Archive Index & Curation (Research Project)

The research project that handles Alex's historical digital life — old startups, past projects, personal documents, years of accumulated files across Dropbox and Desktop. The goal is not to ingest everything but to make it *findable* and extract what's still *decision-relevant*.

### 15.1 The Problem

Alex has years of .md files, documents, and notes spread across multiple locations representing different chapters of life: past startups, old tax planning, personal projects, business explorations. Most of this is not relevant to Bernard's daily operations, but some of it contains insights, relationship history, decision patterns, and lessons that inform current work in non-obvious ways.

Bulk-copying everything into the vault would drown signal in noise. Ignoring it all means Bernard reasons without historical context. The research project threads the needle.

### 15.2 Agent Workflow

This is a Claude Code session (or series of sessions) where the agent acts as a research assistant:

**Pass 1 — Discovery & Classification**
- Crawl target directories (Dropbox, Desktop, archived project folders)
- For each .md file: read, classify by domain (business, personal, financial, legal, technical, relationship), era (date range), and relevance to current active projects
- Output: `reference/index/master-inventory.md` — a searchable index of everything found

**Pass 2 — Relevance Scoring**
- Agent scores each file against Alex's current context (active projects, current priorities, known relationships)
- Scoring dimensions:
  - **Still decision-relevant?** (e.g., old contract terms that inform current legal posture)
  - **Contains relationship history?** (e.g., notes about people Alex still works with)
  - **Contains reusable insight?** (e.g., lessons from a failed startup that apply to Kalpa)
  - **Contains reference data?** (e.g., old pricing models, market research)
- Output: scored inventory with recommended action per file

**Pass 3 — Curated Extraction**
- For high-scoring files: agent produces a `reference/extracts/{domain}/{topic}.md` that captures the insight in Bernard-readable form
- For medium-scoring files: pointer entry in `reference/index/` with one-line summary
- For low-scoring files: skip (but they remain in the master inventory for future search)
- Alex reviews all extracts before they enter the vault

### 15.3 Index Structure

```
reference/
  index/
    master-inventory.md       # Complete file inventory with paths and classifications
    by-domain/
      business.md             # All business-related historical docs
      personal.md             # Personal planning, life docs
      financial.md            # Tax, investment, insurance (pointers only)
      legal.md                # Contracts, agreements (pointers only)
      technical.md            # Old codebases, architecture docs
      relationships.md        # Historical notes on people
  extracts/
    business/
      {startup-name}-lessons.md
      {project-name}-insights.md
    relationships/
      {name}-history.md       # For people Alex still interacts with
    technical/
      {topic}-reference.md
```

### 15.4 The Karpathy Question

Tools like local RAG / deep research (the Karpathy approach) are interesting here specifically because the archive corpus is large and heterogeneous. If the inventory scan reveals 500+ files, it may be more efficient to:
- Build a local vector index over the raw files (without copying them into the vault)
- Let Bernard query that index on-demand ("what did Alex decide about X in 2023?")
- Only extract into the vault when a query reveals something Bernard needs regularly

This is an optimization, not a requirement. Start with the agent-driven Pass 1-3 approach. If the corpus is too large for that to be practical, pivot to local RAG as the archive search layer. The vault still only contains curated extracts and pointers.

### 15.5 Privacy & Sensitivity

- Financial documents: pointer only, never content. Index entry includes document type and date range, not amounts or details.
- Legal documents: pointer only. Index entry includes parties and topic, not terms.
- Personal documents: Alex decides per-file. Default is skip unless Alex flags as relevant.
- Old business documents: extract insights and lessons, not operational details of defunct entities.
- PII from other people: strip before any vault entry. Historical relationship notes use role/context, not personal details, unless the person is a current active contact.

### 15.6 Success Criteria

- [ ] Master inventory covers all target directories
- [ ] Every file classified by domain, era, and relevance score
- [ ] Extracts produced for all high-relevance historical docs
- [ ] Index is QMD-searchable — Bernard can answer "what did Alex do about X in [year]?"
- [ ] No raw financial or legal content in the vault
- [ ] Alex has reviewed and approved all extracts

### 15.7 Phase Placement

Phase 2, parallel with or immediately after Section 14 (Knowledge Bootstrap). The bootstrap handles active files; this handles everything else. Can be done incrementally — one domain/directory per session if the corpus is large.

---

## 16. Stream Watchers

Always-on filters that sit between Alex's communication channels and the vault. Unlike the ingestion pipeline (Section 4.2), which feeds Bernard's *understanding*, stream watchers create *action items and tracking entries*. They are Bernard's operational nervous system.

### 16.1 Concept

A stream watcher is a lightweight, always-on process with four components:

| Component | Description |
|---|---|
| **Source** | A communication channel (WA thread, email inbox, lead group, Chatwoot) |
| **Trigger** | Criteria that identify actionable messages (outbound request, inbound lead, todo-shaped ask) |
| **Action** | What Bernard does when triggered (create followup entry, create lead entry, flag for digest) |
| **Gate** | Human approval mechanism (daily digest batch review, or real-time for urgent items) |

Stream watchers are *not* autonomous. They surface and propose. Alex approves and Bernard executes. The daily digest is the primary review surface for non-urgent items.

### 16.2 Stream Watcher: WA Follow-Up Tracker

**The problem:** Alex sends requests to people on WhatsApp. The request disappears until they reply or someone else asks about it. Good for low-stakes asks, terrible for business-critical follow-ups across 4 companies.

**Source:** Alex's outbound WA messages (via summary pipeline — Bernard never sees raw messages)

**Trigger criteria:**
- Message contains a request, ask, or delegation ("can you...", "please send...", "let me know when...", "following up on...")
- Message is to a business contact (not personal/family)
- Message implies an expected response or deliverable

**Action:** Create `knowledge/followups/{contact}-{topic}.md`:
```yaml
---
title: "Follow-up: [topic]"
type: followup
status: waiting
contact: "[name]"
channel: whatsapp
sent: 2026-03-28
expected_by: 2026-04-02  # inferred from context or default 5 business days
escalation: none
---

## Request
[One-line summary of what Alex asked for]

## Context
[Why this matters — which project/priority it relates to]

## Trail
- 2026-03-28: Initial request sent via WA
```

**Gate:** Follow-ups appear in the daily digest under a "Waiting On" section. Bernard includes: who, what, how long ago, and whether it's approaching the expected response window. Alex can:
- Acknowledge (keep tracking)
- Nudge (Bernard drafts a gentle follow-up message)
- Close (got what was needed, or no longer relevant)
- Escalate (flag for next in-person or call)

**Decay:** If a follow-up sits untouched for 14 days with no Alex action, Bernard flags it once as "still waiting — close or escalate?" If Alex ignores that too, it moves to a `stale` status and drops from the daily digest.

### 16.3 Stream Watcher: Lead Capture Pipeline

**The problem:** Leads arrive via a Bali year group. Alex responds immediately but HubSpot entry and drip assignment happen in batches weeks later. Follow-ups get dropped.

**Source:** Lead group messages (via summary pipeline)

**Trigger criteria:**
- Message identifies a potential Padma Care or PMG prospect
- Contains: name, contact info, health concern or inquiry type
- Comes from a known lead source channel

**Action:** Create `knowledge/padma-care/leads/{name}-{date}.md`:
```yaml
---
title: "Lead: [name]"
type: lead
status: new
source: bali-year-group
captured: 2026-03-28
hubspot: pending
drip: unassigned
---

## Lead Info
- **Name:** [name]
- **Contact:** [channel/method]
- **Inquiry:** [what they're asking about]
- **Product fit:** [Advocacy / Concierge / Unclear]

## Recommended Actions
- [ ] Enter in HubSpot (Bernard can draft fields)
- [ ] Assign drip sequence: [recommended sequence]
- [ ] Initial follow-up by: [date]

## Trail
- 2026-03-28: Lead captured from [source]
```

**Gate:** Leads appear in the daily digest under a "New Leads" section. Bernard drafts:
- HubSpot field values ready to copy-paste (or API-push if integration exists)
- Recommended drip sequence based on inquiry type
- Suggested follow-up timing

Alex reviews, approves entries, and Bernard tracks follow-up completion.

### 16.4 Stream Watcher: Intent-Aligned Todo Capture

**The problem:** Todos arrive via email and WA throughout the day. Not all asks of Alex are things Alex intends to do. Alex roughly blocks days in half by focus area and gets pulled out frequently. Bernard needs to distinguish between "someone asked Alex to do X" and "Alex actually intends to do X."

**Source:** Email and WA summaries

**Trigger criteria:**
- Direct request to Alex (not CC'd, not FYI)
- Aligns with current priorities (knowledge/priorities/current.md)
- Aligns with Alex's current day-half focus block (if known)
- Excludes: mass emails, newsletters, automated notifications, social chatter

**Action:** Create `knowledge/todos/{topic}-{date}.md` or append to existing project file:
```yaml
---
title: "Todo: [topic]"
type: todo
status: proposed  # NOT confirmed — Alex must promote
source: email|whatsapp
from: "[who asked]"
captured: 2026-03-28
priority: inferred  # based on priorities/current.md alignment
---

## The Ask
[One-line: what was requested]

## Alex's Likely Intent
[Bernard's read: does this align with current focus? Is this a "yes" or a "not now"?]

## If Accepted
- [ ] [Concrete next action]
- [ ] [Follow-up if needed]
```

**Gate:** Proposed todos appear in the daily digest under "Incoming Asks." Bernard groups them:
- **Aligned with today's focus** — likely yes
- **Important but not today** — queue for appropriate day
- **Low-priority / decline candidate** — Alex can dismiss with one word

Alex promotes, defers, or dismisses. Only promoted todos become active tracking items.

### 16.5 Stream Watcher Registry

All active stream watchers are registered in a single file: `knowledge/stream-watchers.md`

```yaml
watchers:
  - name: wa-followup-tracker
    source: whatsapp-outbound
    status: active
    output: knowledge/followups/
    gate: daily-digest

  - name: lead-capture
    source: bali-year-group
    status: active
    output: knowledge/padma-care/leads/
    gate: daily-digest

  - name: todo-capture
    source: email, whatsapp
    status: active
    output: knowledge/todos/
    gate: daily-digest
```

This registry is what Bernard checks on each heartbeat to know which watchers are running and where to route incoming summaries.

### 16.6 Building New Stream Watchers

The pattern is intentionally simple so new watchers can be added without engineering effort:

1. Define source, trigger, action, gate
2. Create an entry in `stream-watchers.md`
3. Create the output directory in knowledge/
4. Add the watcher's output section to the daily digest template
5. Bernard starts watching on next heartbeat

Future watcher candidates (from Skills Backlog, Section 11):
- **Chatwoot unhappy patient flagging** — source: Chatwoot, trigger: negative sentiment, action: flag for review
- **Airbnb inquiry responder** — source: Airbnb messages, trigger: new inquiry, action: draft response + pricing check
- **Review monitor** — source: Google/Airbnb/Booking reviews, trigger: new review, action: flag + draft response
- **Kalpa code digest** — source: GitHub, trigger: weekly cron, action: branch/commit summary

### 16.7 Relationship to Ingestion Pipeline (Section 4.2)

The ingestion pipeline and stream watchers share input sources but serve different purposes:

| | Ingestion Pipeline (4.2) | Stream Watchers (16) |
|---|---|---|
| **Purpose** | Feed Bernard's understanding | Create action items |
| **Output** | knowledge/comms/ (summaries) | knowledge/followups/, leads/, todos/ |
| **Trigger** | All approved communications | Specific actionable patterns |
| **Frequency** | Batch (end of day) | Near-real-time (per message batch) |
| **Gate** | Vault curation review | Daily digest review |

Both run on the same summarized input stream. The ingestion pipeline is broad and contextual. Stream watchers are narrow and operational. They complement, not compete.

### 16.8 Phase Placement

Phase 3B — after ingestion pipeline (Phase 3A) is operational, because stream watchers depend on the same summary input stream. However, the WA follow-up tracker could be prototyped earlier as a manual process: Alex tells Bernard about outbound requests, Bernard creates the tracking entry. This manual version validates the concept without requiring the full pipeline.

### 16.9 Success Criteria

- [ ] WA follow-up tracker catching >80% of outbound business requests
- [ ] Zero leads dropped between capture and HubSpot entry
- [ ] Todo capture correctly distinguishing aligned vs. non-aligned asks >70% of the time
- [ ] Daily digest "Waiting On" section actively used by Alex
- [ ] At least 3 stream watchers active by day 75
- [ ] Stream watcher registry maintained and accurate
