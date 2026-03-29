# PMG-Chatwoot Custom Code Refactor
**Project:** PMG-Chatwoot  **Branch:** feature/broadcast-refactor  **Date:** 2026-03-21

## Context
PMG maintains a fork of Chatwoot (v4.11.1 base) with ~60 custom files across broadcast, webhook router, CI/CD, and sidebar/filter mods. The goal is to refactor the PMG layer so quarterly upstream rebases are low-friction: clearly mark all custom code, use feature flags instead of comment-outs, deprecate the CLI broadcast service, and improve the structural hygiene of the broadcast feature. No changes to core Chatwoot code.

## Phases

### Phase 1: Reduce Upstream Diff — Sidebar & Filter Changes ✓
Convert commented-out code and inline modifications to feature-flag-gated behavior. This is the highest-value work because these files have the highest merge conflict risk.

**Tasks:**
- [x] 1.1 — **Sidebar: Replace comment-outs with feature flag gates.** Captain and Campaigns gated via `hasCaptain`/`hasCampaigns` computed properties using `isFeatureEnabledonAccount` (same pattern as `hasAdvancedAssignment`).
- [x] 1.2 — **Sidebar: Add PMG markers to all PMG changes.** (Revised from composable extraction — simpler markers preferred over abstraction for quarterly manual rebase.)
- [x] 1.3 — **Conversation routes: Add PMG comment markers.**
- [x] 1.4 — **ChatList/helpers status filter: Add PMG markers.**

### Phase 2: Broadcast Feature Cleanup ✓
Improve the Rails broadcast feature code quality and deprecate the CLI service.

**Tasks:**
- [x] 2.1 — **Mark CLI broadcast service as deprecated.** `DEPRECATED.md` + startup warnings.
- [x] 2.2 — **Translate Indonesian strings in BroadcastFromSheetService.** All META_ERROR_MESSAGES, error strings, comments, section headers converted to English.
- [x] 2.3 — **Extract broadcast template management to concern.** `Broadcasts::TemplateManagement` concern with `included` block for before_actions.
- [x] 2.4 — **Evaluate broadcast authorization.** custom_roles is Enterprise-only; GlobalConfig stays with TODO marker.
- [x] 2.5 — **Add PMG markers to all custom files.** All Ruby files, key JS entry points, routes.rb, account.rb.
- [x] 2.6 — **Review TemplateCreatorDialog.vue.** 927 lines but self-contained — not worth splitting.

### Phase 3: Infrastructure & Documentation ✓
- [x] 3.1 — **Update PMG-CHANGES.md.** Done in Phase 1 — conventions section, merge strategy, all entries updated.
- [x] 3.2 — **Add upstream rebase runbook.** Created in pmg-docs (`development/chatwoot-upstream-rebase-guide.md`).
- [x] 3.3 — **Evaluate router service placement.** Decision: keep in pmg-chatwoot. Router is Chatwoot infrastructure (webhook routing), not a business integration. Known debt: router imports MetaService from deprecated CLI broadcast — documented in `chatwoot-services/README.md`.

### Phase 4: Direct Chat API + Standalone Router ✓
Break the router's dependency on the deprecated CLI broadcast service. Route programmatic sends through Chatwoot's broadcast API instead of calling Meta directly.

**Tasks:**
- [x] 4.1 — **Extract DLQ to `lib/dlq.js`.** S3 dead-letter queue extracted from router.js.
- [x] 4.2 — **Extract alerting to `lib/alert.js`.** SES alerting extracted from router.js.
- [x] 4.3 — **Create `direct_chat.js`.** WATI-format endpoint, auth via SSM, payload translation, Chatwoot API client.
- [x] 4.4 — **Rewrite `router.js`.** Remove all broadcast/ imports, load routes from SSM with fallback, mount direct_chat router.
- [x] 4.5 — **Add `send_direct` to BroadcastsController.** Rails endpoint for programmatic sends.
- [x] 4.6 — **Create `Whatsapp::DirectSendService`.** Template resolution, per-recipient sends, contact sync, broadcast lifecycle.
- [x] 4.7 — **Vitest suite.** 37 tests across 5 files (dlq, alert, direct_chat unit, endpoint, webhook).
- [x] 4.8 — **RSpec suite.** DirectSendService + BroadcastsController#send_direct tests.

## Skill Sequence

| # | Skill | Apply? | When | Notes |
|---|-------|--------|------|-------|
| 1 | /plan-ceo-review | [N/A] | — | Scope is well-defined refactoring, not product strategy |
| 2 | /plan-eng-review | [x] Done | Phase 4 | Decision tree test coverage audit — identified and filled 2 major test gaps |
| 3 | /plan-design-review | [N/A] | — | No UI design changes — refactoring only |
| 4 | /review | [ ] YES | Before merge | Review full diff before merging to develop |
| 5 | /ship | [ ] YES | After review | Create PR for feature/broadcast-refactor |
| 6 | /qa | [N/A] | — | Browser QA not needed for refactoring (behavior should not change) |
| 7 | /qa-only | [x] Done | Phase 1 | `pnpm eslint` passed, RuboCop clean |
| 8 | /browse | [N/A] | — | No UI to visually verify |
| 9 | /design-consultation | [N/A] | — | No design work |
| 10 | /design-review | [N/A] | — | No design work |
| 11 | /qa-design-review | [N/A] | — | No design work |
| 12 | /setup-browser-cookies | [N/A] | — | No browser session needed |
| 13 | /document-release | [x] Done | Phase 3 | PMG-CHANGES.md, rebase guide, chatwoot-services README |
| 14 | /retro | [N/A] | — | Single-session execution |

## Key Decisions Captured
- **No Rails engine** — too heavy for quarterly rebase cadence. PMG code stays in-tree but clearly marked.
- **Feature flags over comment-outs** — Captain/Campaigns disabled via account feature flags, not source code deletion. Eliminates sidebar merge conflicts.
- **PMG comment markers over composable extraction** — clear `// PMG:` markers at every change boundary is simpler and sufficient for quarterly manual rebase.
- **CLI broadcast deprecated, not removed** — kept because router imports MetaService from it. Clearly marked with DEPRECATED.md.
- **custom_roles is Enterprise-only** — broadcast auth stays with GlobalConfig `BROADCAST_MANAGER_USER_IDS` with a TODO for Enterprise upgrade.
- **TemplateCreatorDialog.vue not split** — 927 lines but self-contained; splitting adds plumbing without meaningful benefit.
- **Router stays in pmg-chatwoot** — it's Chatwoot infrastructure (webhook routing to Chatwoot), not a business integration.
- **Router → broadcast import is known debt** — documented, not fixed in this refactor. Separate task to extract shared lib or copy needed modules.
- **Phase 4: Route through Chatwoot API** — Direct chat sends go through Rails `send_direct` endpoint rather than calling Meta API directly from Node.js. Keeps Meta API interaction in one place (Rails).
- **Phase 4: Sequential send** — DirectSendService sends to recipients sequentially (not parallel) to avoid Meta rate limits and simplify error tracking per-recipient.
- **Phase 4: SSM for route config** — Webhook routes loaded from SSM at startup with hardcoded fallback for resilience during AWS outages.
