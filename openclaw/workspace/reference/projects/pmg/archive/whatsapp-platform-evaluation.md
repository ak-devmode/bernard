# Padma Connect: Platform Evaluation & Decision Log

**Version:** 2.0 — February 13, 2026
**Author:** Alex Knecht, Director — PMG
**Status:** ACTIVE — Chatwoot trial approved, implementation starting

---

## 1. Incident Summary

- **Date:** February 12, 2026
- **Root cause:** PMG developer exposed WATI On-Premise API bearer token (likely via public GitHub repo or unprotected config). Unauthorized third party used the token to submit fraudulent templates (`status_notifa_*`) and send roughly 1000 scam messages through PMG's WABA.
- **Impact:** Meta restricted WABA 110218335053791 for 30 days. Both Clinics CS (+62 813-3939-4907) and Managed Care (+62 822-6632-3030) numbers were blocked from sending/receiving.
- **Data Security:** To the best of our knowledge we were able to curtail access within 1 hour and no personal infomation, phone numbers or details were accessed/removed. No customers were directly contacted. Our account was a vector of attack for the perpatrators scam of pre-defined targets. No private medical information is stored in the workspace under attack (Wati).  
- **Resolution:** 3 policy violations flagged. All 3 successfully reversed. **Restriction lifted Feb 13, 2026.**
- **WATI response:** Revoked partner asset access from Bali and Surabaya WABAs. WATI provides no self-service token revocation and did not respond for 13 hours after multiple tickets raised and contact channels utilize. The combination of slow response and poor API security resulted in the decision to terminate the relationship. For clarity, it is unclear if the breach was caused by PMG or Claire.io (owner of WATI) but their response was significantly below expectation. PMG was able to secure a 816 dollar refund of prepaid subscription fees.

### 1.1 Credential Hygiene Finding

The breach was not a WATI platform failure — it was a PMG credential management failure. This applies regardless of which platform we move to. Required actions before any new tokens are generated:

- [ ] Identify exactly where the token was exposed (public repo, shared doc, Zoho config, plain text?)
- [ ] If GitHub: scrub history or make repo private. Token is in git history even after file deletion.
- [ ] Audit all credentials this developer had access to (AWS keys, Zoho tokens, database passwords)
- [ ] Establish secrets management policy: AWS Parameter Store or SSM for all API tokens
- [ ] No tokens in code, config files, or shared documents — ever

---

## 2. WABA & Number Architecture

### 2.1 Current State

| WABA | Numbers | Status | Notes |
|------|---------|--------|-------|
| 110218335053791 (Bali) | +62 813-3939-4907 (Clinics CS), +62 822-6632-3030 (Managed Care) | **Active** — restriction reversed | Numbers still registered as API numbers. WATI access revoked. |
| 106187252050726 (Surabaya) | None active | Restricted (was auto-restricted due to WATI partner connection) | Empty WABA |
| 105977948738245 (Surabaya standalone) | Standalone Business App | Unaffected | Confirms restrictions are per-WABA, not portfolio-level |
| 409286858932940 (Test) | Meta test number | N/A | Created by Whello for ads |

### 2.2 Critical Constraint: API-to-Business-App Migration Blocked

**Discovery:** After revoking WATI's partner access, we attempted to register our numbers on WhatsApp Business App. Meta returned "not available" — the numbers are still registered as API numbers in Meta's system.

**Why:** Revoking WATI's asset access removed their ability to USE the API, but did not deregister the numbers FROM the API. The numbers remain API-registered under our WABA.

**Deregistration blocked:** Cannot delete phone numbers from WhatsApp Manager because paid messages were sent within the last 30 days (the spam messages count). Earliest possible deletion: ~March 14, 2026.

**Coexistence is one-directional:** Business App → API works (Coexistence). API → Business App does NOT work. You must start from the Business App and extend to the Cloud API, never the reverse.

**Impact on original plan:** The original PRD assumed we could set up Business App immediately (Phase 0) and add Cloud API later (Phase 1). This is impossible with our current numbers. The numbers are stuck on the API with no active BSP managing them.

### 2.3 Revised Strategy

Instead of the original hybrid approach (Business App + custom-built Cloud API layer), we will use **Chatwoot** as our BSP/platform layer.

- **Chatwoot connects directly to Cloud API** — our numbers are already on the API, so Chatwoot can plug right in with no deregistration needed
- **Open source (MIT license)** — can be self-hosted on our own AWS infrastructure
- **Start with Chatwoot Cloud trial** — evaluate features, onboard team
- **Migrate to self-hosted** — move to our own EC2 when ready
- **Build PMG-specific features on top** — SLA monitoring, escalation, Zoho/Kyoo integrations as custom extensions

---

## 3. Platform Decision: Why Chatwoot

### 3.1 Options Evaluated

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **WATI (stay)** | Known platform, no migration | No token revocation, $130+/mo, vendor dependency, trust broken | ❌ Rejected |
| **Respond.io** | Full-featured, good UX | $79+/mo, proprietary, vendor lock-in | ❌ Rejected |
| **360dialog** | Cheapest BSP ($5-50/mo) | Bare-bones, no shared inbox | ❌ Rejected |
| **Custom-built (original Padma Connect)** | Full control, zero vendor | 3-4 week build + 1-2 month Coexistence cooldown. Too long to be operational. | ❌ Rejected for now |
| **Chatwoot Cloud → Self-hosted** | Open source, self-hostable, shared inbox, connects to existing API numbers, zero message markup | Self-hosting requires maintenance, broadcast UX is basic, no native Zoho integration | ✅ Selected |

### 3.2 Why Chatwoot Specifically

- **Solves the immediate blocker:** Numbers are stuck on API. Chatwoot connects to Cloud API directly — no deregistration, no cooldown, no waiting.
- **Open source / self-hostable:** MIT license. Start on cloud trial, move to own infrastructure. No vendor lock-in.
- **Shared inbox with assignment:** Agents get assigned conversations, mark resolved, leadership has oversight. Solves the coordination problem from day one.
- **Multi-number support:** All 3 numbers as separate inboxes in one Chatwoot instance. Agents see only their relevant inbox.
- **Zero message markup:** Direct Cloud API connection. Meta bills directly. Chatwoot doesn't touch message pricing.
- **Webhooks and API:** Extensible for custom automations (SLA monitoring, Zoho integration, Kyoo).
- **Canned responses:** Equivalent to the Quick Replies the team already uses.
- **Migration path:** When self-hosted, we own the data, the infrastructure, and the code.

### 3.3 Chatwoot Limitations & Watchouts

| Limitation | Impact | Mitigation |
|-----------|--------|-----------|
| Broadcast/campaign UX is basic | Template message management through Chatwoot is clunky. Some users report issues with template logging in conversations. | Manage templates in Meta Business Manager directly. Build lightweight broadcast tool on top of Chatwoot if needed. |
| Cloud plan data retention: 6 months (starter) | Conversation history gets deleted after retention period. | Move to self-hosted (unlimited retention) quickly. Export critical data. |
| No native Zoho integration | Zoho Desk/CRM/Billing connections must be built via webhooks/API. | Build as Phase 4 custom extension. Same work we'd have done anyway. |
| Self-hosting is real infrastructure work | PostgreSQL, Redis, Sidekiq, Nginx. Docker-deployable but needs monitoring, backups, updates. | Use existing AWS infrastructure. Docker Compose deployment. Budget engineering time for maintenance. |
| Automation rules are basic | No YAML-driven rules engine like original Padma Connect envisioned. | Build SLA monitoring and escalation as custom webhook handlers that sit alongside Chatwoot. |
| Template message logging | Open GitHub issue (#11789) — outbound templates sent via API don't always log cleanly in Chatwoot conversations. | Test thoroughly during trial. Workaround: log as private note in conversation. |

---

## 4. Meta Verified for WhatsApp Business App

**Context:** Meta Verified is relevant for the future state when/if we enable Coexistence and run Business App alongside Chatwoot/Cloud API. Also relevant if we set up any numbers on Business App directly.

### 4.1 Indonesia Pricing Tiers

| Tier | Monthly Cost (IDR) | Monthly Cost (USD est.) | Linked Devices | Protected Accounts | Key Features |
|------|-------------------|------------------------|----------------|-------------------|--------------|
| Standard | 111,000 | ~$7 | 4 | 0 | Verified badge, custom WA link |
| Plus | 225,000 | ~$14 first year | 6 | 0 | + enhanced Meta support |
| Premium | 605,000 | ~$37 first year | 8 | Up to 10 | + chat assignment, multi-agent |
| Max | 1,759,000 | ~$108 first year | 10 | Up to 50 | + expanded team features |

### 4.2 Meta Verified Chat Assignment Reality Check

Chat assignment via Meta Verified is a manual dropdown — assign a conversation to a team member with notification. It does NOT:
- Filter views (everyone still sees everything)
- Restrict access per agent
- Auto-route based on rules
- Track SLA or response time

Functionally equivalent to creating labels named after agents. Real value is device count increase, verified badge, and enhanced Meta support.

### 4.3 Recommendation (Future State)

If/when we enable Coexistence and run Business App alongside Chatwoot:
- Clinics CS: Premium tier (7 devices needed: 1 phone + 4 agents + Alex + Brant)
- Padma Care: Plus tier (6 devices)
- Crew Care: Plus tier (6 devices)
- **Total: ~IDR 1,055,000/mo (~$65/mo)**

Not needed immediately — Chatwoot handles multi-agent via its own shared inbox.

---

## 5. Contact Sync Architecture

### 5.1 Validated Flow

✅ **Confirmed working** (tested on Narawangsa Business App):
- Google Contacts → WhatsApp Business App sync works
- Web interface edits propagate to phone within minutes
- Local edits work
- Contact names display correctly in conversations

### 5.2 Source of Truth Question

**Open question:** Where does patient/member contact data live?

| System | Contains | Sync Capability to Google |
|--------|----------|--------------------------|
| Zoho CRM | Patient/member records | ✅ Native Google Contacts integration |
| Zoho Desk | Ticket contacts | ❌ No native sync — requires custom Deluge + Google People API |
| Zoho Billing | Billing contacts | ❌ No native sync — requires custom Deluge |
| Clinic software | Patient records | ❌ Depends on software — likely needs custom export |

**Recommended approach:** Zoho CRM as the canonical contact store. Sync CRM → Google Contacts via native integration. Any system that creates contacts (Desk, Billing, clinic software) should push to CRM first, then CRM syncs to Google.

**Concern flagged:** Deluge is fragile — no try/catch support, unreliable retries. For the CRM → Google sync, the native Zoho integration is reliable. For Desk/Billing → CRM sync, consider using Zoho Flow (visual workflow builder) or direct webhooks instead of Deluge functions where possible.

### 5.3 Chatwoot's Contact Management

Chatwoot has its own contact database. When a message arrives, Chatwoot creates a contact record. This means:
- Chatwoot maintains its own contact list (separate from Google Contacts)
- Contact names in Chatwoot come from the WhatsApp profile name or can be manually updated
- For Coexistence later: Business App shows Google Contacts names; Chatwoot shows its own contact names
- Chatwoot contacts can be enriched via API (push from Zoho CRM)

**Action:** During Phase 2, build a Zoho CRM → Chatwoot contact sync (via Chatwoot API) so agent context matches across both platforms.

---

## 6. Conversation Workflow Design

### 6.1 Simplified Label System (Chatwoot)

The original 5-label system was overengineered. Revised to 3 states:

| Label | Color | Applied By | Meaning |
|-------|-------|------------|---------|
| ✅ Resolved | Green | Agent (manual) | Conversation complete. No further action. |
| ⚠️ Warning | Yellow | **Automated** | New inbound message not responded to within SLA window. Auto-applied by custom webhook. |
| 🔴 Escalation | Red | **Automated** (keyword trigger) OR Agent (manual) | Needs leadership attention. Triggers email to PIC with chat context. |

### 6.2 SLA Monitoring Logic

Each number has a configurable SLA for first response time:
- Clinics CS: 15 minutes during business hours
- Padma Care: 30 minutes during business hours
- Crew Care: 60 minutes during business hours

**Auto-Warning rules:**
- New inbound message received → start timer
- If no agent response within SLA → apply "Warning" label automatically
- **"New inbound" definition:** First message from a contact that doesn't have an active open conversation, OR first message after a conversation was marked Resolved. Messages like "thank you" after resolution do NOT trigger the SLA — the conversation is already Resolved.

**Escalation triggers:**
- Certain keywords in patient messages (configurable list: "emergency", "complaint", "manager", "urgent", etc.)
- Agent manually applies Escalation label
- Warning label persists for 2x SLA without response
- **On escalation:** Send email to PIC (configurable per number) with conversation context (last 10 messages, contact info, timestamp)

### 6.3 Implementation

- **Phase 1-2 (Chatwoot Cloud):** Labels are manual. Agents mark Resolved. No automation yet.
- **Phase 3 (Self-hosted):** Build webhook handler that monitors Chatwoot conversation events via Chatwoot webhooks/API. Apply Warning labels automatically. Send Escalation emails.
- **Phase 4:** Add SLA dashboard, response time reporting, agent performance metrics.

---

## 7. Cost Comparison

### 7.1 WATI (Previous)

| Item | Monthly Cost |
|------|-------------|
| WATI subscription (Growth plan) | ~$49/mo |
| WATI per-message markup | Variable (~$30-50/mo est.) |
| **Total** | **~$80-100/mo** |

### 7.2 Chatwoot Path

| Item | Cloud Trial | Cloud Paid | Self-Hosted |
|------|------------|------------|-------------|
| Chatwoot platform | $0 (trial) | ~$19-39/agent/mo | $0 (MIT license) |
| AWS hosting (EC2 + RDS) | N/A | N/A | ~$20-40/mo |
| Meta Cloud API messages | Per Meta rates | Per Meta rates | Per Meta rates |
| Meta Verified (future, 3 numbers) | N/A | N/A | ~$65/mo |
| **Total** | **~$0 + Meta msgs** | **~$95-195/mo + Meta msgs** | **~$85-105/mo + Meta msgs** |

### 7.3 Meta Message Rates (Indonesia, 2026)

| Category | Per Message | PMG Est. Monthly Volume | Est. Monthly Cost |
|----------|------------|------------------------|-------------------|
| Marketing template | ~$0.041 | ~200 | ~$8.20 |
| Utility template | ~$0.025 | ~500 | ~$12.50 |
| Authentication template | ~$0.020 | ~50 | ~$1.00 |
| Service (inbound replies within 24hr) | FREE | ~6,000 | $0 |
| **Total estimated Meta charges** | | | **~$21.70/mo** |

---

## 8. Immediate Action Items

### Tonight / This Weekend
- [ ] Sign up for Chatwoot Cloud free trial
- [ ] Connect Clinics CS number (+62 813-3939-4907) to Chatwoot via WhatsApp Cloud API
- [ ] Connect Managed Care number (+62 822-6632-3030) to Chatwoot
- [ ] Test: send and receive messages through Chatwoot shared inbox
- [ ] Set up canned responses (migrate Quick Replies from WATI)
- [ ] Add agents to Chatwoot and test conversation assignment

### This Week
- [ ] Evaluate Chatwoot features against PMG requirements (see PRD Phase 2 checklist)
- [ ] Set up Zoho CRM → Google Contacts sync for contact name enrichment
- [ ] Test Chatwoot contact management and API for contact enrichment
- [ ] Identify and document all existing WATI integrations (Kyoo, Zoho Billing, Zoho Desk, Jotform)
- [ ] Begin planning self-hosted migration (AWS instance sizing, Docker setup)

### Before Self-Hosted Migration
- [ ] Establish secrets management policy and AWS Parameter Store setup
- [ ] Audit and revoke all developer credentials from previous incident
- [ ] Test Chatwoot self-hosted on a staging EC2 instance
- [ ] Plan data export from Chatwoot Cloud → import to self-hosted

---

## 9. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | Where does patient/member contact data live as source of truth? | Alex | Open |
| 2 | Full list of WATI-connected integrations (Kyoo, Zoho, Jotform, other)? | CS Team | Open |
| 3 | Does Kyoo call WATI API directly or via webhook we control? | Alex | Open |
| 4 | Which Zoho Deluge functions currently call WATI API? | Alex | Open |
| 5 | What WATI features does CS team actually use daily? | CS Team | Open |
| 6 | Actual daily unique conversation count (not message count)? | CS Team | Open |
| 7 | Crew Care number: use existing or register new? | Alex/Brant | Open |
| 8 | Where was the API token exposed? (GitHub repo, config file, other) | Alex/Dev | **Critical** |
| 9 | Can Chatwoot's Embedded Signup enable Coexistence on our numbers? | Alex | Test during Phase 2 |
| 10 | Chatwoot template message logging — does it work reliably? | Alex | Test during Phase 1 |

---

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Feb 13 AM | Revoke WATI partner access | Stop the bleeding. Kill compromised token pathway. |
| Feb 13 AM | Pursue self-built Padma Connect (Option C) | Full control, zero vendor, cost savings. |
| Feb 13 PM | Discovery: numbers stuck on API, cannot move to Business App | 30-day paid message restriction blocks deregistration. Coexistence requires Business App first. |
| Feb 13 PM | Pivot to Chatwoot as BSP/platform layer | Connects to existing API numbers immediately. Open source. Self-hostable. Eliminates the Coexistence dependency for getting operational. |
| Feb 13 PM | Adopt 4-phase approach: Cloud trial → Feature evaluation → Self-hosted migration → Custom extensions | Pragmatic: get operational fast, evaluate thoroughly, then own the infrastructure. |
