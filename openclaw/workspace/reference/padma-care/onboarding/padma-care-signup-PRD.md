# Padma Care — Signup-to-Activation PRD

**Version:** 1.1
**Date:** 23 March 2026
**Author:** Alex / Claude
**Status:** Draft
**Scope:** Everything from Jotform submission through payment authorization completion (or 72hr drip exhaustion). Hands off to `padma-care-onboarding-PRD.md` at payment success.

---

## Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 23 Mar 2026 | Alex/Claude | Initial draft — full signup-to-activation arc including form spec, page copy, system provisioning, drip sequence, and Desk/Drive setup |
| 1.1 | 23 Mar 2026 | Alex/Claude | Corrected Desk/Drive provisioning timing: moved from form submission to payment success. Desk is for members, not prospects. Pre-auth drip state lives in padma-integrations state store. Removed pending_auth/drip_active/drip_exhausted from Desk enum. Added Section 5A for payment-success provisioning. Passport photo fetched at form submission (Jotform URLs are ephemeral) but stored to Drive only at payment success. |

---

# 1. Problem Statement

1.1 The current signup flow loses ~5% of committed prospects between form submission and payment authorization. These are people who already decided to join — the product-market fit signal is strong (98/100 prospects say "this is a great service") — but the mechanical friction of the flow kills their momentum. The form is too long, the confirmation page provides no context for what Xendit is or why a 0 IDR charge appears, and there is no automated recovery when someone abandons the auth step.

1.2 There is no automated recovery when someone abandons the payment authorization step. The drip sequence, confirmation page copy, and success page copy need to work together as a system — currently they either don't exist (drip) or work against the conversion goal (defensive copy on success page).

1.3 The customer-facing copy across all signup touchpoints (form, confirmation page, success page) is procedural and defensive rather than warm and confidence-building. This tone mismatch undermines the "peace of mind" brand positioning that drives retention (per Marketing Plan Section 3.2).

---

# 2. Users and Goals

## 2.1 New Prospect (committed, pre-payment)

- Needs: fast, low-friction form that respects the "sure, why not" energy of a 350k/month decision; clear explanation of what happens at the payment step before they hit it; confidence that their data is handled by a real, trustworthy organization
- Blocked by: 20+ field form with passport upload, emergency contacts, and communication preferences; no context for who Xendit is or why the auth shows 0 IDR; no recovery path when they get distracted mid-auth

## 2.2 New Member (post-payment)

- Needs: emotional reward for completing a multi-step process; clear next-step expectation (PHA will reach out); no anxiety-inducing legal/billing language at the moment of commitment
- Blocked by: payment success page that leads with cancellation policy, no-refunds, and chargeback warnings

## 2.3 Personal Health Advisor (PHA)

- Needs: notification when a new member completes the flow; member context (intake notes, location, start date) before first contact
- Blocked by: no intake notes surfaced in the current flow; no structured alert on signup completion

## 2.4 Padma Care Ops / Admin

- Needs: all member data in predictable locations from payment success; audit trail of signup completion; passport stored outside Jotform
- Blocked by: passport stored only on Jotform (ephemeral URL); no structured provisioning at payment success (Drive folder, Desk contact created manually or inconsistently)

## 2.5 Out of Scope

- Post-payment onboarding sequence (covered by `padma-care-onboarding-PRD.md`)
- Advocacy track signup (separate Desk ticket trigger)
- Zoho Billing subscription creation and Xendit session orchestration (covered by `padma-integrations PRD v2.2` — this PRD references but does not redefine that flow)
- Insurance coordination
- Jotform form analytics / abandonment tracking (no native Jotform support; third-party options documented in `signup-flow-audit-v1.1.md` Section 2.1 but not scoped here)

---

# 3. Flow Overview

```
Jotform submit
  ├── Browser: Thank You redirect → /new-subscription-success/?email=X
  └── Webhook: POST to padma-integrations/webhooks/padmacare-signup
        ├── [Existing v2.2 flow] Zoho Billing contact → Subscription → Xendit session → poll for URL
        ├── [NEW — this PRD] Passport photo fetched from Jotform URL and cached locally
        ├── [NEW — this PRD] Jotform payload cached for downstream provisioning
        └── [NEW — this PRD] Drip scheduler armed (fires if auth not completed by +1hr)

Prospect lands on /new-subscription-success/ → clicks "Authorize My Card" → Xendit auth page

  IF auth completes:
    Xendit webhook → padma-integrations
      ├── [Existing v2.2] Zoho Billing subscription activated
      └── [NEW — this PRD] Zoho Desk contact created (cf_onboarding_stage = provisioned)
                            Google Drive folder provisioned
                            Passport photo saved to Drive /Administrative/
                            Internal alert email fired to PHA/ops
                            Drip scheduler cancelled
                            Payment success page renders (warm welcome copy)
                            → Handoff to onboarding PRD Phase 2 (welcome email)

  IF auth does NOT complete:
    Drip scheduler fires from padma-integrations state store:
      +1hr  → reminder-1hr.html (using cached Jotform data)
      +12hr → reminder-12hr.html
      +24hr → new Xendit URL generated → new-url-24hr.html
      +60hr → new-url-60hr.html (final automated touch)
      +72hr → drip exhausted → internal alert to PHA for manual WhatsApp follow-up
              (no Desk record exists — alert carries Jotform data directly)
```

---

# 4. Phase 1 — Jotform (Prospect-Facing)

## 4.1 Field Spec

The form collects only what is needed to create the member record, trigger payment auth, and capture operationally critical data that is harder to collect later. All other data moves to PHA-driven onboarding.

### 4.1.1 Required Fields

| Field | Jotform Key | Purpose | Maps to |
|-------|-------------|---------|---------|
| First Name | q3_yourName.first | Identity | Desk First Name, Billing first_name |
| Last Name | q3_yourName.last | Identity | Desk Last Name, Billing last_name |
| Gender | q32_gender32 | Indonesian patient registration requirement | Desk cf_gender |
| Date of Birth | q6_dateOf | Indonesian patient registration requirement | Desk cf_date_of_birth |
| Place of Birth / Country | q7_placeOf | National law requirement | Desk cf_place_of_birth |
| Mobile Phone / WhatsApp | q9_mobilePhone.full | Primary contact channel | Desk Phone, Billing mobile |
| Email Address | q33_emailAddress | Account key, email delivery | Desk Email, Billing email |
| Home Address | q10_yourHome | Home visit logistics, billing | Desk Street, Billing address |
| City | q11_city | Location context | Desk City, Billing city |
| Country | q13_country | Billing/location | Desk Country, Billing country |
| Passport Number | q46_passportNumber | Forces better passport photo quality | Desk cf_passport_number |
| Passport Photo | q47_passportPhoto | Required for any hospital appointment booking | Drive /Administrative/ |
| ToS Checkbox | q39_termsCheckbox | Legal requirement | — |

### 4.1.2 Optional Fields (kept at signup)

| Field | Jotform Key | Purpose | Maps to |
|-------|-------------|---------|---------|
| Subscription Start Date | q51_start_date | Relocating members — future activation | Desk cf_membership_start, Billing cf_subscription_start_date |
| "Anything else you'd like us to know?" | [new — TBD] | Open-text catch-all — replaces all communication preference dropdowns | Desk cf_intake_notes |

### 4.1.3 Fields Removed from Form

| Field | Disposition |
|-------|-------------|
| Information style preference | Dropped — PHA adapts organically |
| Preferred update timing | Dropped — PHA discovers naturally |
| Caregiver gender preference | Deferred to first appointment booking |
| "Biggest concern" dropdown | Dropped — replaced by open-text catch-all |
| Zip/Postal code | Dropped — was already marked "not required" |
| Registered address (if different) | Deferred to PHA onboarding Week 1 |
| Emergency contact / partner details | Deferred to PHA onboarding Week 1 |
| Other household residents | Deferred to PHA onboarding Week 1 |
| "How should we address you" | Deferred to PHA intro conversation |

### 4.1.4 Jotform Configuration Tasks

| # | Task | Status |
|---|------|--------|
| J-1 | Remove: communication preference dropdowns (info style, timing, gender, biggest concern) | [ ] |
| J-2 | Remove: zip code, registered address | [ ] |
| J-3 | Add: "Anything else you'd like us to know?" optional open-text field | [ ] |
| J-4 | Move: subscription start date to end of form, mark optional | [ ] |
| J-5 | Update: intro copy per Section 4.2.1 | [ ] |
| J-6 | Remove: mid-form apology note | [ ] |
| J-7 | Update: payment framing copy per Section 4.2.3 | [ ] |
| J-8 | Verify: location field (q23) captures Bali area correctly for cf_location routing | [ ] |

**Cross-reference:** These tasks are also listed in onboarding PRD Section 12.4. Same items, captured in both docs for independent execution tracking.

## 4.2 Form Copy

### 4.2.1 Intro Text

**Current:**
> "Thanks for becoming a Padma Care Member. This online format is intended to make filling this form easier for you. It should take between 5-10 minutes max."

**Replace with:**
> "Welcome to Padma Care. We just need a few details to get your membership set up — this takes about 5 minutes. Have your passport handy for the photo upload. Your Personal Health Advisor will be in touch shortly after to get you fully set up."

### 4.2.2 Mid-Form Apology Note

**Current:**
> "A note on Forms in general. We know they stink - but the better information we have from the start, the better we can help you quickly if you ever get sick. Only a bit more to go."

**Action:** Remove entirely. Shorter form makes this unnecessary. Self-deprecating tone undermines confidence.

### 4.2.3 Payment Framing (Before ToS Checkbox)

**Current:**
> "Padma Care is designed to work with a credit card on file. We accept both local and international credit cards for your convenience..."

**Replace with:**
> "Padma Care bills monthly with a card on file — so you never have to prepay for medical services or worry about settling bills at the hospital. We accept all major credit cards (local and international). On the next screen, you'll securely authorize your card through our payment partner, Xendit. This is an authorization only — your card will not be charged until your service begins."

### 4.2.4 Relocating Members Section

Keep. Update heading copy to: "Moving to Bali soon? Choose your start date and your membership activates when you arrive."

---

# 5. Phase 2 — On Form Submission

**Trigger:** Jotform webhook → `padma-integrations/webhooks/padmacare-signup`

These actions fire in parallel with the existing v2.2 Zoho Billing/Xendit orchestration. They are lightweight — no Desk or Drive provisioning at this stage.

## 5.1 Passport Photo Fetch

5.1.1 The system must fetch the passport photo from the Jotform file URL immediately on webhook receipt. Jotform file URLs are ephemeral — they must not be treated as permanent storage.

5.1.2 The system must cache the passport photo locally (filesystem or S3) keyed to the member email. It will be moved to Google Drive at payment success (Section 7A).

5.1.3 The system must log a warning if the fetch fails and retry once. If retry fails, include the failure in the payment-success internal alert so it can be collected manually.

## 5.2 Jotform Payload Cache

5.2.1 The system must cache the full Jotform payload in the padma-integrations state store (the same in-memory or lightweight persistence layer used by the v2.2 signup state). This payload is needed for Desk contact creation and Drive provisioning at payment success, and for drip email personalization (name, email).

## 5.3 Drip Scheduler Armed

5.3.1 The system must arm the drip scheduler for this member on form submission. The first email fires at +1hr if auth has not completed by then.

5.3.2 Drip state (armed, email_1_sent, email_2_sent, etc.) lives in the padma-integrations state store, not in Zoho Desk.

---

# 5A. Phase 2A — System Provisioning (On Payment Success)

**Trigger:** Xendit `payment.session.completed` webhook → padma-integrations

These actions fire only when payment auth is confirmed. This is when the prospect becomes a member and gets a Desk record.

## 5A.1 Zoho Desk Contact Creation

5A.1.1 The system must create a Zoho Desk contact with all fields per the mapping in Section 4.1.1 and 4.1.2, sourced from the cached Jotform payload.

5A.1.2 The system must set `cf_onboarding_stage = provisioned` at creation.

5A.1.3 The system must set `cf_membership_start` from the subscription start date field. If blank, default to current date.

5A.1.4 The system must write `cf_intake_notes` from the "Anything else" field content. If blank, leave empty.

5A.1.5 The system must handle duplicate detection: if a Desk contact with the same email already exists, update rather than create. Log the collision.

**Cross-reference:** Onboarding PRD Section 3.2.3 and Section 12.1 E-1 describe this same action. No conflict — same trigger (payment success), same owner (padma-integrations). Onboarding PRD is the canonical reference for Desk field mapping; this PRD defers to it.

## 5A.2 Google Drive Folder Provisioning

5A.2.1 The system must create a Drive folder: `/Padma Care Members/[LastName, FirstName — MemberID]/`

5A.2.2 The system must create subfolders: `Administrative/` and `Medical/`

5A.2.3 The system must write the folder URL back to Desk contact field `cf_drive_folder`.

5A.2.4 The system must share the folder with the Padma Care shared drive (team access).

**Cross-reference:** Onboarding PRD Section 3.2.2 and Section 12.1 E-2. Same action, same timing. No conflict.

## 5A.3 Passport Photo Migration to Drive

5A.3.1 The system must move the cached passport photo to Drive `Administrative/passport_[MemberID].jpg`.

5A.3.2 If the passport photo cache is missing (fetch failed at form submission), the internal alert must flag this for manual collection.

**Cross-reference:** Onboarding PRD Section 12.1 E-3. Same action. No conflict.

## 5A.4 Internal Alert Email

5A.4.1 The system must fire an internal alert email to the it-alerts distribution group on payment success.

5A.4.2 The alert must include: member full name, email, WhatsApp number, Bali area/location, subscription start date (flagged if > 7 days in future), contents of "Anything else" field verbatim (at the top, prominently), direct link to the new Drive folder.

**Cross-reference:** Onboarding PRD Section 3.2.4 and Section 12.1 E-4. Same alert, same trigger. No conflict.

---

# 6. Phase 3 — Subscription Confirmation Page

**URL:** `/new-subscription-success/?email=X`

**Trigger:** Jotform Thank You redirect (browser-side, immediate).

## 6.1 Page Elements

6.1.1 **3-step progress indicator** — keep existing (Registration → Confirmation → Payment Authorization). Step 2 highlighted.

6.1.2 **Member details display** — name, email, phone populated from query params or API poll. Confirms record was created.

6.1.3 **Heading:** "You're Almost There"

6.1.4 **Body copy:**
> "Thanks, [name] — your Padma Care membership is being set up.
>
> The last step is a quick card authorization through Xendit, our secure payment partner. Padma Care never sees or stores your card details — Xendit handles that securely on our behalf. This is not a charge — it simply saves your card so we can bill seamlessly each month. The authorization amount will show as 0 IDR on your device.
>
> We accept all major credit cards, including international cards. Most Indonesian debit cards also work, though some local banks may not support recurring authorizations — if that happens, just try a different card."

6.1.5 **CTA button:** "Authorize My Card" — links to Xendit payment session URL.

6.1.6 **Below CTA:** "Questions? WhatsApp us at +62 822 6632 3030 — we're happy to walk you through it."

6.1.7 **Remove:** the membership features summary box. Replace with: "Your Personal Health Advisor will reach out within 24 hours to introduce themselves."

## 6.2 Key Design Decisions

6.2.1 The Xendit trust framing and 0 IDR explanation must appear on this page. This context currently exists nowhere in the active flow — it was in the old (now commented-out) email. Prospects are hitting a third-party payment page cold.

6.2.2 Debit card guidance is proactive, not reactive. Don't wait for the failure.

6.2.3 No re-selling. The person already committed. Don't re-list features or pricing.

---

# 7. Phase 4 — Payment Authorization (Xendit)

This phase is owned by Xendit's hosted payment page. Padma Care controls only what happens before and after.

7.1 The Xendit payment session is created by the existing v2.2 orchestration (Zoho Billing subscription → Xendit session → poll for URL).

7.2 On successful auth, Xendit fires `payment.session.completed` webhook to padma-integrations.

7.3 On webhook receipt, the system must execute all Section 5A provisioning actions (Desk contact, Drive folder, passport migration, internal alert).

7.4 On webhook receipt, the system must cancel any pending drip emails for this member.

7.5 The browser redirects to `/payment-success/`.

---

# 8. Phase 5 — Payment Success Page

**URL:** `/payment-success/`

## 8.1 Page Copy

**Heading:** "Welcome to Padma Care"

**Body:**
> "You're officially a Padma Care member, [name]. We're glad you're here.
>
> **What happens next:**
>
> Your Personal Health Advisor will reach out via WhatsApp within 24 hours to introduce themselves. Save their number — they're your first point of contact for anything health-related in Bali.
>
> You'll receive a welcome email shortly with your membership details, key contacts, and a link to our Terms of Service for your records.
>
> That's it. You're set up. If anything ever comes up — a question, a concern, a midnight worry about a fever — reach out. That's what we're here for."

**Sign-off:** "Welcome aboard. — Alex and the Padma Care Team"

**Contact:** "WhatsApp: +62 822 6632 3030 | Email: padmacare@pbmcgroup.com"

## 8.2 Content Removed from This Page

| Current content | Disposition |
|----------------|-------------|
| Invoice/receipt billing details | Move to welcome email (onboarding PRD Phase 2) |
| Cancellation/no-refunds policy | Move to welcome email or Terms of Service link |
| "Contact us before engaging your bank" | Remove entirely — internal concern, not welcome copy |
| "and/or thank you for extending your membership" | Remove — don't hedge between new and returning |

## 8.3 Handoff

Payment success triggers the onboarding PRD Phase 1 (system provisioning at T+0) and Phase 2 (welcome email). This PRD's scope ends here for the happy path.

**Cross-reference:** Onboarding PRD Section 3.2 Phase 1 picks up at this trigger.

---

# 9. Phase 6 — Payment Auth Drip Sequence

## 9.1 Trigger

The drip scheduler activates when a Jotform submission is processed and the Xendit payment session URL is generated, but payment auth has not completed within 1 hour.

## 9.2 Sequence

| Email | Timing | Template | Subject (in config) | Tone |
|-------|--------|----------|---------------------|------|
| 1 | +1hr | `reminder-1hr.html` | Quick step to finish your Padma Care setup | Gentle, assumes distraction |
| 2 | +12hr | `reminder-12hr.html` | Your Padma Care membership is waiting | Helpful, adds debit card guidance and Xendit trust framing |
| 3 | +24hr | `new-url-24hr.html` | New authorization link — Padma Care | Direct — old URL expired, fresh one provided |
| 4 | +60hr | `new-url-60hr.html` | Here's a fresh Padma Care link to complete the sign-up process | Personal final nudge with explicit off-ramp |

## 9.3 Drip Behavior Requirements

9.3.1 The system must cancel all pending drip emails immediately when a Xendit `payment.session.completed` webhook is received for the member.

9.3.2 At +24hr, the system must generate a new Xendit payment session URL (the original URL expires after 24 hours). The new URL must be used in emails 3 and 4.

9.3.3 At +60hr (email 4), the `{{attemptLabel}}` placeholder must reflect the actual attempt number (e.g., "second" if this is the second URL, "third" if manual re-generation occurred in between).

9.3.4 Drip state (`armed`, `email_1_sent`, `email_2_sent`, `email_3_sent`, `email_4_sent`, `exhausted`, `cancelled`) lives in the padma-integrations state store. No Desk record exists during the drip window — the prospect is not yet a member.

9.3.5 After drip exhaustion (+72hr with no auth), the system must fire an internal alert for manual WhatsApp follow-up. The alert must include the member name, email, WhatsApp number, which drip emails were sent, and whether any were opened (if SES tracking is available). No Desk record is created for drip-exhausted prospects — they remain in the padma-integrations state store and Zoho Billing as inactive subscribers.

9.3.6 The system must not send drip emails to members whose `subscription_start_date` is > 30 days in the future. These members receive a modified drip with longer intervals (TBD — flag as open question).

## 9.4 Template Placeholders

**`reminder-1hr.html`** and **`reminder-12hr.html`:**
- `{{name}}` — member first name
- `{{paymentUrl}}` — active Xendit authorization URL

**`new-url-24hr.html`** and **`new-url-60hr.html`:**
- `{{name}}` — member first name
- `{{paymentUrl}}` — NEW Xendit authorization URL
- `{{attemptLabel}}` — ordinal label (e.g., "second", "third")

## 9.5 Design Notes

9.5.1 Brand colors: primary #505CA0 (links), accent #E6854B (CTA buttons).

9.5.2 Inline styles only.

9.5.3 From line: "Padma Care Team <padmacare@pbmcgroup.com>"

9.5.4 Emails 1-3 sign off as "The Padma Care Team." Email 4 signs off as "Alex and the Padma Care Team."

9.5.5 Email 4 includes an explicit off-ramp: "if you've changed your mind, that's completely fine." At 60 hours, giving permission to walk away often converts better than continued pressure.

---

# 10. Zoho Desk — Configuration Required

| # | Item | Notes |
|---|------|-------|
| D-1 | Desk contact creation module in pmg-integrations | Trigger: Xendit payment success webhook (this PRD Section 5A). Aligns with onboarding PRD E-1 |
| D-2 | Custom fields to add | `cf_pha_assigned`, `cf_location`, `cf_drive_folder`, `cf_agreement_signed`, `cf_medical_auth_signed`, `cf_membership_start`, `cf_passport_number`, `cf_onboarding_stage`, `cf_intake_notes`, `cf_gender`, `cf_date_of_birth`, `cf_place_of_birth`, `cf_referral_id` |
| D-3 | `cf_onboarding_stage` enum values | `provisioned`, `pha_introduced`, `docs_sent`, `docs_complete`, `hx_collected`, `mature` |
| D-4 | Contact view / filter for onboarding stage | PHA and ops need visibility into where each member is in the onboarding journey |

**Note:** Pre-auth drip state (`armed`, `email_1_sent`, etc.) does not live in Desk. It lives in the padma-integrations state store. Desk records only exist for members who have completed payment auth.

**Cross-reference:** Onboarding PRD Section 12.2 lists the same fields and enum. No conflict — same trigger, same values.

---

# 11. Acceptance Criteria

## 11.1 Form

11.1.1 The Jotform form contains only the fields listed in Section 4.1.1 and 4.1.2. All fields from Section 4.1.3 have been removed or deferred.

11.1.2 The form intro copy matches Section 4.2.1.

11.1.3 The payment framing copy matches Section 4.2.3.

11.1.4 The mid-form apology note is removed.

11.1.5 The form submits successfully and fires the webhook to padma-integrations.

## 11.2 System Provisioning (On Form Submission)

11.2.1 On Jotform webhook receipt, the passport photo is fetched from the Jotform URL and cached locally within 60 seconds.

11.2.2 The Jotform payload is cached in the padma-integrations state store for downstream use.

11.2.3 The drip scheduler is armed for this member.

## 11.2A System Provisioning (On Payment Success)

11.2A.1 On Xendit payment success webhook, a Zoho Desk contact is created with `cf_onboarding_stage = provisioned` and all mapped fields populated from the cached Jotform payload.

11.2A.2 If a Desk contact with the same email already exists, the system updates rather than creates, and logs the collision.

11.2A.3 A Google Drive folder is created at `/Padma Care Members/[LastName, FirstName — MemberID]/` with `Administrative/` and `Medical/` subfolders.

11.2A.4 The Drive folder URL is written to `cf_drive_folder` on the Desk contact.

11.2A.5 The cached passport photo is saved to Drive `Administrative/passport_[MemberID].jpg`.

11.2A.6 An internal alert email is sent to it-alerts with all fields specified in Section 5A.4.2.

## 11.3 Confirmation Page

11.3.1 The page displays the 3-step progress indicator with Step 2 highlighted.

11.3.2 The page displays member name, email, and phone.

11.3.3 The page copy includes Xendit trust framing, 0 IDR explanation, and debit card guidance per Section 6.1.4.

11.3.4 The CTA button links to the active Xendit payment session URL.

11.3.5 The membership features summary box is removed.

## 11.4 Payment Success Page

11.4.1 The page heading is "Welcome to Padma Care."

11.4.2 The page copy matches Section 8.1 — no billing, cancellation, or chargeback language.

11.4.3 The page displays WhatsApp and email contact information.

## 11.5 Drip Sequence

11.5.1 Email 1 fires at +1hr if auth is not complete. Email 2 at +12hr. Email 3 at +24hr with a new Xendit URL. Email 4 at +60hr with the same new URL.

11.5.2 All pending drip emails are cancelled within 60 seconds of Xendit `payment.session.completed` webhook receipt.

11.5.3 A new Xendit payment session URL is generated at +24hr and used in emails 3 and 4.

11.5.4 Drip state is tracked in padma-integrations state store (not Desk). No Desk record exists during the drip window.

11.5.5 An internal alert fires to the PHA after drip exhaustion (+72hr).

11.5.6 No drip email is sent after auth completion.

---

# 12. Out of Scope

- Post-payment onboarding sequence (welcome email, PHA intro, document pack, medical history, check-in offer) — covered by `padma-care-onboarding-PRD.md`
- Zoho Billing subscription creation and Xendit session orchestration — covered by `padma-integrations PRD v2.2`
- Advocacy track signup
- Insurance coordination
- Jotform form-level abandonment analytics (no native support; third-party options exist but are not scoped here)
- Automated PHA WhatsApp at +4hr (potential future enhancement — manual PHA follow-up is sufficient for now)
- Drip timing modification for far-future subscription start dates (flagged as open question 13.4)

---

# 13. Open Questions

13.1 **Jotform interim page webhook** — can Jotform fire a webhook on multi-page form page advance (not just final submit)? If yes, this enables triggering Zoho Billing/Xendit orchestration while the prospect fills page 2. If no, the optimization is moot and the current single-submit webhook is fine. The 5-10 second wait is acceptable. @Alex — test in Jotform builder.

13.2 **Xendit URL regeneration at +24hr** — does the current padma-integrations Xendit module support generating a new payment session for an existing Billing subscriber? Or does it assume one session per signup? @Alex / @CC — verify against Xendit API docs and current implementation.

13.3 **SES open/click tracking for drip emails** — is SES configured with engagement tracking? If yes, drip exhaustion alert can include which emails were opened. If no, alert just lists which were sent. @Alex — check SES configuration.

13.4 **Drip timing for far-future start dates** — if `subscription_start_date` is > 30 days out (relocating member who signed up early), should the drip still fire at +1/12/24/60hr? Or should timing be stretched? These members are less likely to complete auth immediately and more likely to respond to a reminder closer to their move date. @Alex — decide based on volume (is this common enough to warrant a variant?).

13.5 **MemberID generation** — the Drive folder and passport filename use `[MemberID]`. What is the canonical member ID? Zoho Billing subscriber ID (available at form submission via v2.2 flow)? Zoho Desk contact ID (available only at payment success)? A Padma-generated ID? The passport photo is cached at form submission but named and stored to Drive at payment success, so the ID must be deterministic from the Billing record or generated independently. @Alex — confirm.

13.6 **cf_place_of_birth target system** — padma-integrations PRD v2.2 notes this custom field needs to be created but is ambiguous about whether it goes in Zoho Billing or Zoho Desk. This PRD maps it to Desk. Confirm this is correct and whether Billing also needs it. @Alex

13.7 **Drip exhaustion alert (+72hr)** — requirement 9.3.5 specifies an internal alert to PHA when all 4 drip emails are sent without auth completion. Verify whether this alert already exists in the current padma-integrations codebase. If it does, confirm it includes the fields specified (name, email, WhatsApp, drip history, SES open data if available). If it doesn't, it needs to be built as part of this PRD's implementation. @Alex / @CC — check current code.

---

# 14. Dependencies

- `padma-integrations PRD v2.2` (Approved) — Jotform webhook handler, Zoho Billing orchestration, Xendit session management. This PRD extends that flow, does not replace it.
- `padma-care-onboarding-PRD.md` (Draft) — picks up at payment success. Shares Desk contact fields and Drive folder structure. Desk enum and provisioning logic now aligned — both PRDs trigger at payment success.
- `signup-flow-audit-v1.1.md` — detailed copy recommendations. This PRD formalizes the audit's recommendations into requirements and acceptance criteria.
- Zoho Desk API access — required for contact creation module. Confirmed available (existing Desk instance in use for Crew Care).
- Google Drive API access — required for folder provisioning. Confirm service account permissions.
- AWS SES — configured for Chatwoot. Confirm availability for drip emails from padma-integrations (same SES domain? Separate sending identity?).
- Xendit API — existing integration via padma-integrations. Confirm support for multiple payment sessions per subscriber.

---

# 15. Feeds Into

**Plan:** `padma-integrations/docs/padma-care-signup-PLAN.md` (to be created after Approved status)

**Related docs:**
- `signup-flow-audit-v1.1.md` — copy audit and field reduction analysis (companion working doc)
- `padma-care-onboarding-PRD.md` — post-payment onboarding (companion PRD)
- `padma-integrations PRD v2.2` — core signup orchestration (upstream dependency)
- `Padma_Care_Marketing_Plan_v2.1.md` — brand positioning and conversion psychology context

---

# 16. Future Phases (Out of Scope — Captured for Backlog)

16.1 **Jotform abandonment tracking** — third-party tools (Zuko, Insiteful, GA4+GTM) can provide field-level dropout data. Worth evaluating after the form reduction is implemented and baseline conversion rate is established. Separate spike.

16.2 **Automated PHA WhatsApp at +4hr** — a WhatsApp message from the PHA between drip email 1 and 2 could provide a human touch that email can't. Requires Chatwoot automation or PHA notification trigger. Low priority until drip sequence performance data is available.

16.3 **Drip A/B testing** — once the baseline drip sequence is running, test subject lines, send times, and copy variants. Requires SES engagement tracking (open question 13.3).

16.4 **Debit card failure detection** — if Xendit returns a specific error code for "debit card not supported for recurring," the confirmation page or drip email could proactively suggest switching to a credit card. Requires Xendit error code mapping. @CC — investigate.

16.5 **Multi-page form with interim webhook** — if Jotform supports page-advance webhooks (open question 13.1), the form could be split into page 1 (critical fields → fires webhook → starts Billing/Xendit in background) and page 2 (passport, start date, open-text). Benefit: Xendit URL is ready by the time they submit. Cost: added complexity. Only worth pursuing if 5-10s wait is causing measurable dropout.

16.6 **Lead re-engagement for drip-exhausted prospects** — prospects who exhaust the 72hr drip without completing auth currently remain as inactive Billing subscribers and stale padma-integrations state entries. There is no system for re-engaging them at 30/60/90 days. A lightweight CRM or even a manual review cadence could recapture some of these — they already said yes once. Requires: deciding where lead data lives (Billing report? exported list? eventual CRM?), a re-engagement email or WhatsApp template, and a cadence. Low priority until volume justifies it, but the gap should be acknowledged.
