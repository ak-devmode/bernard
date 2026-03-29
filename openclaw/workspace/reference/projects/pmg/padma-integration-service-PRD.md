# Padma Integration Service — PRD
**Status:** Approved  
**Version:** 2.2  
**Date:** 2026-03-10  
**Owner:** Alex  
**Repo:** `padma-integrations`

---

## 1. Problem Statement

1.1 The Padma Care new member signup flow is broken in production. Make.com orchestrates Jotform → Zoho Billing → Xendit → Zoho Desk but fails to await the async Xendit payment URL and cannot reliably create the Desk contact. Result: >10% abandonment, incomplete subscriptions, no payment capture.

1.2 Make.com is a paid, opaque dependency with no structured logging, no retry control, and no alerting. Debugging requires stepping through a visual scenario editor rather than reading logs.

1.3 Make.com's role was narrower than assumed: it only creates the Zoho Billing customer + subscription. Payment URL retrieval was always done client-side in WordPress via AJAX polling. Zoho Desk contact creation was never implemented in Make at all — it is missing from the current flow entirely.

1.4 The current flow includes a redundant WordPress relay page (`/process-subscription`) that exists only because Jotform's HTTP POST redirect needed a landing page to forward to Make. This can be eliminated entirely.

1.5 Future integrations (estimated 3–6) have no canonical home — each would be another Make scenario with inconsistent reliability patterns.

---

## 2. Goals

2.1 Replace Make.com entirely for the Padma Care signup flow with a self-hosted Node.js service.

2.2 Fix the broken Xendit URL delivery by implementing proper async polling with exponential backoff instead of a 15s blind wait.

2.3 Eliminate `/process-subscription` WordPress relay page — simplify Jotform to direct webhook + browser redirect.

2.4 Handle all known edge cases and failure modes with structured logging, retry, and alerting.

2.5 Provide a reusable integration harness for future connector pairs with minimal boilerplate.

---

## 3. Simplified Flow (Post-Migration)

```
User submits Jotform
  │
  ├── [Browser] Thank You Page → /new-subscription-success/?email=X  (immediate redirect)
  │     └── Page JS polls GET /api/signup-status?email=X every 3s
  │           - pending  → show skeleton ("preparing your account...")
  │           - ready    → populate name/plan/phone + enable Xendit button
  │           - error    → show friendly message + WhatsApp CTA
  │           - 3min timeout → show error state
  │
  └── [Backend] Webhook POST → /webhooks/padmacare-signup  (async, ACK 200 immediately)
        Step 1: Parse + validate Jotform payload
        Step 2: Zoho Billing — lookup or create contact by email
        Step 3: Zoho Billing — create subscription (idempotency check)
        Step 4: Poll Zoho Billing for Xendit payment URL (exp backoff, max 45s)
        Step 5: Store result in signup state { status, name, phone, plan, xenditUrl }

User on /new-subscription-success/
  → Clicks "Complete Payment Authorization" → Xendit hosted page
  → Xendit redirects → /payment-success/

[Background] Xendit payment status polling (post-signup-ready)
  → completed  → Step 6: create Zoho Desk contact; mark signup done
  → active >24h → SNS alert + Phase 4 abandonment flow
  → expired    → SNS alert + Phase 4 re-engagement flow
```

**Eliminated from flow:**
- `/process-subscription` WordPress relay page — deprecated
- Make.com — all 4 Jotform webhook URLs removed after cutover
- 15s blind wait — replaced with proper exponential backoff polling

---

## 4. Architecture

### 4.1 Two-Layer Design

```
┌─────────────────────────────────────────────┐
│           padma-integrations                │  Node.js / PM2 on Chatwoot EC2
│                                             │
│  Layer 1: API Service                       │
│  - Express HTTP server                      │
│  - POST /webhooks/:integration              │
│  - GET  /api/signup-status?email=X          │
│  - GET  /health                             │
│  - HMAC / token auth middleware             │
│  - SSM secrets loader (startup)             │
│  - Winston structured logger → CloudWatch   │
│                                             │
│  Layer 2: Integration Harness               │
│  - Pipeline runner (sequential ctx steps)   │
│  - Retry wrapper (exp backoff + jitter)     │
│  - Step-level timing + logging              │
│  - Error capture → SNS alert               │
│  - In-memory signup state store (TTL 48hr) │
└─────────────────────────────────────────────┘
```

### 4.2 Connector Model

Each integration is a self-contained module that self-registers on service startup:

```
integrations/
  padmacare-signup/
    index.js        ← registers route + pipeline
    originator.js   ← parse/validate Jotform payload
    billing.js      ← Zoho Billing API calls
    desk.js         ← Zoho Desk API calls
    transform.js    ← field mapping (Jotform → Zoho schemas)
    poller.js       ← Xendit URL + payment status polling
    config.js       ← SSM param paths for this connector
```

New integrations drop into `integrations/` and self-register — core service files untouched.

### 4.3 Signup State Store

In-memory store keyed by email, holds transient state for success page polling:

```js
{
  "user@example.com": {
    status: "pending" | "ready" | "error" | "done",
    name, phone, plan,
    xenditUrl: "https://...",
    xenditStatus: "active" | "completed" | "expired",
    subscriptionId: "...",
    deskContactId: "..." | null,
    createdAt: ISO8601,
    error: "..." | null
  }
}
```

- TTL: 48 hours (covers Xendit 24hr window + buffer); entries auto-evicted
- PM2 restart clears state — acceptable for v1; if persistence needed → Redis (phase decision)
- `/api/signup-status` reads from this store; no Zoho API call on each poll

---

## 5. Layer 1 — API Service

- **5.1** Express server, port configurable via env (confirm no conflict on Chatwoot EC2)
- **5.2** `POST /webhooks/:integration` — ACK 200 immediately, run pipeline async
- **5.3** `GET /api/signup-status?email=X` — returns signup store state for success page polling
- **5.4** `GET /health` — uptime, registered integrations list, Node version
- **5.5** HMAC signature verification for Jotform (key from SSM); static token option for other connectors
- **5.6** Secrets loaded from AWS SSM `/padma/{env}/integrations/` at startup
- **5.7** Winston JSON logs → CloudWatch
- **5.8** Request body: 1MB limit default

---

## 6. Layer 2 — Integration Harness

### 6.1 Pipeline Runner

- `ctx` object passed through all steps: `{ payload, result, meta: { integration, startedAt, steps[] } }`
- Each step: entry log (name), exit log (duration ms), error log + abort on throw
- Step abort → error handler → SNS alert + signup store update

### 6.2 Retry Wrapper

- Per-step config: `{ maxAttempts: 3, backoffMs: 500, factor: 2, jitter: true }`
- Non-retryable: 4xx (except 429) — fail immediately
- Retryable: 5xx, timeouts, network errors, 429
- Log per attempt: number, error type, next delay ms

### 6.3 Error Handling

- Final failure → structured log (integration, step, attempts, error — no PII in logs)
- SNS publish → `it-alerts@pbmcgroup.com`
- Signup store → `status: "error"`, `error: "<user-friendly string>"`
- Success page renders error state with WhatsApp CTA (`+62 822 663 23030`)

### 6.4 Zoho OAuth2 Token Manager (shared singleton)

- Reads `client_id`, `client_secret`, `refresh_token` from SSM at startup
- In-memory `access_token` + expiry timestamp
- Proactive refresh at T-5min; reactive refresh on 401 (single retry then fail)
- All connectors call `zohoAuth.getToken()` — no per-connector auth duplication

---

## 7. Padma Care Signup Connector

### 7.1 Pipeline Steps

**Step 1 — Parse + Validate**
- Parse Jotform `rawRequest` / `formData`
- Validate: email format, required fields (name, phone, plan)
- Hard fail (no retry) if invalid → SNS alert, log rejection reason

**Step 2 — Zoho Billing: Contact Lookup / Create**
- GET contact by email
- Found → use existing `contactId`; log as existing customer
- Not found → POST new contact; capture `contactId`
- If subscription already active + payment completed → skip to done state (idempotency)

**Step 3 — Zoho Billing: Create Subscription**
- POST subscription with `contactId` + plan details
- Capture `subscriptionId` → `ctx.result.subscriptionId`
- Duplicate guard: if subscription exists for this email, use existing

**Step 4 — Poll for Xendit Payment URL**
- Poll `GET /billing/v1/cm_session_history?cf_customer={customer_id}` → check `module_records[0].cf_payment_link_url`
- Schedule: 2s, 4s, 8s, 16s, 15s — max 45s / 6 attempts
- URL found → `ctx.result.xenditUrl`; signup store → `status: "ready"`
- Timeout (45s) → signup store → `status: "error"`; SNS alert

**Step 5 — Xendit Payment Status Polling** *(runs in background after Step 4)*
- Poll Xendit payment link status every 10min for up to 24hrs
- `completed` → trigger Step 6; signup store → `status: "done"`
- `active` at T+24hr → SNS alert; Phase 4 abandonment flow
- `expired` → SNS alert; Phase 4 re-engagement flow

**Step 6 — Zoho Desk: Create Contact** *(post-payment only)*
- Map payload → Desk contact schema
- POST to Zoho Desk API
- Retry 3x with backoff
- Log `deskContactId`; update signup store
- Failure here does not affect signup success — SNS alert + manual fallback

### 7.2 Field Mapping *(confirmed from Make blueprint + PHP plugin)*

**Jotform → Zoho Billing customer:**
| Jotform field | Zoho Billing field |
|---|---|
| `q3_yourName.first` + `q3_yourName.last` | `customer_name` |
| `q33_emailAddress` | `email` (primary lookup key) |
| `q9_mobilePhone.full` | `phone` |
| `q10_yourHome` | `billing_address.address` |
| `q11_city` | `billing_address.city` |
| `q13_country` | `billing_address.country` |
| `q14_zipPostal` | `billing_address.zip` |

**Xendit URL retrieval (confirmed):**
- Endpoint: `GET /billing/v1/cm_session_history?cf_customer={customer_id}`
- Field: `module_records[0].cf_payment_link_url`
- Status field: `module_records[0].cf_status`

**Jotform → Zoho Desk contact** (`POST /api/v1/contacts`):

*Standard fields:*
| Jotform field | Zoho Desk field | Notes |
|---|---|---|
| `yourName[first]` + `yourName[last]` | `lastName` (full name) | Concatenate |
| `emailAddress` | `email` | Primary key |
| `mobilePhone[full]` | `phone` | Already `+62` formatted |
| `yourHome` | `street` | |
| `city` | `city` | |
| `country` | `country` | Default: Indonesia |
| `zipPostal` | `zip` | |

*Custom fields:*
| Jotform field | Zoho Desk field | Notes |
|---|---|---|
| `gender32` | `cf_gender` | Direct map Male/Female |
| `dateOf[month/day/year]` | `cf_date_of_birth` | Convert → `YYYY-MM-DD` |
| `passportNumber` | `cf_passport_numebr` | Note: typo in Zoho field name — keep as-is |
| `fileUpload[0]` | `cf_passport_url` | First URL from array; Jotform must have public file access enabled |
| `mobilePhone[full]` | `cf_whatsapp` | Duplicate of phone field |
| `partnerPhone[full]` | `cf_partner_phone_wati` | |
| `anyOther[full]` | `cf_secondary_phone` | |
| `howShould` | `cf_nama_panggilan` | Preferred address/nickname |
| `whatKind` | `cf_information_style_preference` | Picklist — see mapping below |
| `whenDo` | `cf_contact_preferences` | Picklist — see mapping below |
| `doYou` | `cf_caregiver_gender_preference` | Direct map Yes/No/Any |
| `start_date[month/day/year]` | `cf_onboard_date` | Convert → `YYYY-MM-DD` |
| `location` | `cf_location_province_kabupaten_desa` | |
| `yourRegistered` | `cf_address_1` | Registered address if different |
| `placeOf` | `cf_place_of_birth` | **CREATE this field in Zoho Desk first** |
| Concatenated (see below) | `cf_partner_household_information` | Max 255 chars |

*Picklist value mappings (Jotform → Zoho):*
- `cf_information_style_preference`: "All the nitty-gritty details" → "Detailed" | "I'm most concerned about cost..." → "Financial" | "Medium and balanced" → "Balanced" | "Executive summary only" → "Summary"
- `cf_contact_preferences`: "Lunch" → "Lunchtime" | "Evening (After work hours)" → "Evening - after work hours" | AM/PM/Any → direct
- `cf_gender`, `cf_caregiver_gender_preference`: direct map

*Partner/household concatenation for `cf_partner_household_information`:*
```
"{name20[first]} {name20[last]} ({relationshipTo})" + " | Dependents: {otherDependents}" if present
Truncate at 255 chars. Example: "Jane Smith (Spouse) | Dependents: Emma (5), Oliver (3)"
```

*Fields explicitly not mapped to Desk (per Alex):* partner email, service agreement checkbox, ref number, subscription amount, biggest concern field.

**Remaining to confirm:**
- ~~Zoho Billing plan ID~~ — **Resolved: `803889627` (Padma Care Membership - Monthly, IDR 350,000)**
- [ ] Create `cf_place_of_birth` custom field in Zoho Desk before Phase 3 cutover

### 7.3 Edge Case Matrix

| Case | Handling |
|---|---|
| New customer, no subscription | Standard happy path |
| Existing customer, no subscription | Reuse contact, create subscription |
| Existing customer, subscription active, payment pending | Return existing Xendit URL |
| Existing customer, subscription active, **payment completed** | Signup store → done; success page redirects to /payment-success/ |
| Existing customer, subscription active, **payment link expired** | SNS alert; Phase 4: regenerate + email user |
| Duplicate form submission (same email, in-flight) | Return current store state; no duplicate Zoho calls |
| Email format invalid | Hard fail Step 1; SNS alert; no downstream calls |
| Xendit URL not returned within 45s | Error state; SNS alert; success page shows WhatsApp CTA |
| Zoho Billing 5xx / timeout | Retry 3x; final fail → error state + SNS |
| Zoho Desk contact creation fails | SNS alert; signup still successful (payment done); retry manually via admin |
| PM2 restart mid-flight | State lost; success page JS 3min timeout → error state; user contacts via WhatsApp |
| User closes browser before clicking Xendit | Xendit URL remains valid 24hr; Phase 4 catches if unpaid |

---

## 8. Success Page Contract

`GET /api/signup-status?email=X` — polled by success page JS every 3s:

```json
// pending
{ "status": "pending" }

// ready
{ "status": "ready", "name": "Angga Utomo", "phone": "+628...", "plan": "Padma Care", "xenditUrl": "https://checkout.xendit.co/..." }

// error
{ "status": "error", "error": "We encountered an issue preparing your account. Please contact us via WhatsApp." }

// done (already paid)
{ "status": "done" }
```

**Web dev implementation requirements:**
- Poll every 3s; client-side timeout at 3min → show error state
- `ready` → populate name/phone/plan fields; set button href; enable button
- `done` → redirect immediately to `/payment-success/`
- `error` → show error message + WhatsApp button (`https://wa.me/6282266323030`)

---

## 9. Phase 4 — Abandonment Recovery *(future)*

9.1 **Trigger:** Xendit status `active` at T+24hr or `expired`

9.2 **Admin resend endpoint:** `GET /admin/resend-payment?email=X&token=ADMIN_SECRET`
- Regenerates Xendit URL via Zoho Billing
- Sends re-engagement email to subscriber with new link + 24hr window
- Resets TTL in signup store
- Logs recovery attempt

9.3 **SNS alert format** includes: name, email, plan, original signup timestamp, resend URL — operable from mobile browser; no email reply parsing required.

---

## 10. Infrastructure

| Concern | Decision |
|---|---|
| Hosting | Chatwoot EC2, alongside broadcast service |
| Process manager | PM2 |
| Port | TBD — confirm no conflict with Chatwoot/broadcast service ports |
| Secrets | AWS SSM `/padma/{env}/integrations/` |
| Logs | Winston → CloudWatch |
| Alerts | SNS → `it-alerts@pbmcgroup.com` |
| Deployment | Match broadcast service pattern |
| State persistence | In-memory v1; Redis if restarts become a problem |

---

## 11. Migration Cutover Checklist

- [ ] Map all 4 Make webhook URLs — confirm what each does (web dev)
- [ ] Confirm `/process-subscription` is relay-only; sign off to deprecate (web dev)
- [ ] Register Zoho OAuth2 app; obtain client ID / secret / refresh token
- [ ] Obtain Jotform HMAC webhook key
- [ ] Complete field mapping (Section 7.2)
- [ ] Deploy service to Chatwoot EC2, confirm health endpoint
- [ ] Add `padma-integrations` webhook URL to Jotform (keep Make URLs live)
- [ ] Change Jotform Thank You Page: remove `/process-subscription` HTTP POST → simple redirect to `/new-subscription-success/?email=X`
- [ ] Web dev adds polling JS to `/new-subscription-success/`
- [ ] Parallel test: submit test form, verify both Make + new service handle correctly
- [ ] Validate edge cases (Section 7.3) against test submissions
- [ ] Remove Make webhook URLs from Jotform
- [ ] Deprecate `/process-subscription` WordPress page
- [ ] Shut down WordPress REST endpoint `GET /wp-json/custom/v1/zohobilling/` — exposes OAuth token via plaintext username/password in query string
- [ ] Monitor CloudWatch for 48hrs post-cutover

---

## 12. Phased Build Plan

### Phase 1 — Core Service Scaffold
- [ ] Init repo `padma-integrations`
- [ ] Express server + `/health` endpoint
- [ ] SSM secrets loader
- [ ] Winston structured logger → CloudWatch
- [ ] Pipeline runner with step-level logging
- [ ] Connector auto-registration pattern
- [ ] In-memory signup state store + `/api/signup-status` endpoint

### Phase 2 — Harness Hardening
- [ ] Retry wrapper (exp backoff + jitter)
- [ ] SNS error alerting
- [ ] HMAC auth middleware
- [ ] Per-step timing logs
- [ ] PM2 config + deployment script

### Phase 3 — Padma Care Signup Connector
- [ ] Zoho OAuth2 token manager
- [ ] Jotform payload parser + validation
- [ ] Field mapping implementation (pending Section 7.2)
- [ ] Zoho Billing: contact lookup/create + idempotency
- [ ] Zoho Billing: subscription create
- [ ] Xendit URL poller (exp backoff, 45s max)
- [ ] Xendit payment status poller (background, 24hr window)
- [ ] Zoho Desk contact creation (post-payment)
- [ ] Edge case handling (Section 7.3)
- [ ] End-to-end test
- [ ] Cutover per Section 11

### Phase 4 — Abandonment Recovery
- [ ] T+24hr Xendit status check + SNS alert
- [ ] Admin resend endpoint
- [ ] Subscriber re-engagement email
- [ ] SNS alert with embedded resend URL

---

## 13. Open Questions

1. ~~PMG-only vs Kalpa?~~ — **Resolved: PMG/Padma only.**
2. ~~Which EC2?~~ — **Resolved: Chatwoot instance.**
3. ~~Zoho auth method?~~ — **Resolved: OAuth2 required. Token manager built into service.**
4. ~~Fire-and-forget?~~ — **Resolved: Yes. ACK 200 immediately.**
5. ~~What is breaking in Make?~~ — **Resolved: Blind 15s wait for async Xendit URL; Desk leg hanging intermittently.**
6. ~~Role of `/process-subscription`?~~ — **Resolved: Relay-only. Deprecate at cutover.**
7. ~~Which Zoho Billing API field carries the Xendit payment URL?~~ — **Resolved: `cf_payment_link_url` on `GET /billing/v1/cm_session_history?cf_customer={id}` → `module_records[0].cf_payment_link_url`. Confirmed from WordPress plugin.**
8. ~~Does Zoho Billing push a webhook when Xendit URL is ready?~~ — **Resolved: No webhook. Poll only. WordPress already does this via AJAX — we move it server-side.**
9. What do the 4 Make webhook URLs each do? — @web dev — needed before cutover
10. Port number for service on Chatwoot EC2 — @Alex — needed before Phase 1 deploy

---

## 14. Dependencies

| Dependency | Status |
|---|---|
| Broadcast service repo (reference architecture) | Resolved |
| AWS SSM `/padma/{env}/` path hierarchy | Resolved |
| SNS `it-alerts` topic ARN | Resolved |
| Chatwoot EC2 access + PM2 | Resolved |
| Zoho OAuth2 credentials (client ID, secret, refresh token) | **Extract from WordPress `wp_options` table — already registered. Do not re-register.** |
| Jotform HMAC webhook secret | **Needed before Phase 3** |
| Zoho Billing field mapping + Xendit URL field name | **Resolved — confirmed from blueprint + PHP plugin** |
| Web dev: success page polling JS | **Needed before cutover** |
| Zoho Desk field mapping | **Resolved — `jotform_zoho_final_mapping_v2.0.json`** |
| Web dev: confirmation of `/process-subscription` deprecation | **Needed before cutover** |
