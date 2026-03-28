# Progress: Bernard v2 Rebuild

## Resume Context
<!-- Updated after every significant action. Paste the first 20 lines of this file
     into a new conversation to get oriented. -->
**Scope:** plans/scope-bernard-v2-rebuild/scope.md
**Last action:** Eng review complete (2026-03-28) — 3 issues found and resolved, all plan files updated
**Next action:** Execute Phase 1 plan (can compress Phases 1-3 into 1-2 sessions)
**Open blockers:** None — all 7 plans updated with CEO + eng review decisions
**Key files changed:** Phase 1, 3, 5, 6 plan files updated with eng review findings

---

## Decisions Log
<!-- Running list of non-obvious decisions made during execution and WHY.
     These are the highest-value lines for future sessions. -->

- (2026-03-28) CC can SSH directly into server — faster iteration, user approves commands
- (2026-03-28) Vault seeding: templates for sensitive (people), pre-populate for projects/principles/Padma Care — balances privacy with useful starting content
- (2026-03-28) QMD backend: unknown if built-in — Plan 3 must research before configuring
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
| bernard-v2-phase-1-PLAN.md | 1 — Foundation & Config | Ready to execute | OC upgrade, voice disable, vault dirs, openclaw.json |
| bernard-v2-phase-2-PLAN.md | 2 — Identity & Learning Loop | Ready to execute | SOUL v2, FEEDBACK.md, AGENTS.md, security spine |
| bernard-v2-phase-3-PLAN.md | 3 — Vault & QMD | Ready to execute | Vault architecture, QMD config, curation loop |
| bernard-v2-phase-4-PLAN.md | 4 — Digest & Phase 2 Skills | Ready to execute | Digest template, 5 skill files |
| bernard-v2-phase-5-PLAN.md | 5 — Ingestion Pipeline | Ready to execute | Email/WA pipeline, PII strip, afterTurn hook |
| bernard-v2-phase-6-PLAN.md | 6 — CC Dispatch | Ready to execute | CC install, ACP bridge, approval gate |
| bernard-v2-phase-7-PLAN.md | 7 — Padma Care Community | Ready to execute | Voice docs, monitoring, response templates, SEO |

---

## Artifacts
<!-- Files created during execution that live outside the source repo -->

(none yet)
