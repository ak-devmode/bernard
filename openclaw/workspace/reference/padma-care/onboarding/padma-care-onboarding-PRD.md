# Padma Care — Concierge Member Onboarding PRD

**Version:** 1.2
**Date:** 23 March 2026
**Author:** Alex / Claude
**Status:** Draft
**Scope:** Concierge membership track only. Advocacy track is a separate flow triggered from an existing member's Desk record.

---

## Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 23 Mar 2026 | Alex/Claude | Initial draft — full onboarding arc from payment through Month 5 maturation |
| 1.1 | 23 Mar 2026 | Alex/Claude | Added Section 11 (PHA communication templates with tone guidance), Section 12 (pending engineering work), Section 13 (future projects backlog) |
| 1.2 | 27 Mar 2026 | Alex/Claude | Fixed cf_onboarding_stage enum to match actual Zoho values. Added Section 4.3 with full stage transition map, automated gate-based graduation (Onboarding→Active), onboarding trigger cron (30min post-auth), hourly gate polling, manual override endpoint, and doc pack auto-send. Split E-8 into E-8/8b/8c/8d. |

---

# 1. Problem Statement

1.1 Padma Care's current onboarding ends at payment confirmation. There is no structured post-payment sequence, which means member experience from T+0 to first service interaction is entirely dependent on PHA availability and institutional memory — not a repeatable system.

1.2 Retention to date has been driven by Alex's personal engagement. This does not scale beyond ~20-30 members and is currently transitioning to Gita and Kezia without a codified handoff.

1.3 The highest-value outcome of onboarding is a member's first service interaction with a complimentary upgrade — after which retention is materially higher. The onboarding sequence must create conditions for that interaction to happen organically, without feeling like a sales push.

---

# 2. Users and Goals

## 2.1 New Concierge Member
- Needs: confirmation that the service is real and premium from the first moment post-payment; a named human contact; genuinely useful information before they ever need care
- Blocked by: automated-feeling welcome emails, no immediate human touchpoint, no practical guidance for emergencies

## 2.2 Personal Health Advisor (PHA)
- Needs: member context before first contact; clear triggers for each outreach step; templates that feel personal, not scripted
- Blocked by: no structured intake data routed to them; no notification of new member details before they make the WA call

## 2.3 Padma Care Admin / Ops
- Needs: all signed documents and member data in predictable, accessible locations; no manual file management; audit trail of onboarding completion
- Blocked by: no automated document storage; Jotform-hosted passport creates a vendor dependency

## 2.4 Out of Scope
- Advocacy track onboarding (separate PRD / Desk ticket trigger)
- Insurance coordination workflows
- BPJS or local patient registration (not a concierge member use case)

---

# 3. Onboarding Sequence

## 3.1 Sequence Overview

| Phase | Timing | Type | Owner |
|-------|--------|------|-------|
| 1. Payment success + system provisioning | T+0 | Automated | pmg-integrations |
| 2. Welcome email | T+0 | Automated | pmg-integrations |
| 3. PHA WhatsApp introduction | T+2-4hr | Manual (templated) | PHA |
| 4. Document pack | T+48-72hr | Automated email + JotSign | pmg-integrations |
| 5. Health question prompt | Day 3-5 | Manual WA | PHA |
| 6. Emergency directive | Week 2 (~Day 10) | Manual WA + PDF | PHA |
| 7. Multi-modal medical history | Day 30 | Manual WA | PHA |
| 8. Check-in visit offer | Day 60-90 | Automated email + PHA WA | pmg-integrations + PHA |
| 9. Annual physical proposal | Month 4-5 | PHA WA or email | PHA |

---

## 3.2 Phase 1 — Payment Success + System Provisioning (T+0, automated)

**Trigger:** Xendit payment success webhook → pmg-integrations

**Actions fired in parallel:**

3.2.1 **Payment success page** renders per audit doc Section 4.2. Emotional peak tone. Sets expectation for PHA WA within 24 hours. No billing/legal language.

3.2.2 **Google Drive folder created:** `/Padma Care Members / [LastName, FirstName] — [MemberID] /`
- Subfolder: `Administrative` (service agreement, standing medical auth, signed docs)
- Subfolder: `Medical` (medical history, advocacy docs, records received)
- Passport photo downloaded from Jotform URL and saved to `Administrative` at creation time. Jotform URL is ephemeral — must be fetched and stored immediately on webhook receipt.
- Folder shared with Padma Care shared drive (PC team access)

3.2.3 **Zoho Desk contact created** with fields per mapping table in Section 6.1. Member ID, Drive folder URL, and passport stored/linked.

3.2.4 **Internal alert email** fires to it-alerts group (existing mechanism). Body must include:
- Member full name, email, WhatsApp
- Location (Bali area)
- Subscription start date (flag if future date)
- Contents of the "Anything else you'd like us to know?" field — verbatim, at the top
- Direct link to the new Drive folder

**Relocating member variant:** If `subscription_start_date` is > 7 days in the future, flag the internal alert and suppress all subsequent PHA-facing phases until T-7 from start date. Welcome email uses future-arrival variant (see 3.3).

---

## 3.3 Phase 2 — Welcome Email (T+0, automated)

**Trigger:** Same payment success webhook, fires immediately.

**Key design decisions:**

3.3.1 Email fires before PHA has made contact. Do NOT presume PHA contact has happened. Use: *"Your Personal Health Advisor will be reaching out via WhatsApp shortly to introduce themselves."*

3.3.2 Do NOT name the PHA in the automated email. PHA name only appears in the manual WA message they send personally. This decouples automation from assignment and survives staff transitions without touching templates.

3.3.3 This email is the single reference document for the membership — what's included, key contacts, team number, what to do when you need care. Not a sales email. Not a legal email.

3.3.4 **Relocating member variant:** Acknowledge the future start date explicitly. *"Your membership activates on [date] — we'll be in touch as you get closer to arrival."* This variant should be triggered when `subscription_start_date` > 7 days out.

3.3.5 Billing/legal/cancellation content does not belong here. Route to Terms of Service link.

**Template:** Update of existing welcome email PDF (doc shared in context). Requires:
- [ ] Remove "By now, Kezia has already reached out" — replace with forward-looking PHA framing
- [ ] Remove PHA name injection — use "Your Personal Health Advisor" throughout
- [ ] Add future-start-date variant block
- [ ] Remove or relocate billing/cancellation language
- [ ] Final link targets: team WhatsApp +62 822 6632 3030, padmacare@pbmcgroup.com
- [ ] Brand colors: #505CA0 primary, #E6854B CTA

---

## 3.4 Phase 3 — PHA WhatsApp Introduction (T+2-4hr, manual)

**Trigger:** PHA receives internal alert email, reads member notes before sending.

**Template (draft):**
> "Hi [FirstName]! I'm [PHA name], your Personal Health Advisor at Padma Care. I'm your dedicated point of contact for anything health-related while you're in Bali — same person every time.
>
> Quick question to help me get things right for you: what's the best time of day to reach you, and how do you like to be addressed?"

**If "Anything else" field has content:** PHA opens with a specific reference before the template message.
> "I saw you mentioned [X] — happy to talk through that whenever you're ready."

This is the highest-leverage personalization moment in the entire sequence. The alert email surfaces it deliberately so the PHA never cold-calls.

**PHA assignment:** Manual assignment in Desk custom field `cf_pha_assigned`. For the current period (Kezia / Nur operating as Kezia): assignment is always Kezia. Future: balanced by daypart preference once we have shift data.

---

## 3.5 Phase 4 — Document Pack (T+48-72hr, automated email)

**Trigger:** Timer from payment success (or manual send by PHA after WA intro confirmed).

**Framing:** Separate email from welcome. Subject: *"Two quick things to complete your Padma Care setup"*. Copy: *"We've pre-filled your details so you're not retyping anything — this takes about 3 minutes."*

**Documents sent via JotSign:**

3.5.1 **Service Agreement** (updated version — see gaps)
- Pre-populated from Jotform payload: name, DOB, address, passport number, start date
- Member signs via JotSign
- Webhook fires to pmg-integrations on completion → saves signed PDF to Drive `/Administrative` → updates Desk contact: `cf_agreement_signed = true`, date stamped

3.5.2 **Standing Medical Authorization** (new document — see gaps)
- Membership-scoped, not incident-scoped
- Valid for duration of membership, revocable by written notice
- No incident date, no 30-day expiry
- Same JotSign → Drive → Desk flow as above

**Follow-up:** If unsigned after 5 days, PHA follows up naturally via WA. Not an automated drip — a human check-in. Docs are important but not a blocker on service delivery.

---

## 3.6 Phase 5 — Health Question Prompt (Day 3-5, PHA manual WA)

**Trigger:** PHA calendar reminder, ~3 days after WA intro

**Message:**
> "Hey [name], now that you're settled in — what's one health question you've been sitting on? Could be anything."

This is the first demonstration of the service in action. No appointment implied, no transaction. The goal is a reply — any reply — that the PHA can engage with substantively. That engagement is the first proof-of-value moment.

**Chatwoot integration note:** WhatsApp Business chat windows close 24 hours after last member message. When the window closes, a timed Chatwoot trigger fires the chat history to AI for extraction. Output: structured patient profile update (relevant medical or preference notes) → saved to Desk contact notes and/or Notion. The "anything else" field from signup seeds this profile at Day 0; subsequent WA conversations mature it over time.

---

## 3.7 Phase 6 — Emergency Directive (Week 2, ~Day 10, PHA manual WA + PDF)

**Trigger:** PHA calendar reminder, approximately Day 10

**Format:** Personal WA message from PHA + downloadable/printable PDF attachment. The document is designed to be saved to phone, printed, or put somewhere physical — because in a real emergency members should not be searching through WA chat history for critical information.

**Document contents (Gita has existing draft — use as base):**

3.7.1 Area-specific ER recommendations — nearest ER for their Bali location (Canggu/Seminyak, Ubud, Sanur, Nusa Dua, Denpasar variants). Not just the name — practical notes on which hospitals are better for specific situations.

3.7.2 How to get in and get out — practical ER navigation guidance. Triage process, what to say, what to bring, how to avoid getting stuck.

3.7.3 Bed class pricing table — brief reference showing how room class selection affects total bill. The key message: the class you choose on admission carries through the whole stay. Downgrading after the fact is difficult.

3.7.4 The advocacy trigger note: *"If you're admitted and it's already office hours, connect to us immediately. We can interrupt your current plan and place you on our hospital account — which changes your pricing tier. This is one of the most valuable things your membership gives you."*

3.7.5 Closing line: *"If you're unsure what to do, text us first — that's what we're here for. +62 822 6632 3030"*

**Personalization:** Location field from Desk (`cf_location`) determines which ER variant is used. PHA WA message references their area by name. *"Since you're in Canggu, here's what you need to know..."*

**Template library needed:** 5-6 area-based document variants. Gita's draft is the starting point.

---

## 3.8 Phase 7 — Multi-Modal Medical History (Day 30, PHA WA)

**Trigger:** PHA calendar reminder, Day 30

**Format:** PHA sends a personal WA message offering multiple response modes — voice note, text, or a short structured form. Voice note is presented as the easiest option but not the only one. Accommodates members who prefer text or structured input.

**PHA message:**
> "Hey [name], we'd love to get a quick health snapshot so we know you better before you ever need care. Just reply to these in whatever format works for you — voice note, text, or I can send a quick form:
>
> — Any medications you take regularly?
> — Any surgeries or hospital stays in the past?
> — Any ongoing conditions (diabetes, blood pressure, allergies)?
> — Anything else your doctor should know?"

**Back-end processing:** Voice notes transcribed, passed through structured extraction prompt, mapped to internal medical history categories, clinical review by Gita before going into member file. Text responses handled equivalently. Output stored in Drive `/Medical` subfolder and linked in Desk contact.

---

## 3.9 Phase 8 — Check-in Visit Offer (Day 60-90, automated email + PHA WA)

**Trigger:** Automated email at Day 60 (or 90 — to be decided based on early member feedback), followed by PHA WA reinforcement

**Objective:** First in-person or virtual interaction. Not a medical appointment — a relationship check-in framed as a benefit. If this interaction happens, the member gets a complimentary upgrade on their first real service use, which materially increases retention.

**Options offered:**

| Format | Price | Description |
|--------|-------|-------------|
| In-clinic general check-in | Free | At Padma Clinic — casual, relationship-building |
| Virtual nurse visit | 800k | WhatsApp/video — nurse-led, follows up on medical history |
| Home doctor visit | 1,600k | Doctor comes to member — highest touch |

**Framing:** *"We like to check in with members around the [60/90]-day mark — not a formal appointment, just a chance to follow up on anything from your health snapshot and talk through preventative care. We'll walk you through our annual health check-up template and see what makes sense for you."*

**If declined:** No pressure. Proceed directly to Phase 9.

---

## 3.10 Phase 9 — Annual Physical Proposal (Month 4-5, PHA WA or email)

**Trigger:** PHA calendar reminder Month 4-5, regardless of whether Phase 8 check-in happened

**Framing:** *"Even if we haven't connected yet, we've put together a personalised health check-up outline based on what you shared with us. This is yours to use whenever — there's no obligation, and it's part of your membership."*

**What it is:** A bespoke Annual Physical / Medical Check-up Template — standard base package with patient-specific additions and removals based on medical history and check-in conversation. Written in plain language with brief education on each item. A menu the member can act on whenever they're ready.

**Note:** Full design of the Annual Physical product is a separate project. This phase references it as a deliverable — the PRD for that product is out of scope here.

---

# 4. Data Architecture

## 4.1 Drive Folder Structure

```
/Padma Care Members/
  /[LastName, FirstName — MemberID]/
    /Administrative/
      - passport_[MemberID].jpg (migrated from Jotform at T+0)
      - service_agreement_signed_[date].pdf
      - standing_medical_auth_signed_[date].pdf
    /Medical/
      - medical_history_[date].pdf (Day 30 output)
      - [advocacy docs when applicable, linked from Desk ticket]
```

## 4.2 Zoho Desk Contact Fields

See Section 6.1 for full field mapping. Key additions required:

| Field | API Name | Source | Notes |
|-------|----------|--------|-------|
| PHA Assigned | `cf_pha_assigned` | Manual | Used for routing and notifications |
| Location (Bali area) | `cf_location` | Jotform q23 | Drives emergency directive variant |
| Drive Folder URL | `cf_drive_folder` | pmg-integrations at T+0 | Set once, permanent |
| Agreement Signed | `cf_agreement_signed` | JotSign webhook | Boolean + date |
| Medical Auth Signed | `cf_medical_auth_signed` | JotSign webhook | Boolean + date |
| Membership Start Date | `cf_membership_start` | Jotform q51 | |
| Passport Number | `cf_passport_number` | Jotform q46 | |
| Onboarding Stage | `cf_onboarding_stage` | pmg-integrations | Enum: Pending / Provisioned / Onboarding / Active / Paused / Cancelled. See Section 4.3 for stage transitions. Field exists on both Zoho Billing customer and Zoho Desk contact. |

## 4.3 Onboarding Stage Transitions (`cf_onboarding_stage`)

This field tracks the member's lifecycle stage on the Zoho Billing customer record. It is the single source of truth for where a member is in the onboarding arc. The field is a dropdown with the following values:

| Stage | Set When | Trigger | Owner |
|-------|----------|---------|-------|
| **Pending** | Jotform signup submitted, Zoho Billing customer created | Step 2 of signup pipeline (`billing-contact`) | pmg-integrations (automated) |
| **Provisioned** | Xendit payment auth completed, Drive folder + Desk contact created | `xendit-session` connector (`create-desk-contact`) | pmg-integrations (automated) |
| **Onboarding** | Welcome email sent (~T+30min after Xendit auth) | Onboarding cron (see 4.3.1) | pmg-integrations (automated) |
| **Active** | All onboarding gates complete (see 4.3.2) | Onboarding cron polling (see 4.3.2) | pmg-integrations (automated) |
| **Paused** | Membership paused (billing hold, travel, etc.) | Manual — ops or billing team | Manual |
| **Cancelled** | Membership cancelled | Zoho Billing cancellation webhook or manual | Manual or automated |

### 4.3.1 Provisioned → Onboarding (automated)

**Trigger:** Cron job runs ~30 minutes after Xendit payment auth completes. On trigger:

1. Send welcome email (Phase 2, Section 3.3)
2. Set `cf_onboarding_stage = Onboarding`
3. Record onboarding start timestamp on the member record

The 30-minute delay ensures system provisioning (Drive folder, Desk contact) is complete before the welcome email fires. The welcome email is the member's first post-payment touchpoint and marks the beginning of the onboarding arc.

**Manual override:** An admin endpoint (`/admin/start-onboarding/:email`) must exist to manually trigger the onboarding flow for a member. This covers cases where the automated trigger fails, a member was set up outside the pipeline (e.g., manual Zoho entry), or the flow needs to be re-run. The endpoint should perform the same sequence: send welcome email, set stage to Onboarding, and start the onboarding gates checklist.

### 4.3.2 Onboarding → Active (automated, gate-based)

A member graduates to `Active` when **all four onboarding gates** are complete:

| # | Gate | How it completes | How it's checked |
|---|------|-----------------|------------------|
| G-1 | Welcome email sent | Automated at Onboarding start (4.3.1) | Recorded on send |
| G-2 | Service Agreement signed | Member signs via JotSign → webhook fires to pmg-integrations | Poll: `cf_agreement_signed = true` on Desk contact |
| G-3 | Standing Medical Authorization signed | Member signs via JotSign → webhook fires to pmg-integrations | Poll: `cf_medical_auth_signed = true` on Desk contact |
| G-4 | PHA welcome WA sent | PHA sends welcome broadcast via Chatwoot | Poll: check Chatwoot conversation exists for member phone number |

**Automation flow:**

- After welcome email sends, the Service Agreement and Medical Authorization are sent as **separate emails** (each via JotSign/Jotform, not bundled) per the document pack timing (Phase 4, ~T+48-72hr or configurable).
- A **polling cron** (1x per hour) checks all four gates for each member in `Onboarding` status.
- When all four gates are `true`, the cron sets `cf_onboarding_stage = Active` automatically.
- Members stuck in `Onboarding` have at least one incomplete gate — the polling cron should log which gates are missing, making it easy to identify what's blocking graduation.

**Design intent:** The entire `Provisioned → Onboarding → Active` arc should be fully automated. If a member is sitting in `Onboarding` for longer than expected, the missing gate(s) are immediately visible. Phases 5-9 (health question prompt, emergency directive, medical history, check-in visit, annual physical) are ongoing relationship touches that happen *after* `Active` status — they are not onboarding gates.

### 4.3.3 Paused and Cancelled

`Paused` and `Cancelled` are lifecycle states, not onboarding states. They can be set from any prior stage and are not part of the onboarding sequence.

### 4.3.4 Operational notes

- A member should not stay in `Provisioned` for more than 1 hour under normal operation. If they do, the onboarding cron has not fired — investigate.
- A member should not stay in `Onboarding` for more than 7 days. If they do, at least one gate is incomplete — check which one and follow up.
- The hourly polling cron should emit a metric/alert for members in `Onboarding` for > 7 days.

---

# 5. Advocacy Track — Separation of Concerns

5.1 Advocacy is a separate flow. It is NOT triggered by the concierge signup. It is triggered by creating an `Advocacy :: [subtype]` ticket in Desk against an existing member contact.

5.2 When an Advocacy ticket is created:
- Member's core contact data auto-populates from Desk (no re-collection)
- Incident-scoped medical authorization (based on existing Chris authorization template — dated, 30-day validity) is generated pre-populated and sent via JotSign
- Signed authorization stored in Drive `/Medical` subfolder
- Desk ticket linked to member contact

5.3 The same Drive directory serves both tracks. Identity layer is shared. Documents are separated by subfolder.

5.4 `Advocacy :: New Advocacy Event` ticket type to be created in Desk (follows existing taxonomy: `Service :: [subtype]`, `Treatment :: [subtype]` from CC world).

---

# 6. Field Mapping Reference

## 6.1 Jotform → Zoho Desk Contact

| Jotform Field | Jotform Key | Desk Field |
|---------------|-------------|------------|
| First Name | q3_yourName.first | First Name |
| Last Name | q3_yourName.last | Last Name |
| Email | q33_emailAddress | Email |
| Phone / WhatsApp | q9_mobilePhone.full | Phone |
| Date of Birth | q6_dateOf (composite) | cf_date_of_birth |
| Place of Birth | q7_placeOf | cf_place_of_birth |
| Home Address | q10_yourHome | Street |
| City | q11_city | City |
| Country | q13_country | Country |
| Gender | q32_gender32 | cf_gender |
| Location (Bali area) | q23_location | cf_location |
| Passport Number | q46_passportNumber | cf_passport_number |
| Subscription Start | q51_start_date | cf_membership_start |
| Referral ID | q49_ref | cf_referral_id |
| Anything else | [new field post-audit] | cf_intake_notes |

## 6.2 Jotform → Zoho Billing Customer (existing — from blueprint)

Currently mapping: display_name, first_name, last_name, email, phone, mobile, billing/shipping address, cf_referral_id, cf_subscription_start_date.

Gap: `cf_place_of_birth` not currently mapped to Billing. Per PRD v2.2, this custom field needs to be created in Zoho Desk (not Billing — confirm target system).

---

# 7. Open Questions

7.1 **Day 60 vs Day 90 for check-in offer** — which timing? Earlier risks feeling rushed; later risks losing momentum. @Alex — decide based on first 5-10 member cohort feedback. Default to Day 60 for now.

7.2 **JotSign webhook endpoint** — does pmg-integrations have a JotSign inbound handler, or does this need to be built? @Hamzah

7.3 **Chatwoot 24hr trigger → AI extraction** — scope and ownership. Is this a pmg-integrations task or a separate Chatwoot automation? @Alex / @Hamzah

7.4 **Service agreement update** — old document needs: removal of stale terms, addition of advocacy service scope, current pricing, concierge-specific language. Who authors the update? @Alex / legal review?

7.5 **Standing medical authorization draft** — who writes this? Gita should review for clinical appropriateness. @Gita

7.6 **Emergency directive template variants** — Gita has an existing draft. How many area variants needed at launch? Recommend: Canggu/Seminyak, Ubud, Sanur/Denpasar, Nusa Dua/Jimbaran as minimum. @Gita

7.7 **Annual Physical product PRD** — this is referenced in Phase 9 but is a separate project. @Alex to scope separately.

---

# 8. Out of Scope

- Advocacy track onboarding (triggered from Desk, separate design)
- Insurance claim coordination
- BPJS patient registration
- Annual Physical product design (referenced but not defined here)
- Newsletter / ongoing engagement (marketing plan Section 2.2.2.10-12)
- EHR / medical record system sync (future state — Drive is the interim store)
- PHA scheduling / rotation logic (manual assignment for now)

---

# 9. Dependencies

- `padma-integrations PRD v2.2` (Approved) — signup flow and Xendit webhook handling
- Zoho Desk contact creation module — not yet implemented in pmg-integrations (gap from Make.com blueprint)
- JotSign account with webhook support — assumed available, confirm
- Google Drive shared drive for PC team — confirm structure and access permissions
- Gita: emergency directive draft, standing medical auth draft
- Service agreement updated version — prerequisite before automating document pack (Phase 4)

---

# 10. Feeds Into

**Plan:** `padma-integrations/docs/padma-care-onboarding-PLAN.md` (to be created after Approved status)

**Related docs:**
- `signup-flow-audit-v1.1.md`
- `Padma_Care_Marketing_Plan_v2.1.md`
- `padma-integrations PRD v2.2`

---

# 11. PHA Communication Templates

## 11.1 Tone Principles

These templates are starting points, not scripts. The PHA should read them once and then write naturally. The goal is to sound like a smart, warm colleague — not a customer service agent. Key markers of the right tone:

- Use first names immediately and throughout
- Short paragraphs or single sentences. No walls of text over WA.
- Specific over generic. "Since you're in Canggu" beats "depending on your location."
- Low pressure. Never imply an action is urgent unless it genuinely is.
- One ask per message. Don't bundle.

---

## 11.2 Phase 3 — PHA WhatsApp Introduction (T+2-4hr)

**Standard template:**

> Hi [FirstName]! I'm [PHA name] — your Personal Health Advisor at Padma Care. I'll be your go-to for anything health-related while you're in Bali. Same person every time.
>
> Quick one: what's the best time of day to reach you, and how do you like to be addressed?

**If "Anything else" intake field has content — open with this before the template:**

> Hi [FirstName]! I'm [PHA name] from Padma Care. I saw you mentioned [X] when you signed up — happy to talk through that whenever you're ready.
>
> I'll be your dedicated health advisor here. Quick question to get started: what time of day works best for messages, and how do you like to be addressed?

**Relocating member variant (future start date):**

> Hi [FirstName]! I'm [PHA name] from Padma Care — your Personal Health Advisor once you arrive in Bali. Looking forward to having you here.
>
> We'll get properly introduced closer to your arrival on [start date], but wanted to say hi and let you know I'm already thinking about your setup. Any questions before you land, feel free to send them my way.

---

## 11.3 Phase 5 — Health Question Prompt (Day 3-5)

> Hey [FirstName] — now that you're a bit settled in, wanted to check: is there anything health-related you've been meaning to look into? Could be something small, something you've been putting off — anything at all. Happy to point you in the right direction or just think it through with you.

**If member has been responsive / chatty in intro:**

> Hey [FirstName] — quick one. Any health questions been sitting in the back of your mind? Doesn't need to be urgent. Sometimes just good to get a second opinion or know who to call.

**If member gave minimal response to intro:**

> Hi [FirstName], just checking in. If you ever have a health question — big or small — this is the number to text. No need to wait until something goes wrong.

---

## 11.4 Phase 6 — Emergency Directive Delivery (Week 2, ~Day 10)

**WA message accompanying the PDF:**

> Hey [FirstName] — something genuinely useful for you.
>
> I've put together a quick emergency reference for your area of Bali — which ER to go to, how to navigate it, and a few things worth knowing about how hospital billing works here. It's short and practical.
>
> [PDF attached]
>
> Best thing to do: save it to your phone or print it. When you're scrambling in an emergency is not the time to search through chat.
>
> And as always — if you're ever unsure what to do, text us first. +62 822 6632 3030

---

## 11.5 Phase 7 — Medical History Prompt (Day 30)

> Hey [FirstName], we're coming up on your first month — hope it's been a good one.
>
> We'd love to get a quick health snapshot on file so we know you better before you ever need care. Nothing formal — just a few questions. Reply however is easiest for you: text is fine, voice note is fine.
>
> — Any medications you take regularly?
> — Any surgeries or hospital stays in the past few years?
> — Anything ongoing you manage — blood pressure, allergies, anything like that?
> — Anything else your doctor should probably know about you?
>
> Takes most people about 5 minutes. No rush.

---

## 11.6 Phase 8 — Check-in Visit Offer (Day 60-90, PHA WA follow-up)

*Fires after automated email. PHA sends this 1-2 days later if no response to email.*

> Hey [FirstName] — did you get the note about the check-in? No pressure at all, just wanted to flag that the in-clinic option is completely free and pretty casual — more of a coffee-and-a-chat than a medical visit. But totally fine if now isn't the right time.

**If member declines:**

> Completely understood — good to know. We'll still put together a personalised health check-up outline for you in the next couple of months — that's yours regardless. Talk soon.

---

## 11.7 Phase 9 — Annual Physical Proposal (Month 4-5)

> Hi [FirstName], hope you're well.
>
> One of the things we do for members around this mark is put together a personalised health check-up outline — a suggested annual physical based on your age, history, and what we know about you. It's not a booking or a commitment, just a clear starting point so when the time feels right, you're not starting from scratch.
>
> I'll send it across in the next day or two. Let me know if anything on it looks off or if you want to talk through any of it.

---

# 12. Pending Engineering Work

This section captures all engineering items identified during onboarding design that are not yet built or scoped. These are inputs to the pmg-integrations implementation plan.

## 12.1 pmg-integrations — New Capabilities Required

| # | Capability | Trigger | Notes |
|---|-----------|---------|-------|
| E-1 | Zoho Desk contact creation on signup | Xendit payment success webhook | Not in current Make.com blueprint. Full field mapping in Section 6.1 |
| E-2 | Google Drive folder provisioning on signup | Same webhook | Create `/[LastName, FirstName — MemberID]/Administrative` and `/Medical` subfolders. Folder URL written back to Desk `cf_drive_folder` |
| E-3 | Passport photo migration from Jotform to Drive | Same webhook | Fetch Jotform file URL immediately (URL is ephemeral), download, upload to Drive `/Administrative`. Remove Jotform file dependency |
| E-4 | Internal alert email with member context | Same webhook | Existing alert updated to include: location, start date (flag if future), "Anything else" intake note verbatim, Drive folder link |
| E-5 | Welcome email variant — relocating member | Same webhook, conditional on `subscription_start_date` > T+7 | Separate template with future-arrival acknowledgment |
| E-6 | Document pack email with JotSign links | Timer: T+48hr from payment success | Pre-populated JotSign links for service agreement + standing medical auth |
| E-7 | JotSign webhook inbound handler | JotSign completion event | On signature: download signed PDF, save to Drive `/Administrative`, update Desk contact flags (`cf_agreement_signed`, `cf_medical_auth_signed`) with date |
| E-8 | Onboarding trigger cron | 30min after Xendit auth | Cron picks up `Provisioned` members where Xendit auth completed ≥30min ago. Sends welcome email, sets stage to `Onboarding`, records start timestamp. See Section 4.3.1 |
| E-8b | Onboarding gate polling cron | Hourly | Polls all members in `Onboarding` status. Checks four gates (G-1 through G-4 per Section 4.3.2). When all complete → set `Active`. Log missing gates for stuck members. Alert if `Onboarding` > 7 days |
| E-8c | Manual onboarding trigger endpoint | Admin action | `POST /admin/start-onboarding/:email` — manually kicks off the onboarding flow (welcome email + stage set + gate tracking). For members set up outside the pipeline or to recover from failures |
| E-8d | Document pack auto-send | ~T+48-72hr from onboarding start | Send Service Agreement and Medical Authorization as **separate** JotSign emails (not bundled). Triggered by onboarding cron after configurable delay from onboarding start |
| E-9 | Day 60/90 check-in offer email | Timer from payment success | Automated email with check-in options table. Triggers PHA WA follow-up notification |
| E-10 | 5-day document reminder | Timer from doc pack send, if `cf_agreement_signed = false` | Single internal alert to PHA to follow up via WA — not a member-facing drip |

## 12.2 Zoho Desk — Configuration Required

| # | Item | Notes |
|---|------|-------|
| D-1 | Create Desk contact creation step in pmg-integrations | Blocked by E-1 |
| D-2 | Add custom fields per Section 4.2 table | `cf_pha_assigned`, `cf_location`, `cf_drive_folder`, `cf_agreement_signed`, `cf_medical_auth_signed`, `cf_membership_start`, `cf_passport_number`, `cf_onboarding_stage`, `cf_intake_notes` |
| D-3 | Create `Advocacy :: New Advocacy Event` ticket type | Follows existing CC taxonomy. Subtype list TBD in Advocacy PRD |
| D-4 | PHA assignment field `cf_pha_assigned` | Manual at first. Future: routing logic by daypart preference |

## 12.3 Chatwoot — Planned Automation (Not Yet Scoped)

| # | Item | Notes |
|---|------|-------|
| C-1 | 24hr chat window close trigger | When WA conversation window closes in Chatwoot, fire chat history to AI extraction endpoint |
| C-2 | AI extraction → patient profile update | Structured prompt maps conversation content to contact fields in Desk and/or Notion. Clinical notes, preferences, follow-up items |
| C-3 | Intake notes surface to PHA at T+2hr | `cf_intake_notes` from signup form surfaced in PHA alert before first WA contact — already in E-4 above, but Chatwoot-sourced updates feed the same field over time |

## 12.4 Jotform — Form Updates Required (per signup-flow-audit-v1.1)

These are pre-engineering prerequisites — form changes needed before the integration can map the right fields.

| # | Item |
|---|------|
| J-1 | Remove: communication preference dropdowns (info style, timing, gender, biggest concern) |
| J-2 | Remove: zip code, registered address (if different) |
| J-3 | Add: "Anything else you'd like us to know?" optional open-text field (maps to `cf_intake_notes`) |
| J-4 | Move: subscription start date to end of form, optional |
| J-5 | Update: intro copy and payment framing copy (per audit Sections 2.4.1, 2.4.3) |
| J-6 | Remove: mid-form apology note (audit Section 2.4.2) |
| J-7 | Verify: Location field (q23) is capturing Bali area correctly and routing to `cf_location` |

---

# 13. Future Projects Backlog

Items raised during onboarding design that are real projects but explicitly out of scope for this PRD. Captured here so they don't get lost.

## 13.1 Annual Physical / Medical Check-up Product

A bespoke annual physical template — standard base package with patient-specific additions and removals based on medical history. Written in plain language with brief patient education on each item. Includes a menu of add/remove options so the member can personalise it. The onboarding sequence references this as a deliverable in Phase 9 but its design is a separate project.

Key elements to scope: standard base package definition, menu of optional add-ons, pricing structure, the patient-facing document format, how it connects to Gita's clinical workflow.

## 13.2 PHA Rotation and Shift Management

Currently: Kezia (with Nur operating as Kezia during trial period), hiring Ayu. Future state: ~50 members per PHA, cross-coverage when off shift, daypart-balanced assignment (AM preference → AM shift PHA, PM preference → PM shift PHA). Requires: `cf_pha_assigned` in Desk, assignment logic in pmg-integrations, coverage protocol when assigned PHA is unavailable.

## 13.3 Multi-Modal Patient History Format

Voice note history collection met generational pushback. Full solution: PHA sends a short WA prompt offering three response modes — voice note, free text, or a structured Jotform. All three routes feed into the same AI extraction pipeline. AI transcription (voice) or structured parsing (text/form) → mapped to internal medical history categories → Gita clinical review → stored in Drive `/Medical` and linked in Desk. Requires: transcription service (Whisper or equivalent), structured extraction prompt, Gita review workflow.

## 13.4 Chatwoot → Patient Profile Automation

When a WA conversation window closes in Chatwoot (24hr after last member message), fire chat history to an AI extraction endpoint. Structured output updates Desk contact notes and/or Notion patient profile with: medical topics discussed, preferences expressed, follow-up items flagged. Over time this matures the patient profile without any manual data entry. The `cf_intake_notes` field from signup is the seed; Chatwoot conversations are the ongoing source. Requires: Chatwoot webhook on window close, AI extraction service, Desk/Notion write-back.

## 13.5 EHR / Medical Records Sync

Drive is the interim document store. Long-term: Drive syncs to a proper EHR or medical records system. Folder structure (`/Administrative`, `/Medical`) is designed with this migration in mind. No action until EHR system is selected.

## 13.6 Advocacy Track PRD

Advocacy onboarding is architecturally separated from concierge (Section 5). It needs its own PRD covering: incident-scoped medical authorization flow, JotSign + Drive storage for advocacy docs, `Advocacy :: [subtype]` ticket types and subtypes, doctor referral economics and tracking, advocacy-to-concierge conversion tracking. Gita's existing authorization form is the starting point for the document design.

## 13.7 Member Newsletter / Ongoing Engagement

Per marketing plan Section 2.2.2.10-12: monthly newsletter, seasonal health alerts, non-transactional touches. Newsletter platform selection (Kezia to research) is a prerequisite. Content cadence and production workflow to be designed separately once advocacy messaging is validated.

## 13.8 Specialist Scorecard / QA Framework

Per marketing plan v2.1: quality assurance for the 108-doctor network. Scorecard criteria, strike policy, and ongoing curation process. Referenced as a parallel initiative — not part of onboarding but feeds into the service quality the onboarding promises.
