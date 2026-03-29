# PMG Customisations — Changes from Upstream Chatwoot v4.11.1

This document records every change PMG has made to the upstream Chatwoot codebase. Consult this before merging upstream updates to understand which files have conflict risk.

**Upstream base:** `chatwoot/chatwoot` v4.11.1
**PMG fork:** `Padma-Medical-Group/pmg-chatwoot`
**Working branch:** `staging` (integration: `develop`)

## Conventions

- All PMG modifications to upstream files are marked with `// PMG:` (JS/Vue) or `# PMG:` (Ruby) comments at each change boundary. Search for `PMG:` to find every modification point.
- Captain and Campaigns are gated via Chatwoot's built-in feature flags (`captain_integration`, `campaigns`) — disable those features on the PMG account to hide them. No source code deletion needed.
- PMG-only files (broadcasts, Google Sheets service, etc.) have a `# PMG: Custom feature` header comment.

---

## 1. Frontend Changes

### 1.1 Sidebar Navigation Restructure

**Files:** `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`
**Conflict risk:** Medium (reduced from High by using feature flags instead of comment-outs)

**Changes:**
- Renamed "Conversation" group label → "Conversations"
- Moved Mentions, Unassigned (formerly Unattended), and Pending inside the Conversations group as child nav items
- Added Pending as a new nav item with `defaultStatus: 'pending'` prop
- Renamed "Unattended" → "Unassigned" in nav label (routes unchanged)
- Moved Unattended from inside Settings to bottom of nav as standalone item
- Captain and Campaigns gated via `isFeatureEnabledonAccount` + `FEATURE_FLAGS.CAPTAIN` / `FEATURE_FLAGS.CAMPAIGNS` (same pattern as `hasAdvancedAssignment`)
- Broadcasts nav item (PMG custom feature)

**Why:** CS team workflow requires Pending queue. Captain and Campaigns disabled via feature flags (not code deletion) so upstream merges don't conflict on those blocks.

**How to find changes:** Search `// PMG:` in the file — every modification has a marker comment.

---

### 1.2 Conversation Routes — Pending

**Files:** `app/javascript/dashboard/routes/dashboard/conversation/conversation.routes.js`
**Conflict risk:** Low (additive — two new route objects)

**Changes:**
- Added two new routes: `conversation_pending` and `conversation_through_pending`
- Both use `defaultStatus: 'pending'` to filter the conversation list
- Marked with `// PMG: Pending queue routes`

---

### 1.3 Status Filter Fix (All Tab)

**Files:** `app/javascript/dashboard/components/ChatList.vue`, `app/javascript/dashboard/store/modules/conversations/helpers.js`
**Conflict risk:** Medium

**Problem:** Resolved conversations disappeared from all views. The `conversationFilters.status` always used `activeStatus` ref (defaulting to `'open'`), so resolved conversations were never fetched.

**Changes:**
- `ChatList.vue`: `conversationFilters` computed now forces `status: 'all'` when on the All tab. Added `effectiveStatus` computed for badge display. Marked with `// PMG: All-tab status fix`.
- `helpers.js`: `filterByStatus()` now handles array values — returns `true` if array includes `'all'` or the chat's current status. Marked with `// PMG:` comment.

**Result:** All tab shows all statuses including resolved; Mine/Unassigned tabs remain open-only.

---

### 1.4 sass-embedded Version Pin

**Files:** `package.json`, `pnpm-lock.yaml`
**Conflict risk:** Low — devDependency only, upstream likely to change too

**Problem:** `sass-embedded@1.98+` injects `@use "sass:meta"` into Vue SFC style blocks, breaking `@import 'reset'` in Vite 5. Manifests as `assets:precompile` failure with cryptic Sass error.

**Fix:** `pnpm add -D sass-embedded@npm:sass@1.79.3` — aliases `sass-embedded` to the safe `sass@1.79.3` package.
```json
"sass": "1.79.3",
"sass-embedded": "npm:sass@1.79.3"
```

---

## 2. Backend Changes

### 2.1 Broadcast Feature (Full Custom Feature)

**Files:**
- `app/controllers/api/v1/accounts/broadcasts_controller.rb` (new)
- `app/jobs/broadcasts/broadcast_executor_job.rb` (new)
- `app/services/whatsapp/broadcast_from_sheet_service.rb` (new)
- `app/services/google_sheets_service.rb` (new)
- `app/models/broadcast.rb` (new)
- `app/policies/broadcast_policy.rb` (new)
- `app/models/account.rb` — added `has_many :broadcasts` relationship
- `config/routes.rb` — added broadcasts resource routes
- `db/migrate/` — broadcast-related migrations (4 files)
- Frontend: `app/javascript/dashboard/routes/dashboard/broadcasts/` — routes, pages, components (11 Vue files), API client, Vuex store
- `app/javascript/dashboard/featureFlags.js` — added `BROADCASTS` flag
**Conflict risk:** Low (new files, no upstream overlap) except `config/routes.rb` and `account.rb`

**What it does:**
Allows CS managers to send WhatsApp template broadcasts to recipients from a Google Sheet. Execution flow:
1. Agent creates broadcast via UI → `BroadcastsController`
2. `BroadcastExecutorJob` runs in Sidekiq
3. `BroadcastFromSheetService` reads recipients from Google Sheets, sends via `channel.send_template` (Meta Cloud API)
4. `GoogleSheetsService` fetches credentials from SSM at `/pmg/google/service_account_key`

Access control: broadcast sidebar visible to admin and manager roles only.

**Note:** The standalone `chatwoot-services/broadcast/` CLI tool is deprecated — superseded by this Rails implementation.

---

### 2.1b Direct Send API

**Files:**
- `app/controllers/api/v1/accounts/broadcasts_controller.rb` — added `send_direct` action
- `app/services/whatsapp/direct_send_service.rb` (new) — sends templates to direct recipients, syncs contacts and conversations
- `app/services/whatsapp/template_processor_service.rb` — processes header, body, footer, and button components
- `app/services/whatsapp/populate_template_parameters_service.rb` — builds Meta API parameter objects (text, media, currency, button)
- `app/policies/broadcast_policy.rb` — added `send_direct?` policy method
- `app/controllers/concerns/broadcasts/template_management.rb` (new) — extracted template CRUD from controller
- `config/routes.rb` — added `post :send_direct` to broadcasts collection
- `chatwoot-services/router/direct_chat.js` (new) — Node.js API gateway with WATI-format translation
- `chatwoot-services/router/lib/dlq.js` (new) — S3 dead-letter queue (extracted from router.js)
- `chatwoot-services/router/lib/alert.js` (new) — SES alerting (extracted from router.js)
- `chatwoot-services/router/router.js` — rewritten: removed broadcast/ imports, loads routes from SSM, mounts direct_chat router
**Conflict risk:** Low (new PMG files + `config/routes.rb` and `broadcast_policy.rb`)

**What it does:**
Programmatic WhatsApp template messaging via Chatwoot's broadcast pipeline. External services (Kyoo, pmg-integrations, future integrations) call `POST /api/v1/sendTemplateMessages` on the router. The router validates, resolves the sending inbox, translates the payload, and forwards to the Rails `send_direct` endpoint which creates a broadcast record and sends via Meta Cloud API.

**Architecture:**
```
External service → POST /api/v1/sendTemplateMessages (port 3000)
  → Rate limit (100/min per IP)
  → Auth (timing-safe token comparison via SSM)
  → Validate & sanitize payload
  → Resolve sender_phone → inbox_id (Chatwoot API lookup, cached 1hr)
  → Translate WATI payload → Chatwoot broadcast format
  → POST to Rails send_direct endpoint (port 3001/3002)
    → BroadcastsController#send_direct → Broadcast record
    → DirectSendService → TemplateProcessorService → channel.send_template → Meta API
  → On failure: S3 DLQ + SES alert
```

#### API Reference — `POST /api/v1/sendTemplateMessages`

**Authentication:** `Authorization` header with a static API token (stored in SSM).

**Request body:**
```json
{
  "template_name": "kyoo_appt_qr_in",
  "broadcast_name": "Kyoo Appointment",
  "sender_phone": "6282266323030",
  "receivers": [
    {
      "whatsappNumber": "6281234567890",
      "customParams": [
        { "name": "patient_name", "value": "John Doe" },
        { "name": "qr_code", "value": "https://example.com/qr.png" }
      ]
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `template_name` | string | Yes | Meta-approved template name, or a caller alias (mapped internally via `TEMPLATE_NAME_MAP`) |
| `broadcast_name` | string | No | Human-readable label for logging and audit |
| `sender_phone` | string | No | Sending WhatsApp number (digits only, e.g. `6282266323030`). Resolves to a Chatwoot inbox. Falls back to `DIRECT_CHAT_DEFAULT_INBOX_ID` env var if omitted. Returns 422 if provided but no matching inbox found. |
| `receivers` | array | Yes | 1–500 recipients |
| `receivers[].whatsappNumber` | string | Yes | Recipient phone number. Indonesian numbers normalized automatically (0xxx→62xxx, 8xxx→628xxx). |
| `receivers[].customParams` | array | No | Template variable values as `{ name, value }` pairs |

**Template parameter handling:**

Templates are configured in `TEMPLATE_PARAM_CONFIGS` (in `direct_chat.js`). Each entry controls how `customParams` map to Meta's template components:

- **Positional body** (`body: ['param1', 'param2']`): Named params mapped to `{{1}}`, `{{2}}`, etc.
- **Named body** (no `body` array): Params passed as-is with named keys (`{{name}}`, `{{date}}`, etc.)
- **Header image** (`header_image: 'param_name'`): Extracted as media URL for the template header component.
- **CTA buttons** (`buttons: [{ type: 'url', param: 'param_name' }]`): Extracted as button parameters. For URL buttons, the value is the dynamic suffix appended to the template's base URL (e.g., template URL `https://xen.to/{{1}}` + param value `ahmvyGlu` → `https://xen.to/ahmvyGlu`).

Templates not listed in `TEMPLATE_PARAM_CONFIGS` pass all `customParams` through as named body keys.

**Success response (200):**
```json
{
  "success": true,
  "broadcastId": 73,
  "recipientCount": 1
}
```

**Error responses:**

| Status | Error Code | When |
|---|---|---|
| 401 | `AUTH_INVALID` | Missing or invalid Authorization header |
| 400 | `VALIDATION_ERROR` | Missing template_name, empty receivers, >500 recipients, variable too long |
| 422 | `INVALID_SENDER_PHONE` | `sender_phone` provided but no matching inbox |
| 429 | `RATE_LIMIT_EXCEEDED` | >100 requests/minute from same IP |
| 502 | `UPSTREAM_ERROR` | Chatwoot/Meta API error (message included, HTML never leaked) |

Error format: `{ "success": false, "error": "ERROR_CODE", "message": "Human-readable description" }`

**Side effects:**
- Chatwoot contact created/updated for each recipient (name + phone)
- Chatwoot conversation created/updated with outgoing message record
- On failure: payload saved to S3 DLQ for replay, SES alert sent to ops

**Current template configurations:**

| Template | Caller Name | Body Format | Header | Buttons | Used By |
|---|---|---|---|---|---|
| `kyoo_appt_confirmation_id` | `kyoo_appt_qr_in` | Positional (7 params) | Image (QR code) | — | Kyoo |
| `pc_payment_auth_2hr` | — | Named (`{{name}}`) | — | URL CTA (`payment_url` suffix) | Padma Care drip |

**SSM parameters:**
- `/pmg/kyoo/api_token` — API auth token (shared by all callers)
- `/pmg/chatwoot/api_token` — Chatwoot internal API token for send_direct calls
- `/pmg/router/webhook_routes` — JSON webhook route config (loaded at startup with hardcoded fallback)

**Environment variables (systemd override):**
- `CHATWOOT_API_URL` — Chatwoot Rails API base URL (default: `http://localhost:3001`)
- `DIRECT_CHAT_DEFAULT_INBOX_ID` — Fallback inbox when `sender_phone` not provided (production: `3`)

**Tests:**
- Vitest (Node.js): 42 tests across 5 files — dlq, alert, direct_chat unit, direct_chat endpoint, webhook routing
- RSpec (Rails): DirectSendService unit tests + BroadcastsController#send_direct integration tests

---

### 2.2 Message Finder Cursor Fix

**Files:** `app/finders/message_finder.rb`
**Conflict risk:** Medium

**Problem:** The `messages_before` cursor used `id` for pagination but the API consumer expected `created_at`-based ordering. Messages returned in wrong order when IDs and timestamps diverged.

**Fix:** Changed cursor field from `id` to `created_at` in the `messages_before` scope.

---

### 2.3 Broadcast Service — Okto's Enhancements

**Files:** `app/services/whatsapp/broadcast_from_sheet_service.rb`
**Conflict risk:** Low (PMG-only file)

**Additions by Okto:**
- `META_ERROR_MESSAGES` hash — human-readable error messages for Meta API error codes (translated to English from original Indonesian)
- `sync_contact` method — creates/updates Chatwoot contact from Google Sheet data after successful send
- Improved `send_to` with `message_id` nil check
- Nil-safe `failed_recipients` handling

---

### 2.4 Migration Fix — AddCachedLabelsList

**Files:** `db/migrate/20231211010807_add_cached_labels_list.rb`
**Conflict risk:** Low (migration file, upstream already moved past this)

**Problem:** `ActsAsTaggableOn::Taggable::Cache` constant does not exist in the installed gem version. Migration crashed on fresh database setup.

**Fix:** Added `rescue NameError` around the `Cache.included(Conversation)` call. The column is added successfully; the cache backfill (which would be a no-op on an empty DB) is skipped gracefully.

### 2.1c Broadcast Bug Fixes (Post-Deploy)

**Files:**
- `Gemfile` / `Gemfile.lock` — added `aws-sdk-ssm` gem
- `app/controllers/api/v1/accounts/broadcasts_controller.rb` — added `:template_body` to `before_action :broadcast`
- `app/views/api/v1/models/_broadcast.json.jbuilder` — nil guard for deleted inbox

**Conflict risk:** Low

**What changed and why:**

1. **`aws-sdk-ssm` gem** — `GoogleSheetsService` loads Google credentials from AWS SSM at runtime, but the gem was missing from `Gemfile`. Broadcast jobs in both web and sidekiq containers failed with `"Google credentials not found: aws-sdk-ssm gem not available"`. The gem is already used transitively (same dependency pattern as `aws-sdk-s3`), just needed to be declared explicitly.

2. **`template_body` before_action** — `Broadcasts::TemplateManagement` concern registered `before_action :broadcast, only: [:template_body]` in its `included do` block, but this was not reliably executing before the action, leaving `@broadcast` nil and causing a 500. Fix: explicitly declare `:template_body` in the controller's own `before_action`. The concern's declaration is now redundant but left in place for documentation clarity.

3. **nil inbox guard in jbuilder** — Broadcast index returned 500 when any broadcast record had a deleted/nil inbox. The jbuilder partial unconditionally called `json.partial! inbox`. Fixed with an `if resource.inbox` guard that renders `null` for deleted inboxes, maintaining consistent API response shape.

---

### 2.5 Test Hardening & Simplification (PR #30 Review)

**Files changed:**
- `spec/services/whatsapp/direct_send_service_spec.rb` — +5 tests (header_image, language lookup)
- `spec/controllers/api/v1/accounts/broadcasts_controller_spec.rb` — +3 tests (manager/broadcaster role, header_image passthrough)
- `spec/policies/broadcast_policy_spec.rb` (new) — full role matrix (admin/manager/broadcaster/agent × 3 permission tiers)
- `spec/lib/pmg/phone_normalizer_spec.rb` (new) — mirrors JS `normalizePhone` tests for Ruby parity
- `chatwoot-services/router/test/direct_chat.test.mjs` — +5 tests (positional variables, header_image extraction)
- `chatwoot-services/router/test/direct_chat_endpoint.test.mjs` — fixed pre-existing SSM test failure, updated payload assertion for positional format

**Code simplifications:**
- `lib/pmg/phone_normalizer.rb` (new) — extracted duplicate `normalize_phone` from `broadcasts_controller.rb` and `broadcast_from_sheet_service.rb` into shared `Pmg::PhoneNormalizer` module
- `app/policies/broadcast_policy.rb` — collapsed 15 repetitive methods into two `define_method` loops (82 → 34 lines)

**Upstream upgrade hardening:**
- `app/models/account_user.rb` — moved `broadcaster` enum from position `3` to `10`, leaving headroom (3–9) for upstream role additions
- `db/migrate/20260325042019_rebase_broadcaster_enum_value.rb` — reversible migration: `UPDATE account_users SET role = 10 WHERE role = 3`

**Conflict risk:** Low (tests and new files) except `account_user.rb` enum (coordinate with deploy)

---

## 3. Deployment Files (New — No Upstream Conflict)

| File | Purpose |
|------|---------|
| `docker-compose.pmg.yml` | Two-profile Docker Compose (staging + production) |
| `fetch-secrets.sh` | Generates `.env.staging` / `.env.production` from SSM |
| `deployment/chatwoot-staging-docker.service` | Systemd unit for staging Docker stack boot |
| `deployment/chatwoot-production-docker.service` | Systemd unit for production Docker stack boot |
| `chatwoot-services/router/` | Webhook router + Direct Chat API (Express, routes Meta webhooks, programmatic sends) |
| `chatwoot-services/router/lib/` | Shared utilities: S3 DLQ (`dlq.js`), SES alerting (`alert.js`) |
| `chatwoot-services/router/test/` | Vitest test suite (42 tests) |
| `chatwoot-services/broadcast/` | **Deprecated** — CLI broadcast tool, superseded by Rails UI |
| `.github/workflows/pmg-ci.yml` | PMG CI workflow (lint + specs) |
| `.github/workflows/pmg-deploy.yml` | PMG deploy workflow (Docker build → ECR → manual deploy) |
| `PMG-CHANGES.md` | This file |
| `docs/` | Broadcast usage guide, runbook, infrastructure, CI/CD docs |

---

## 4. Upstream Merge Strategy

**Cadence:** Quarterly or on important upstream patches/features.

**Preparation:**
1. Search all modified upstream files for `// PMG:` or `# PMG:` markers to identify every change point
2. Review this document for conflict risk ratings

**During rebase:**
1. **Feature-flag-gated items** (Captain, Campaigns) — accept upstream's version of the code. The feature flag conditionals will simply wrap the new upstream code. If the upstream structure changed significantly, update the spread pattern.
2. **Marked inline changes** (sidebar restructure, ChatList status fix, routes) — resolve manually using the `// PMG:` markers to identify what PMG added vs what upstream changed.
3. **PMG-only files** — no conflicts expected. Verify they still compile against new upstream APIs.

**After merge:**
1. Run `pnpm eslint` and `bundle exec rubocop -a` to catch syntax issues
2. Rebuild Docker image on staging
3. Verify: sidebar nav, Pending queue, All-tab status filter, broadcasts, webhook routing
4. If a PMG feature breaks, disable its feature flag while investigating — don't block the merge

**High conflict risk files:**
- `app/javascript/dashboard/components-next/sidebar/Sidebar.vue` — nav structure
- `app/javascript/dashboard/components/ChatList.vue` — status filter
- `config/routes.rb` — broadcasts routes
- `package.json` / `pnpm-lock.yaml` — sass-embedded pin

**Medium conflict risk (coordinate with deploy):**
- `app/models/account_user.rb` — `broadcaster: 10` enum (upstream could add roles at 3–9)

**Low/no conflict risk — PMG-only files:**
- `app/services/whatsapp/broadcast_from_sheet_service.rb`
- `app/services/google_sheets_service.rb`
- `app/controllers/api/v1/accounts/broadcasts_controller.rb`
- `lib/pmg/phone_normalizer.rb` — shared phone normalization module
- `app/finders/message_finder.rb` — check if upstream has also changed the cursor logic
