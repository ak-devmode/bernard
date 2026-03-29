# ADR-001: Replace WATI with Self-Hosted Chatwoot for WhatsApp Operations

**Version:** 1.0
**Date:** 11 March 2026
**Status:** Accepted — in execution
**Maintained by:** Alex Knecht

---

## 1. Context

### 1.1 Triggering Incident

1.1.1 On **12 February 2026**, a PMG developer exposed a WATI On-Premise API bearer token — likely via a public GitHub repository or unprotected config. An unauthorized third party used the token to submit fraudulent templates (`status_notifa_*`) and sent approximately 1,000 scam messages through PMG's WhatsApp Business Account (WABA 110218335053791).

1.1.2 Meta restricted the WABA for 30 days. Both the Clinics CS number (+62 813-3939-4907) and the Managed Care number (+62 822-6632-3030) were blocked from sending and receiving. Three policy violations were flagged; all three were successfully reversed and the restriction was lifted on **13 February 2026**.

1.1.3 **Root cause:** PMG credential management failure, not a WATI platform failure. The token was accessible where it should not have been.

1.1.4 **WATI's response** was the decisive factor against staying. WATI provides no self-service token revocation. After multiple tickets and contact attempts across all available channels, WATI did not respond for 13 hours. The combination of poor API security design (no revocation) and inadequate incident response ended the relationship. PMG secured an $816 refund of prepaid subscription fees.

### 1.2 The API Lock-In Discovery

1.2.1 After revoking WATI's partner access, PMG attempted to register the numbers on the WhatsApp Business App to operate independently. Meta returned "not available" — the numbers remained registered as API numbers in Meta's system.

1.2.2 Revoking WATI's asset access removed their ability to use the API, but did not deregister the numbers from the Cloud API. The numbers are stuck on the API. They cannot be deleted from WhatsApp Manager because paid messages were sent within the previous 30 days (the spam messages count toward this limit). Earliest possible deletion: ~14 March 2026.

1.2.3 **Coexistence is one-directional:** Business App → Cloud API works (Coexistence mode). Cloud API → Business App does not. You must originate from the Business App. Our numbers were already on the API, so the original plan to run a WhatsApp Business App setup immediately was blocked.

1.2.4 This discovery, made on the afternoon of 13 February, invalidated the initially favoured option (self-built Padma Connect) because that design assumed a Business App phase followed by a Cloud API phase. With numbers locked to the API, a BSP or platform layer connecting directly to Cloud API was required to get operational.

---

## 2. Options Evaluated

### 2.1 WATI — Stay

2.1.1 No self-service token revocation means the same vulnerability exists on next rotation. Trust in the vendor was broken by the 13-hour incident response. Monthly cost ~$80–100 including message markup.

**Verdict:** Rejected. Trust and security posture do not meet minimum requirements.

### 2.2 Respond.io

2.2.1 Full-featured, shared inbox, reasonable UX. $79+/month, fully proprietary, significant vendor lock-in on data and integrations.

**Verdict:** Rejected. Cost similar to WATI, same lock-in risk.

### 2.3 360dialog

2.3.1 Cheapest BSP option ($5–50/month). Bare-bones — provides API relay only. No shared inbox, no agent management.

**Verdict:** Rejected. Does not solve the operational coordination problem.

### 2.4 Custom-Built Padma Connect (Original Plan)

2.4.1 Full control, zero vendor dependency, cost limited to infrastructure. Design was a custom Rails/Node application over the WhatsApp Cloud API with a shared inbox, SLA monitoring, and Zoho integrations.

2.4.2 Rejected for the immediate situation because: (a) build estimate was 3–4 weeks, (b) the numbers were stuck on the API requiring a BSP to connect now, and (c) a 1–2 month Coexistence cooldown would have been required before enabling a Business App fallback. The team could not operate without a functional inbox for that duration.

2.4.3 This remains the long-term direction — custom integrations and automations are being built as extensions on top of Chatwoot rather than as a replacement.

**Verdict:** Rejected as the immediate solution. Adopted as the long-term extension strategy.

### 2.5 Chatwoot Cloud → Self-Hosted (Selected)

2.5.1 Open source, MIT license. Self-hostable. Connects directly to WhatsApp Cloud API — no deregistration or cooldown required, given our numbers are already on the API.

2.5.2 Provides shared inbox, conversation assignment, multi-number support, canned responses, and an extensible webhook/API layer.

2.5.3 Zero message markup — Meta bills directly. Chatwoot does not touch message pricing.

**Verdict:** Selected.

---

## 3. Decision

3.1 **Migrate from WATI to Chatwoot** as the primary WhatsApp operations platform for all PMG business units (Padma Clinics, Padma Care, Crew Care).

3.2 **Adoption path:** Chatwoot Cloud trial (operational from 13 February 2026) → self-hosted on AWS EC2 (`chat.pbmcgroup.com`), targeting go-live **18 March 2026**.

3.3 **Fork strategy:** `pmg-chatwoot` is a maintained fork of `chatwoot/chatwoot` (MIT). PMG customisations — the Broadcasts module and UI modifications — are additive, isolated from core Chatwoot files where possible, and tracked via the upstream remote. Patches are merged per the strategy in `prd_padma_chatwoot_v5.md` Phase 6.

3.4 **Custom extension strategy:** Platform-level integrations (Zoho CRM sync, Kyoo relay, Jotform flows) that do not require access to Chatwoot's internal data model live in a separate `padma-integrations` repository and consume Chatwoot's public API. The Broadcasts module is the exception — it is co-located in `pmg-chatwoot` because it is tightly coupled to Chatwoot's Postgres tables and Sidekiq job processing.

3.5 **Credential management:** All API tokens and secrets (Meta, Chatwoot, AWS) are stored in AWS Secrets Manager. No tokens in code, config files, environment files committed to version control, or shared documents. This is a direct remediation of the root cause of the incident.

---

## 4. Consequences

### 4.1 Accepted

4.1.1 **Self-hosting maintenance burden.** Running Postgres, Redis, Sidekiq, and Nginx on AWS requires ongoing maintenance, monitoring, backups, and patch management. This is a deliberate trade for data ownership and cost control.

4.1.2 **Broadcast UX is basic out of the box.** Template management through the stock Chatwoot UI is limited. PMG has built a custom Broadcasts module (3-screen UI) to address this. Template creation and management continues via Meta Business Manager directly.

4.1.3 **No native Zoho integration.** Zoho Desk/CRM/Billing connections must be built via webhooks and API. This was always necessary — same work regardless of platform.

4.1.4 **Cloud data retention.** Chatwoot Cloud (starter) retains conversation history for 6 months. This is acceptable given the planned migration to self-hosted (unlimited retention) before this limit is reached.

4.1.5 **Upstream fork divergence risk.** As a fork, `pmg-chatwoot` will drift from upstream if not actively maintained. The upstream tracking strategy (Phase 6 of the PRD) addresses this: security patches merged immediately, release notifications via GitHub Watch.

### 4.2 Not Accepted (Mitigated)

4.2.1 **Conversation history loss during WATI → Chatwoot transition.** Accepted as a one-time cost. WATI message history is not being migrated. app.chatwoot.com (cloud instance) remains accessible as an archive until 10 April 2026.

4.2.2 **Template message logging reliability.** Open GitHub issue #11789 — outbound templates sent via API do not always log cleanly in Chatwoot conversations. Workaround: log as a private note in the conversation. Being tracked as a post-launch item.

---

## 5. Status

5.1 Decision made: **13 February 2026**.

5.2 Cloud instance operational: **13 February 2026** (`app.chatwoot.com`).

5.3 Self-hosted staging operational: **February 2026** (`staging-chat.pbmcgroup.com`). Receives dual-delivered Meta webhooks alongside the cloud instance.

5.4 Broadcasts module built and tested on staging: **March 2026**.

5.5 Self-hosted production go-live: **target 18 March 2026** (`chat.pbmcgroup.com`). Cloud instance decommissioned: **10 April 2026**.

---

## 6. Related Documents

6.1 `archive/whatsapp-platform-evaluation.md` — Full incident report, platform evaluation, options analysis, and decision log.

6.2 `archive/padma-connect-feature-evaluation.md` — Feature gap analysis and go/no-go criteria evaluated during the platform selection process.

6.3 `development/prds/chatwoot-platform-PRD-v5.md` — Implementation PRD covering the full migration to self-hosted, broadcast module spec, data migration, infrastructure, and post-launch phases.

6.4 `pmg-chatwoot` repository — `padma-medical-group/pmg-chatwoot` — the forked Chatwoot codebase with PMG customisations.

---

# Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 11 March 2026 | Alex | Initial version — documents the WATI → Chatwoot decision, incident context, options evaluated, and current implementation status. |
