# Padma Connect: Feature Evaluation & Test Plan

**Date:** February 13, 2026
**Purpose:** Evaluate edge cases and go/no-go criteria before committing to self-built Padma Connect vs. alternative BSP

---

## 1. WhatsApp Business App: Free vs Meta Verified (Premium)

### 1.1 Device Limits — The Core Issue

| Plan | Primary Phone | Companion Devices | Total | Cost |
|------|--------------|-------------------|-------|------|
| Free | 1 | 4 | 5 | $0 |
| Meta Verified | 1 | 9 | 10 | ~$5-15/mo (varies by region, check app) |

**PMG reality:** Each number needs 1 dedicated phone (primary) + agents + leadership companions.

- Clinics CS: 1 phone + 4 agents + Alex + Brant = 7 devices → **exceeds free tier**
- Padma Care: 1 phone + 3 agents + Alex + Brant = 6 devices → **exceeds free tier**
- Crew Care: 1 phone + 3 agents + Alex + Brant = 6 devices → **exceeds free tier**

**Verdict:** You need Meta Verified on all 3 numbers, or you drop leadership from companion access on some numbers.

### 1.2 Meta Verified Features — What You Get

| Feature | Free | Meta Verified | PMG Relevance |
|---------|------|---------------|---------------|
| Linked devices | 5 | 10 | **CRITICAL** — you need this |
| Chat assignment to agents | No | Yes | **HIGH** — see Section 3 |
| Blue verified badge | No | Yes | NICE-TO-HAVE — builds patient trust |
| Custom WhatsApp link (wa.me/yourname) | No | Yes | LOW — not essential |
| Enhanced Meta support | No | Yes | MEDIUM — useful during incidents like this one |
| Multi-agent permissions | No | Basic | MEDIUM — some role control |

### 1.3 Meta Verified Availability

Meta Verified is confirmed rolling out in Indonesia (announced alongside Brazil, India, Colombia). Check each phone's WhatsApp Business App → Settings for availability and local pricing.

### 1.4 Recommendation

Pay for Meta Verified on all 3 numbers. At ~$5-15/mo each, the total is $15-45/mo — cheaper than WATI and gives you the device count and chat assignment you need. This is a no-brainer.

---

## 2. Google Contacts Sync — Test Plan

### 2.1 What We're Validating

The entire Padma Connect architecture depends on contact names showing up correctly on companion devices. If this doesn't work reliably, it's a significant UX degradation vs. WATI (where names came from WATI's contact database).

### 2.2 Test Using Narawangsa (Live, Unaffected)

**Prerequisites:**
- [ ] Create a new Google account (e.g., test-wa-contacts@gmail.com)
- [ ] Your Narawangsa WhatsApp Business App is on a phone signed into a Google account
- [ ] Access to at least 1 companion device (WhatsApp Web or Mac app)

**Test Steps:**

| # | Action | Expected Result | Pass/Fail |
|---|--------|-----------------|-----------|
| 1 | Add 5 test contacts to the Google account (use phone numbers of people you know who have WhatsApp) | Contacts appear in Google Contacts web UI | |
| 2 | On the primary phone, ensure Google Contacts sync is enabled (Settings → Accounts → Google → toggle Contacts sync) | Phone contacts include the 5 test entries | |
| 3 | Open WhatsApp Business App on primary phone → check if those 5 contacts show names in chat list / new message search | Names display correctly | |
| 4 | Open WhatsApp Web (companion device) → search for one of the 5 contacts | Name displays correctly on companion | |
| 5 | Add 1 new contact to Google account while WhatsApp is already open | Name appears on phone and companion within ~15 minutes (may need app refresh) | |
| 6 | Change a contact name in Google Contacts | Updated name reflects on phone and companion | |
| 7 | Have someone NOT in your contacts message the Narawangsa number | Shows as phone number only (no name) — confirms unknown caller behavior | |
| 8 | Add that person to Google Contacts after they messaged | Name updates in existing conversation thread | |

### 2.3 Zoho → Google Sync Test (Second Phase)

Only do this after the basic Google Contacts test passes:

- [ ] Set up Zoho CRM native Google Contacts integration (Settings → Marketplace → Google Contacts)
- [ ] Configure one-way sync: Zoho → Google
- [ ] Add a test contact in Zoho CRM with a real phone number
- [ ] Verify it appears in Google Contacts within sync interval
- [ ] Verify it appears on WhatsApp Business App / companion device

### 2.4 Known Risks

- **Sync latency:** Google Contacts sync to Android can take 5-30 minutes. Not instant. Acceptable for PMG since contact creation happens at registration, not mid-conversation.
- **Contact limit:** Google supports 25,000 contacts. PMG is well within this.
- **Sync failures:** If Zoho-Google sync breaks, names stop updating. Mitigation: weekly spot-check of recent Zoho entries vs Google Contacts.
- **Multiple Google accounts on phone:** If the primary phone is signed into multiple Google accounts, WhatsApp reads contacts from ALL accounts. Keep the dedicated phone on a single Google account to avoid confusion.

### 2.5 Go/No-Go Criteria

- **GO:** Steps 1-8 all pass. Names display correctly on both primary and companion devices within reasonable time.
- **NO-GO:** Names don't propagate to companion devices, or sync is unreliable/delayed beyond 30 minutes. → Fall back to BSP with built-in contact management (e.g., Respond.io).

---

## 3. Critical Features: Gap Analysis & Workarounds

### 3.1 Conversation Ownership / "Who's Working On This?"

**What WATI provides:** Ticket system with open/closed status, assigned agent.

**The problem on Business App:** Everyone sees every message. No assignment (unless Meta Verified), no "resolved" flag, no way to prevent two agents replying to the same person.

**Workarounds by tier:**

| Approach | Complexity | Effectiveness |
|----------|-----------|---------------|
| **Meta Verified chat assignment** | Low (built-in) | MEDIUM — assigns chats to agents, but limited controls. No "resolved" status. |
| **WhatsApp Labels** (built into Business App) | Low | MEDIUM — create labels like "In Progress - [Agent Name]", "Resolved", "Waiting on Patient". Agents label conversations as they work them. Visible to all companion devices. |
| **Team discipline + labels** | Low | Works for small teams. Clinics CS has 4 agents — manageable. Crew Care has 3 — easy. |
| **Padma Connect audit dashboard (Phase 3)** | High | BEST — build open/closed status tracking, agent assignment, in the web dashboard. But this is weeks away. |

**Recommended interim approach:**
1. Use Meta Verified chat assignment where available
2. Create a standard label set across all numbers:
   - 🟢 New (unassigned)
   - 🟡 In Progress
   - 🔴 Waiting on Patient
   - ⬛ Resolved
   - ⭐ Escalate to Leadership
3. Team rule: Before replying, check the label. If it's "In Progress" and you didn't start it, don't touch it.
4. End-of-day: team lead reviews all conversations and closes/relabels as needed

### 3.2 Message Volume Reality Check

**You mentioned ~7,400 messages/month = ~247/day across Clinics CS.**

But "messages" ≠ "conversations." A single patient exchange might be 5-10 messages back and forth. So the actual conversation count is likely:

- ~50-80 unique conversations per day on Clinics CS
- ~15-25 on Managed Care
- TBD on Crew Care

At 50-80 conversations/day split across 4 agents, that's ~12-20 conversations per agent per day. This is very manageable on WhatsApp Business App with labels and chat assignment. You don't need a ticketing system for this volume — you need basic coordination.

**Action item:** Ask the CS team to count unique patient conversations (not messages) for one typical day. This validates whether the label-based approach is sufficient or if you truly need a ticketing system from day one.

### 3.3 Outside Office Hours (OOH) Auto-Reply

**What WATI provides:** Automated reply when message arrives outside business hours.

**WhatsApp Business App built-in:** Yes — "Away message" feature. Set business hours, configure auto-reply text. Works on free tier. No API needed.

**Limitation:** The auto-reply is the same message every time. No dynamic content, no routing logic.

**Verdict:** Built-in is sufficient for Phase 0. Padma Connect Phase 2 replaces this with API-driven OOH that can be smarter (different messages per department, escalation triggers, etc).

### 3.4 Broadcast / Mass Messaging

**What WATI provides:** Template-based broadcast to contact lists via API.

**WhatsApp Business App:** Broadcast lists limited to 256 contacts. Also broadcast lists are DISABLED in coexistence mode.

**Workaround:** This is exactly what Padma Connect Phase 1 solves — broadcast via Cloud API. No Business App workaround exists for this at scale.

**Risk:** Until Phase 1 is built, you cannot send mass messages. For the interim period, you'd need to send individually or in small batches from the Business App — painful but possible for Padma Care's ~700 messages/month.

**Verdict:** This is a real gap during the interim. Manageable for Padma Care (small volume). Harder for Clinics CS (~6,000/month) but much of that is inbound patient-initiated (free, no broadcast needed).

### 3.5 Integration: Kyoo (Reservation Confirmations)

**What WATI provides:** Kyoo calls WATI API → WATI sends WhatsApp confirmation with QR code.

**Workaround options:**
1. **Kyoo calls Cloud API directly** — requires updating Kyoo webhook URL to point to your Padma Connect endpoint (Phase 2)
2. **Kyoo sends SMS instead** — temporary fallback if Kyoo supports it
3. **Manual confirmation** — staff sends confirmation via Business App after seeing Kyoo booking

**Open question (from PRD):** Does Kyoo call WATI API directly, or via a webhook you control? This determines how hard the migration is.

**Verdict:** Needs investigation. This is a Phase 2 deliverable but you need to understand the current integration architecture NOW so you can plan the cutover.

### 3.6 Integration: Zoho Billing (Payment Links / Invoices)

**What WATI provides:** Zoho Deluge functions call WATI API to send payment links via WhatsApp.

**Workaround:** Update Deluge functions to call Cloud API directly using Meta's REST endpoint. This is straightforward — it's just changing the URL, headers, and payload format in the Deluge code.

**Interim workaround:** Staff manually sends payment links via Business App copy-paste from Zoho Billing.

**Verdict:** Easy to migrate in Phase 2. Manual workaround is fine for interim.

### 3.7 Message Search / History

**What WATI provides:** Searchable message history in WATI dashboard.

**WhatsApp Business App:** Search works within the app, but only on the primary device. Companion devices have limited search.

**Padma Connect Phase 3:** Full audit dashboard with searchable message history via Cloud API webhooks.

**Interim gap:** Leadership can't search historical conversations across agents without physical access to the primary phone. Cloud API webhooks in Phase 1 can log all messages to a database even before the dashboard UI is built.

**Verdict:** Start logging via webhook as soon as Phase 1 is live, even if the search UI comes later. The data capture is what matters.

### 3.8 Contact Management / CRM Link

**What WATI provides:** Contact list with tags, importable, linked to conversations.

**WhatsApp Business App:** Contacts come from phone's address book (Google Contacts sync). No tagging or CRM metadata visible in WhatsApp.

**Workaround:** Zoho CRM remains the source of truth. Agents who need patient context open Zoho Desk/CRM alongside WhatsApp. This is actually how most businesses operate — the messaging tool handles messaging, the CRM handles context.

**Verdict:** Not a gap — it's a different workflow. Agents will need to adapt but it's standard practice.

---

## 4. Feature Gap Summary

| Feature | WATI | Business App (Free) | Business App (Meta Verified) | Padma Connect (Future) | Interim Risk |
|---------|------|--------------------|-----------------------------|----------------------|-------------|
| Multi-device (5+) | Via API | 5 max | 10 max | N/A (uses App) | **LOW** — Meta Verified solves |
| Chat assignment | Yes | No | Yes (basic) | Phase 3 | **LOW** |
| Open/closed status | Yes | No (use labels) | No (use labels) | Phase 3 | **LOW** — labels work |
| OOH auto-reply | Yes | Yes (built-in) | Yes (built-in) | Phase 2 (smarter) | **NONE** |
| Broadcast (>256) | Yes | No | No | Phase 1 | **MEDIUM** — no mass messaging until Phase 1 |
| Kyoo integration | Yes | No | No | Phase 2 | **MEDIUM** — needs manual workaround |
| Zoho Billing integration | Yes | No | No | Phase 2 | **LOW** — manual copy-paste |
| Message search/audit | Yes | Basic (on phone) | Basic (on phone) | Phase 3 | **MEDIUM** — no leadership visibility |
| Contact names | Via WATI DB | Via Google Contacts | Via Google Contacts | Via Google Contacts | **TEST REQUIRED** — see Section 2 |
| Agent performance metrics | Basic | None | None | Phase 3 | **LOW** — not critical for current scale |

---

## 5. Decision Framework

### Go Self-Built (Padma Connect) if:

- [ ] Google Contacts sync test PASSES (Section 2)
- [ ] Team confirms label-based workflow is acceptable for interim
- [ ] Kyoo integration architecture is understood and migratable
- [ ] You accept ~3 weeks of reduced functionality during build phases

### Go Alternative BSP (e.g., Respond.io) if:

- [ ] Google Contacts sync FAILS or is unreliable
- [ ] Team cannot function without real-time shared inbox / ticketing from day one
- [ ] Kyoo or Zoho integrations are too tightly coupled to BSP architecture
- [ ] Build effort is not feasible given current team bandwidth

### Hybrid Option:

Use Meta Verified Business App + labels for daily operations (no BSP needed), and build Padma Connect for broadcasts/automations/audit only. This reduces the scope of what you need to build and eliminates the BSP dependency for agent conversations entirely.

---

## 6. Immediate Action Items

- [ ] Buy 3 Redmi 12C phones + 3 postpaid SIMs (Telkomsel)
- [ ] Run Google Contacts sync test on Narawangsa (Section 2.2)
- [ ] Ask CS team: count unique conversations (not messages) for 1 typical day
- [ ] Ask CS team: what WATI features do they actually use daily?
- [ ] Check Meta Verified availability and pricing in WhatsApp Business App (Indonesia)
- [ ] Verify Kyoo integration architecture (direct API call vs. webhook you control?)
- [ ] Audit Zoho Deluge functions that call WATI API (list them)
- [ ] Submit third Meta appeal on latest policy violation
- [ ] Monitor for additional policy violations from recipient spam reports
