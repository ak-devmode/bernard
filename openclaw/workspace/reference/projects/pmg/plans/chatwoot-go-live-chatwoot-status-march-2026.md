# Chatwoot Project — Status vs PRD
**For:** Alex
**Date:** 10 March 2026
**Reference:** prd_padma_chatwoot_v4-1.md

---

## Phase 1 — Production Stabilization (app.chatwoot.com)

| Item | Status | Notes |
|------|--------|-------|
| WATI migration | ✅ Done | Fully off WATI |
| All 3 inboxes operational | ✅ Done | Padma Care, Crew Care, Padma Clinics live |
| Contact sync (name/number mismatch, custom attributes not showing) | ⏳ Outstanding | PRD §2.1 item 2 |
| Assignment rules | ⚠️ Partial | "Seems to kind of be working" — not fully validated |
| Label & automated logic | ⏳ Outstanding | PRD §2.1 item 4 |
| Bug: conversation disappears on resolve | ⏳ Outstanding | PRD §2.1 item 5 — not investigated |
| Canned responses expansion | ⏳ Outstanding | PRD §2.1 item 6 |
| Agent training materials (Loom videos) | ⏳ Not started | 5 videos planned — PRD Training section |
| Performance monitoring | ⏳ Not started | PRD §2.1 item 8 |
| Pending + escalation box (notification rules by inbox) | ⏳ Not started | PRD §2.1 item 9 |
| Broadcast number fix (677 fallback → 4907 permanent) | ⏳ Outstanding | PRD §1.4 temporary note — execute when broadcasts confirmed stable |

---

## Phase 2 — Staging Validation

| Item | Status | Notes |
|------|--------|-------|
| Staging server running | ✅ Done | `https://staging-chat.pbmcgroup.com` live since Feb 17 |
| All 3 WhatsApp inboxes on staging | ✅ Done | Padma Care, Crew Care, Padma Clinics |
| Router dual-delivery (prod + staging) | ✅ Done | Real patient messages hitting staging in parallel |
| S3 file uploads validation | ⏳ Outstanding | Bucket `chatwoot-staging-attachments` configured, not tested end-to-end |
| SES email configuration | ⏳ Not started | Outbound email notifications not set up |
| Sidekiq job processing | ✅ Done | Broadcasts send via Sidekiq (tested) |

---

## Phase 3 — Migration Preparation (Production Cutover)

| Item | Status | Notes |
|------|--------|-------|
| CS team staging validation period | ⏳ Not started | Needs coordination with CS leads |
| Data migration (conversations + contacts from app.chatwoot.com) | ⏳ Not started | No procedure built yet |
| Database backup/restore procedures | ⏳ Not started | |
| Cutover checklist | ⏳ Not started | |
| Rollback plan | ⏳ Not started | |
| Migrate router service to staging box | ⏳ Not started | PRD §5.2 — currently on 10.10.3.7 |
| DNS cutover (point production domain to self-hosted) | ⏳ Not started | Requires cutover decision |

**Dependency:** Phases 1 + 2 must be complete first.

---

## Phase 4 — Broadcasts Module (Chatwoot Integration)

| Item | Status | Notes |
|------|--------|-------|
| Broadcasts sidebar menu item | ✅ Done | |
| Template selection UI (searchable, per inbox) | ✅ Done | |
| Google Sheet as audience source | ✅ Done | Named sheets + tab selection |
| Template variable auto-mapping | ✅ Done | Config-driven, no manual input needed |
| Row filter (e.g. only rows where status = "ready") | ✅ Done | |
| Preview recipients before sending | ✅ Done | Shows name + phone list |
| Background send via Sidekiq | ✅ Done | |
| Broadcast history page (agent, status, sent/failed counts) | ✅ Done | |
| Feature-flagged for safe rollback | ✅ Done | |
| Recipient management via CSV or Chatwoot contact filters | ⚠️ Not built | PRD §6.4 mentioned CSV — we use Google Sheets instead (intentional) |
| Role-based access (CS leads only) | ⏳ Outstanding | Currently admin-only via Pundit policy; no lead-specific role |

**Note:** The PRD described recipients from "CSV upload or contact filters." We replaced this with Google Sheets as the audience source, which is more aligned with the actual CS team workflow. This is intentional.

---

## UI Modifications (PRD §4.3.2)

| Item | Status | Notes |
|------|--------|-------|
| Broadcasts added to sidebar | ✅ Done | |
| Hide "All Conversations" | ⏳ Not done | |
| Hide "Mentions" | ⏳ Not done | |
| Hide "Campaigns" | ⏳ Not done | |
| Hide "Help Center" | ⏳ Not done | |
| Hide "Captain" | ⏳ Not done | |
| Rename "Conversations" section to "Channels" | ⏳ Not done | |
| Unattended moved to bottom | ⏳ Not done | |

These are cosmetic but reduce cognitive load for CS team. Low effort, can be done before cutover.

---

## Contact Sync (PRD §4 Dual Sync)

| Item | Status | Notes |
|------|--------|-------|
| Zoho CRM → Chatwoot contacts sync | ⏳ Not started | Real-time on create, daily batch for updates |
| Contact naming convention (per business unit) | ⏳ Not started | `FirstName LastName - PC`, `- MV Aurora`, etc. |
| Zoho CRM → Google Contacts (for future Business App) | ⏳ Not started | Phase 4+ |

---

## Phase 5 — Advanced Features

| Item | Status |
|------|--------|
| SLA monitoring (30min warning → 60min escalation email) | ⏳ Not started |
| Advanced analytics / response time dashboard | ⏳ Not started |
| Zoho CRM / Desk / Billing integration | ⏳ Not started |
| Kyoo reservation confirmation relay | ⏳ Blocked (Meta billing issue) |
| Jotform signup flow | ⏳ Not started |
| AI / bot capabilities (Captain evaluation) | ⏳ Phase 5+ |

---

## Summary

| Phase | Status |
|-------|--------|
| Phase 1 — Production stabilization | ⚠️ Partially done — several outstanding issues |
| Phase 2 — Staging validation | ✅ Mostly done — S3 + SES remaining |
| Phase 3 — Cutover preparation | ⏳ Not started |
| Phase 4 — Broadcasts module | ✅ Done and live on staging |
| Phase 4 — UI cleanup (hide/rename items) | ⏳ Not done |
| Phase 4 — Contact sync (Zoho → Chatwoot) | ⏳ Not started |
| Phase 5 — Advanced features | ⏳ Not started |

**Biggest gap before cutover:** Phase 1 production issues (contact sync, bug on resolve, agent training) and Phase 3 migration procedures (data migration, rollback plan, cutover checklist).

**What's needed from you:** Cutover date decision + coordination with CS leads for staging validation period.
