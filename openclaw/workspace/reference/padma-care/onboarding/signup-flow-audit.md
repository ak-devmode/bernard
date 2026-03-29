# Padma Care Signup Flow — Copy Audit & Recommendations

**Version:** 1.1
**Date:** 23 March 2026
**Author:** Alex / Claude
**Status:** Draft — working document

---

# 1. Flow Overview

Current flow: Prospect commits → Jotform (long) → Subscription confirmation page → Xendit card auth → Payment success page. Email drip fires when auth is not completed.

The flow itself is structurally sound. The problem is not the steps — it's the weight and tone at each step. The form collects too much too early, the confirmation page undersells the moment, and the success page reads like a legal disclaimer instead of a welcome.

---

# 2. Jotform — Field Reduction Recommendations

## 2.1 Problem

The form asks for 20+ fields including passport upload, emergency contacts, partner details, communication preferences, and household members. This is comprehensive onboarding data disguised as a signup form. The marketing plan (Section 4.1.7) identifies that the core conversion problem is mechanical inertia, not objection to the service — "98 out of 100 say this is a great service." A long form is exactly the kind of mechanical friction that kills "sure, why not" energy.

The marketing plan also already designs an onboarding sequence (Section 2.2.2) that unfolds over weeks: Week 1 welcome/PHA intro, Week 2 emergency directive, Day 30 medical history. That sequence is the right place for deep data collection — warm, personal, PHA-driven.

**Jotform analytics gap:** Jotform has no built-in field-level abandonment tracking. We cannot see which field people drop off at — only total views vs. submissions. Third-party options exist (Zuko, Insiteful, GA4 + GTM) but add cost and setup complexity. Practical implication: we can't measure form friction, so the best strategy is to remove it. Shorter form = less to go wrong.

## 2.2 Recommended: Keep at Signup

These are fields needed to create the member record, trigger the payment auth flow, and capture operationally critical data that's harder to collect later:

- First Name, Last Name
- Gender (required for Indonesian patient registration systems)
- Date of Birth (same)
- Place of Birth / Country (same — national law requirement)
- Mobile Phone / WhatsApp
- Email Address
- Home Address, City, Country (needed for home visit logistics, billing)
- Passport photo upload (required for any future hospital appointment booking — collecting at signup avoids chasing it later; keep the passport number field as well since it forces better photo quality)
- ToS checkbox
- Subscription start date (optional — for relocating members; move to end of form)
- "Anything else you'd like us to know?" (optional, open text — replaces all four communication preference dropdowns; low-friction for the majority, captures richer signal from those who want to share, and is more useful for future AI member profiling than structured dropdown values)

**Total: ~12 fields + 2 optional. Target completion time: 3-5 minutes.**

## 2.3 Recommended: Move to Onboarding (PHA-Driven, Post-Signup)

| Field | When to collect | How |
|-------|----------------|-----|
| Emergency contact / partner details | Week 1 — PHA intro | Conversational via WhatsApp, not a form |
| Other household residents | Week 1 — PHA intro | Natural follow-up: "anyone else in the household who might use the service?" |
| "How should we address you" | Week 1 — PHA intro | PHA just asks naturally |
| Caregiver gender preference | When first appointment is being booked | Context-appropriate moment |
| Registered address (if different) | Onboarding Week 1 | Low-priority data point |

**Dropped entirely** (not collected at signup or onboarding):

| Field | Rationale |
|-------|-----------|
| Information style preference | PHA adapts organically after first real interaction — a dropdown doesn't make anyone feel seen |
| Preferred update timing | Same — emerges naturally within the first week |
| "Biggest concern" dropdown | Too structured; the PHA micro-prompt ("What's one health question you've been sitting on?") from the onboarding plan (Section 2.2.2.2) is 10x better |
| Zip/Postal code | Marked "Not Required" in current form — if it's not required, don't ask at signup |

## 2.4 Copy Changes to Retained Form

### 2.4.1 Current intro text
> "Thanks for becoming a Padma Care Member. This online format is intended to make filling this form easier for you. It should take between 5-10 minutes max."

**Problem:** "5-10 minutes" is honest but sets a ceiling expectation that feels heavy for a 350k/month decision. "This online format is intended to make filling this form easier for you" is filler — of course it's online, and "easier for you" compared to what?

**Recommended:**
> "Welcome to Padma Care. We just need a few details to get your membership set up — this takes about 5 minutes. Have your passport handy for the photo upload. Your Personal Health Advisor will be in touch shortly after to get you fully set up."

Rationale: honest time estimate for the retained fields (passport photo adds a minute), forward reference to the PHA creates anticipation of the human relationship, signals that signup is not the whole process, passport heads-up avoids a "wait, I need to go find that" moment mid-form.

### 2.4.2 Current mid-form note
> "A note on Forms in general. We know they stink - but the better information we have from the start, the better we can help you quickly if you ever get sick. Only a bit more to go."

**Recommended:** Remove entirely. With the shorter form, this apology is unnecessary. If you keep the longer form, this copy is self-deprecating in a way that undermines confidence — you're essentially saying "we know this is bad but do it anyway."

### 2.4.3 Current payment framing
> "Padma Care is designed to work with a credit card on file. We accept both local and international credit cards for your convenience..."

**Problem:** "designed to work with a credit card on file" is passive and slightly defensive. "For your convenience" is meaningless filler. The copy doesn't explain WHY card-on-file matters (avoids prepayment hassle, enables seamless billing).

**Recommended:**
> "Padma Care bills monthly with a card on file — so you never have to prepay for medical services or worry about settling bills at the hospital. We accept all major credit cards (local and international). On the next screen, you'll securely authorize your card through our payment partner, Xendit. This is an authorization only — your card will not be charged until your service begins."

Rationale: leads with the benefit (no prepayment), names Xendit before they encounter it (reduces surprise), explains auth vs. charge distinction upfront instead of on a page they might not read.

### 2.4.4 Relocating members section

Keep. The "pick your start date" feature is a proven conversion tool (referenced in marketing plan 4.1.7.1). Consider making this more prominent — "Moving to Bali soon? Choose your start date and your membership activates when you arrive."

---

# 3. Subscription Confirmation Page

## 3.1 Current Copy Audit

**What works:**
- 3-step progress indicator (Registration → Confirmation → Payment Authorization) — keep this
- Member details display (name, email, phone) — confirms the record was created, builds confidence

**What doesn't work:**

3.1.1 **"We are currently preparing your member account in the background."** Back-office language. The member doesn't care about your backend processes. Replace with something that reinforces their decision.

3.1.2 **"The final step is to provide credit card authorization for your membership fees and any validated and authorized medical charges from services you access through Padma."** Too long, too formal, slightly anxiety-inducing ("any validated and authorized medical charges" sounds like an open-ended commitment). The auth explanation should have already happened in the form (see 2.4.3 above).

3.1.3 **Membership summary box at the bottom.** The person already bought. Re-listing features at this stage is selling to a sold customer. It creates a "wait, did I make the right decision?" re-evaluation moment right before the critical payment step.

3.1.4 **CTA: "Complete Payment Authorization."** Technically accurate, emotionally cold. This button is the single highest-friction point in your entire funnel and it reads like a tax form.

## 3.2 Recommended Copy

**Page heading:** "You're Almost There" (or "One Last Step")

**Body copy:**
> "Thanks, {{name}} — your Padma Care membership is being set up.
>
> The last step is a quick card authorization through Xendit, our secure payment partner. This is not a charge — it simply saves your card details so we can bill seamlessly each month. The authorization amount will show as 0 IDR.
>
> We accept all major credit cards, including international cards. Most Indonesian debit cards also work, though some local banks may not support recurring authorizations — if that happens, just try a different card."

**CTA button text:** "Authorize My Card" or "Complete Setup"

**Below CTA (small text):**
> "Questions? WhatsApp us at +62 822 6632 3030 — we're happy to walk you through it."

**Remove:** the membership features summary box. Replace with nothing, or a single reassuring line: "Your Personal Health Advisor will reach out within 24 hours to introduce themselves."

## 3.3 Key Additions

3.3.1 **Xendit framing.** The old (now commented-out) email had great copy for this: "We have partnered with Xendit to securely store your payment credentials (we actually never take possession of your private financial information)." This trust-building context currently exists nowhere in the active flow. It must live on this page.

3.3.2 **0 IDR authorization explanation.** Also from the old email. People see a 2FA notification for "0.00 IDR" and get confused or suspicious. Explain it before they encounter it.

3.3.3 **Debit card guidance.** Proactive, not reactive. Don't wait for the failure — tell them upfront that credit cards work best.

---

# 4. Payment Success Page

## 4.1 Current Copy Audit

This page is the biggest problem in the flow. The first thing a new member reads after completing signup is paragraphs about:
- Invoice receipts and billing procedures
- Cancellation and no-refunds policy
- "Please contact us before engaging your bank or credit card provider"

This is defensive, legal-department copy. It communicates anxiety about chargebacks, not excitement about a new member. The emotional arc should peak here — this person just committed, authorized their card, and completed a multi-step process. Reward that.

## 4.2 Recommended Copy

**Page heading:** "Welcome to Padma Care"

**Body:**
> "You're officially a Padma Care member, {{name}}. We're glad you're here.
>
> **What happens next:**
>
> Your Personal Health Advisor will reach out via WhatsApp within 24 hours to introduce themselves. Save their number — they're your first point of contact for anything health-related in Bali.
>
> You'll receive a welcome email shortly with your membership details, key contacts, and a link to our Terms of Service for your records.
>
> That's it. You're set up. If anything ever comes up — a question, a concern, a midnight worry about a fever — reach out. That's what we're here for."

**Sign-off:**
> "Welcome aboard. — Alex and the Padma Care Team"

**Below, smaller:**
> "WhatsApp: +62 822 6632 3030 | Email: padmacare@pbmcgroup.com"

## 4.3 What to Remove or Relocate

| Current content | Recommendation |
|----------------|----------------|
| Invoice/receipt billing details | Move to welcome email |
| Cancellation/no-refunds policy | Move to welcome email or Terms of Service link |
| "Contact us before engaging your bank" | Remove entirely from member-facing copy — this is an internal concern, not a welcome message |
| "and/or thank you for extending your membership" | Remove — don't hedge between new and returning, it weakens the moment |

---

# 5. Payment Auth Reminder Email Sequence

## 5.1 Sequence Design

| Email | Timing | Template file | Subject line (in config) | Tone |
|-------|--------|--------------|-------------------------|------|
| 1 | +1 hour | `reminder-1hr.html` | Quick step to finish your Padma Care setup | Gentle, assumes distraction |
| 2 | +12 hours | `reminder-12hr.html` | Your Padma Care membership is waiting | Helpful, adds debit card guidance |
| 3 | +24 hours | `new-url-24hr.html` | New authorization link — Padma Care | Direct, fresh URL (old one expired) |
| 4 | +60 hours | `new-url-60hr.html` | Here's a fresh Padma Care link to complete the sign-up process | Personal final nudge, explicit off-ramp |

After email 4 with no completion → PHA manual WhatsApp follow-up.

## 5.2 Template Files and Placeholders

Four separate HTML files in `padma-integrations/integrations/padmacare-signup/templates/`:

**`reminder-1hr.html`** and **`reminder-12hr.html`:**
- `{{name}}` — member first name
- `{{paymentUrl}}` — active Xendit authorization URL

**`new-url-24hr.html`** and **`new-url-60hr.html`:**
- `{{name}}` — member first name
- `{{paymentUrl}}` — NEW Xendit authorization URL (fresh generation at +24hr)
- `{{attemptLabel}}` — ordinal label, e.g., "second", "third"

Subject lines live in the service config, not in the templates.

## 5.3 Design Notes

5.3.1 All emails use Padma Care brand colors: primary #505CA0 (links), accent #E6854B (CTA buttons).

5.3.2 Inline styles only (email clients strip `<style>` blocks).

5.3.3 From line: "Padma Care Team <padmacare@pbmcgroup.com>"

5.3.4 Emails 1-3 sign off as "The Padma Care Team." Email 4 signs off as "Alex and the Padma Care Team" — personal touch on the final automated contact.

5.3.5 Email 4 includes an explicit off-ramp ("if you've changed your mind, that's completely fine"). At 60 hours, giving permission to walk away often converts better than continued pressure.

---

# 6. Action Items

- [X] Reconfigure Jotform: remove communication preference fields (info style, timing, gender, biggest concern), remove zip code, remove registered address — Alex in Jotform builder
- [X] Reconfigure Jotform: add "Anything else you'd like us to know?" optional open-text field at end — Alex in Jotform builder
- [X] Reconfigure Jotform: move subscription start date to end of form as optional — Alex in Jotform builder
- [X] Update Jotform intro copy (Section 2.4.1) and payment framing copy (Section 2.4.3) — Alex in Jotform
- [X] Remove mid-form apology note (Section 2.4.2) — Alex in Jotform
- [X] Rewrite subscription confirmation page copy (Section 3.2) — Alex/dev in WordPress
- [X] Add Xendit trust framing and 0 IDR explanation to confirmation page (Section 3.3)
- [X] Rewrite payment success page (Section 4.2) — Alex/dev in WordPress
- [X] Relocate billing/cancellation/legal content to welcome email or ToS link (Section 4.3)
- [X] Deploy 4 email templates to `padma-integrations/integrations/padmacare-signup/templates/`
- [x] Add subject lines to service config (Section 5.1 table)
- [X] Implement 4-step drip scheduler in padma-integrations (+1hr, +12hr, +24hr new URL, +60hr new URL)
- [X] Test debit card failure messaging — confirm Xendit returns a clear error when local debit is rejected
- [ ] Update PHA onboarding playbook: add passport collection to Week 1 if not already captured, add emergency contact/partner collection, add "how should we address you" prompt
- [ ] Consider: add a WhatsApp message from PHA at +4 hours if auth not completed (human touch before email #2)
- [X] Fix phone number display across all pages to +62 822 6632 3030 (consistent spacing)

---

# Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 22 Mar 2026 | Alex/Claude | Initial audit — form reduction, page copy rewrites, email sequence design |
| 1.1 | 23 Mar 2026 | Alex/Claude | Jotform analytics gap documented (no field-level abandonment tracking). Passport photo + number kept at signup (number forces better photo quality). Communication preference dropdowns replaced with single open-text catch-all. Email templates finalized as 4 separate files with subject lines in config. Phone number spacing standardized. Action items expanded with PHA onboarding handoff tasks. |
