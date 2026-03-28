# Progress: Bernard v2 Rebuild

## Resume Context
<!-- Updated after every significant action. Paste the first 20 lines of this file
     into a new conversation to get oriented. -->
**Scope:** plans/scope-bernard-v2-rebuild/scope.md
**Branch:** bernard-v2
**Last action:** Phases 1-6 complete (2026-03-28) — single session, all deployed to server
**Next action:** Execute Phase 7 plan — `plans/scope-bernard-v2-rebuild/bernard-v2-phase-7-PLAN.md`
**Open blockers:** None
**Server:** 54.251.203.204, gateway healthy, QMD indexing 24 files, CC dispatch working
**What's live:** Identity, vault (projects/people/ideas/comms), digest template, 5 skills, ingestion pipeline, PII stripping, CC dispatch via acpx, JSONL logging
**Human TODOs:** `plans/scope-bernard-v2-rebuild/TODO-alex.md` (priorities, people files, board dates, etc.)
**Someday list:** `plans/scope-bernard-v2-rebuild/TOMORROW.md`

---

## Decisions Log
<!-- Running list of non-obvious decisions made during execution and WHY.
     These are the highest-value lines for future sessions. -->

- (2026-03-28) CC can SSH directly into server — faster iteration, user approves commands
- (2026-03-28) Vault seeding: templates for sensitive (people), pre-populate for projects/principles/Padma Care — balances privacy with useful starting content
- (2026-03-28) QMD is @tobilu/qmd on npm (v2.0.1) — installed via npm on server, collection symlinked at ~/vault → knowledge/
- (2026-03-28) QMD collection path quirk: QMD maps collection name to ~/name/, so we symlink ~/vault → the actual knowledge dir
- (2026-03-28) QMD searchMode starts as "search" (BM25) — upgrade to "query" once vault has 10+ meaningful files
- (2026-03-28) OpenClaw stability note: QMD memory backend has known stability issues (GitHub #11308) — monitor after deploy
- (2026-03-28) acpx is the ACP bridge (npm 0.3.1) — Bernard shells out to `acpx claude exec "..."`, no openclaw.json config needed
- (2026-03-28) System node upgraded from v22 to v24 (NodeSource) — both ubuntu and bernard users benefit
- (2026-03-28) CC auth: Bernard uses ANTHROPIC_API_KEY from systemd env. Alex uses Pro OAuth (logged in as ubuntu).
- (2026-03-28) PR creation E2E deferred — dispatch pipeline confirmed working, test with real repo when needed
- (2026-03-28) CC not on server — Plan 6 blocked until CC installed (prerequisite added)
- (2026-03-28) Voice stays disabled — explicit gate: 2 weeks of useful text digests before re-enabling
- (2026-03-28) ENG REVIEW: openclaw.json has duplicate `tools` key causing silent config loss — fix in Phase 1 Task 1.3
- (2026-03-28) ENG REVIEW: merged email + WA ingest scripts into single `tools/ingest.py --source` — DRY, one test surface
- (2026-03-28) ENG REVIEW: QMD is separate install (Tobi Lütke), not built into OpenClaw — install commands in Phase 3 Task 3.5
- (2026-03-28) ENG REVIEW: ACP config block (`acp.enabled`, `acp.dispatch.enabled`) needed in openclaw.json — Phase 6 Task 6.2
- (2026-03-28) CEO REVIEW: rsync replaced with git+symlinks — repo cloned on server, deploy = git pull
- (2026-03-28) CEO REVIEW: Phases 1-3 can compress into 1-2 sessions — plan files stay separate
- (2026-03-28) CEO REVIEW: reactive-first philosophy — Bernard earns proactivity through trust
- (2026-03-28) CEO REVIEW: simple dedup added to ingestion pipeline (hash subject+date)
- (2026-03-28) CEO REVIEW: all expansion proposals skipped — PRD is the dream, need results first

---

## Progress Log

| Date | Skill/Action | Status | Notes |
|------|--------------|--------|-------|
| 2026-03-28 | /scope | Done | 7-phase scope created from bernard-master-plan-v2 PRD |
| 2026-03-28 | /plan-ceo-review | Done | EXPANSION mode → all skipped. Git+symlinks adopted. Reactive-first confirmed. Dedup added. Plans updated. |
| 2026-03-28 | /plan-eng-review | Done | 3 findings: (1) openclaw.json duplicate `tools` key fix → Phase 1 Task 1.3, (2) DRY: merged email+WA into single ingest.py → Phase 5 Task 5.2, (3) added ingest.py unit tests → Phase 5 Task 5.3. ACP config block added to Phase 6 Task 6.2. QMD install resolved. |
| 2026-03-28 | Phase 1 | Done | Foundation: OC upgrade, voice disabled, vault dirs, openclaw.json cleaned, git+symlinks deploy |
| 2026-03-28 | Phase 2 | Done | Identity: SOUL v2, IDENTITY.md, FEEDBACK.md, AGENTS.md, MEMORY.md, security spine |
| 2026-03-28 | Phase 3 | Done | Vault: 4 project files, templates (people/ideas), principles, priorities, comms structure, CURATION.md, QMD v2.0.1 installed + indexing 12 files, gateway restarted with QMD memory backend |
| 2026-03-28 | Phase 4 | Done | Digest: DIGEST.md (4-section daily digest), 5 skills (dropped balls, board topics, staff check-ins, pricing, house projects), tracking/ dir with templates, QMD now indexing 23 files |
| 2026-03-28 | Phase 5 | Done | Ingestion: ingest.py (email/WA/Chatwoot), pii_strip.py (regex+LLM), 26 tests passing, auto-learn skill, USER.md criteria filled. Pipeline works on server. QMD indexing 24 files. |
| 2026-03-28 | Phase 6 | Done | CC Dispatch: Claude Code 2.1.86 + acpx 0.3.1 installed. System node upgraded to v24. AGENTS.md dispatch rules with approval gate. cc-dispatch.sh logging wrapper. JSONL logging active. E2E dispatch tested. |

---

## Human Steps

| Step | Status | Notes |
|------|--------|-------|
| Review Plan 1 output before deploying to server | [ ] Pending | After Plan 1 execution |
| Populate vault people/ files with real contacts | [ ] Pending | After Plan 3 creates templates |
| Fill in USER.md current priorities | [ ] Pending | After Plan 2 updates USER.md |
| Create Padma Care team member accounts in target groups | [ ] Pending | Prerequisite for Plan 7 community monitoring |
| Verify OpenRouter spend limit is set | [ ] Pending | Manual check at openrouter.ai |
| Run Bernard for 2 weeks text-only to evaluate digest quality | [ ] Pending | Gate for voice re-enablement |

---

## Plans

| Plan File | Phase | Status | Notes |
|-----------|-------|--------|-------|
| bernard-v2-phase-1-PLAN.md | 1 — Foundation & Config | Done | OC upgrade, voice disable, vault dirs, openclaw.json |
| bernard-v2-phase-2-PLAN.md | 2 — Identity & Learning Loop | Done | SOUL v2, FEEDBACK.md, AGENTS.md, security spine |
| bernard-v2-phase-3-PLAN.md | 3 — Vault & QMD | Done | Vault populated, QMD v2.0.1 installed, 12 files indexed, curation loop |
| bernard-v2-phase-4-PLAN.md | 4 — Digest & Phase 2 Skills | Done | DIGEST.md, 5 skills, 6 tracking templates, digest-log.md |
| bernard-v2-phase-5-PLAN.md | 5 — Ingestion Pipeline | Done | ingest.py, pii_strip.py, 26 tests, auto-learn.md, USER.md criteria |
| bernard-v2-phase-6-PLAN.md | 6 — CC Dispatch | Done | CC 2.1.86, acpx 0.3.1, dispatch working, JSONL logging, approval gate in AGENTS.md |
| bernard-v2-phase-7-PLAN.md | 7 — Padma Care Community | Ready to execute | Voice docs, monitoring, response templates, SEO |

---

## Artifacts
<!-- Files created during execution that live outside the source repo -->

(none yet)
