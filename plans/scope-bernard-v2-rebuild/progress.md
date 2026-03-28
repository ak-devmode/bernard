# Progress: Bernard v2 Rebuild

## Resume Context
<!-- Updated after every significant action. Paste the first 20 lines of this file
     into a new conversation to get oriented. -->
**Scope:** plans/scope-bernard-v2-rebuild/scope.md
**Last action:** Scope created (2026-03-28)
**Next action:** /plan-ceo-review on scope, then execute Phase 1 plan
**Open blockers:** None — all 7 plans ready for execution
**Key files changed:** None yet

---

## Decisions Log
<!-- Running list of non-obvious decisions made during execution and WHY.
     These are the highest-value lines for future sessions. -->

- (2026-03-28) CC can SSH directly into server — faster iteration, user approves commands
- (2026-03-28) Vault seeding: templates for sensitive (people), pre-populate for projects/principles/Padma Care — balances privacy with useful starting content
- (2026-03-28) QMD backend: unknown if built-in — Plan 3 must research before configuring
- (2026-03-28) CC not on server — Plan 6 blocked until CC installed (prerequisite added)
- (2026-03-28) Voice stays disabled — explicit gate: 2 weeks of useful text digests before re-enabling

---

## Progress Log

| Date | Skill/Action | Status | Notes |
|------|--------------|--------|-------|
| 2026-03-28 | /scope | Done | 7-phase scope created from bernard-master-plan-v2 PRD |

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
| bernard-v2-phase-1-PLAN.md | 1 — Foundation & Config | Draft | OC upgrade, voice disable, vault dirs, openclaw.json |
| bernard-v2-phase-2-PLAN.md | 2 — Identity & Learning Loop | Draft | SOUL v2, FEEDBACK.md, AGENTS.md, security spine |
| bernard-v2-phase-3-PLAN.md | 3 — Vault & QMD | Draft | Vault architecture, QMD config, curation loop |
| bernard-v2-phase-4-PLAN.md | 4 — Digest & Phase 2 Skills | Draft | Digest template, 5 skill files |
| bernard-v2-phase-5-PLAN.md | 5 — Ingestion Pipeline | Draft | Email/WA pipeline, PII strip, afterTurn hook |
| bernard-v2-phase-6-PLAN.md | 6 — CC Dispatch | Draft | CC install, ACP bridge, approval gate |
| bernard-v2-phase-7-PLAN.md | 7 — Padma Care Community | Draft | Voice docs, monitoring, response templates, SEO |

---

## Artifacts
<!-- Files created during execution that live outside the source repo -->

(none yet)
