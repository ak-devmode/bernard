# padma-integrations — Claude Code Context

## What this service is

Integration bus for Padma Medical Group, replacing Make.com. Parent process (server.js)
receives webhooks and dispatches them via IPC to child processes — one per integration
connector. Each child runs its own pipeline, loads its own SSM secrets, and has an
independent circuit breaker. All secrets come from AWS SSM at startup — hard fail if
any are missing.

**Port:** `3012`
**Deploy target:** `pmg-chatwoot` EC2 (`/var/www/services/padma-integrations`)
**Deployed branch:** `main`
**Process manager:** systemd (`padma-integrations.service`)

---

## Architecture

```
Parent (server.js :3012)
  POST /webhooks/:integration → IPC dispatch to child
  GET /api/status/:integration?key=email → IPC proxy
  GET /health → aggregated from all children
  POST /admin/enable/:integration → re-enable downed integration
      │ fork()
      ▼
Child: padmacare-signup (worker.js)
  Pipeline: parseJotform → billingContact → billingSubscription →
            xenditCustomer → xenditPaySession → writeSessionHistory → storeResult
  Cron: auth-retry (*/10 * * * *) — scan cm_session_history, renew expired sessions
  State: in-memory Map, 48hr TTL, keyed by email

Child: xendit-session (worker.js)
  Pipeline: handleSessionWebhook → createDeskContact
    Step 1: verify callback token, update cm_session_history status
    Step 2: create Drive folder → get URL,
            create/update Desk contact (with Drive URL in cf_passport_url),
            set onboarding stage → Provisioned, clean up signup cache
```

**Bus pattern:** Parent discovers connector manifests in `integrations/`, validates them,
forks a child per connector. Children communicate with parent via IPC messages (see
`bus/ipc.js` for the message contract). Dead-letter queue to S3 if child is unavailable.

---

## Key Files

```
server.js                    — bus entry point, webhook routing, health aggregation
worker.js                    — child process entry point, pipeline execution, IPC
bus/process-manager.js       — child lifecycle, crash recovery, process circuit breaker
bus/ipc.js                   — IPC message types and builders
bus/dlq.js                   — S3 dead letter queue with CloudWatch fallback
bus/metrics-emitter.js       — CloudWatch metrics batching (60s flush)
harness/pipeline.js          — sequential step runner with SNS alerting
harness/retry.js             — exponential backoff with jitter
harness/circuit-breaker.js   — three-state circuit breaker (closed/open/half-open)
harness/policy.js            — tier presets (payments/business/notifications)
lib/zoho-auth.js             — Zoho OAuth2 token manager with dedup
lib/zoho-subscriptions.js    — Zoho Billing API client
lib/zoho-desk.js             — Zoho Desk API client (contacts CRUD, cf_ nesting)
lib/google-drive.js          — Google Drive API (shared drive folder management)
lib/xendit.js                — Xendit Sessions API client
lib/ses.js                   — SES email sender with template interpolation
lib/sns.js                   — SNS alert publisher
lib/ssm.js                   — SSM bulk parameter loader
lib/signup-cache.js          — file-based cross-worker signup data cache (72hr TTL)
middleware/auth.js            — auth factory (hmac/apikey/none)
schema/connector-manifest.js — manifest validation
```

### Connectors

```
integrations/padmacare-signup/     — Jotform → Zoho → Xendit signup pipeline
  index.js                         — manifest (policy: business, cron: auth-retry)
  steps/parse-jotform.js           — validate + normalize Jotform fields
  steps/billing-contact.js         — find or create Zoho Billing customer
  steps/billing-subscription.js    — create subscription (auto_collect=false)
  steps/xendit-customer.js         — create/retrieve Xendit customer
  steps/xendit-payment-session.js  — create card auth session URL
  steps/write-session-history.js   — write cm_session_history for Zoho compat
  steps/store-result.js            — save final state for success page
  cron/auth-retry.js               — drip campaign: email(1hr), WA(2hr), email(12hr), renew+email(24hr), quiet renew(48hr), email(60hr), abandon(72hr)
  templates/reminder-1hr.html      — 1hr gentle nudge email
  templates/reminder-12hr.html     — 12hr follow-up email
  templates/new-url-24hr.html      — 24hr new auth URL email
  templates/new-url-60hr.html      — 60hr final reminder email

integrations/xendit-session/       — Xendit webhook → Zoho + Desk + Drive provisioning
  index.js                         — manifest (verifies x-callback-token, expired=log-only)
  steps/create-desk-contact.js     — Drive folder + Desk contact + onboarding stage
```

---

## SSM Parameters

All parameters live under `/pmg/integrations/` in AWS SSM (ap-southeast-1):

| SSM Path | Used for |
|---|---|
| `/pmg/integrations/zoho_client_id` | Zoho OAuth2 |
| `/pmg/integrations/zoho_client_secret` | Zoho OAuth2 |
| `/pmg/integrations/zoho_refresh_token` | Zoho OAuth2 |
| `/pmg/integrations/zoho_org_id` | Zoho organization ID |
| `/pmg/integrations/xendit_api_key` | Xendit API (production) |
| `/pmg/integrations/xendit_api_key_sandbox` | Xendit API (sandbox, XENDIT_MODE=sandbox) |
| `/pmg/integrations/xendit_callback_token` | Xendit webhook verification |
| `/pmg/integrations/zoho_desk_refresh_token` | Zoho Desk OAuth2 (separate scopes) |
| `/pmg/integrations/zoho_desk_org_id` | Zoho Desk organization ID |
| `/pmg/integrations/google_service_account_key` | Google Drive service account JSON |
| `/pmg/integrations/ses_from_address` | SES sender email for auth-retry |
| `/pmg/integrations/notification_email` | Internal notification recipient |
| `/pmg/integrations/sns_topic_arn` | SNS failure alert topic (→ it-alerts@) |
| `/pmg/kyoo/api_token` | Chatwoot direct chat API auth (shared with Kyoo) |

---

## Adding a New Connector

1. Create `integrations/{name}/index.js` exporting a manifest:
```js
module.exports = {
  name: 'my-integration',    // must match /webhooks/:integration
  version: '1.0.0',
  ssmParams: { myKey: '/pmg/integrations/my_key' },
  auth: { type: 'none' },    // 'hmac' | 'apikey' | 'none'
  policy: 'business',        // 'payments' | 'business' | 'notifications'
  stateKey: 'email',
  onSecretsLoaded(secrets) { /* init API clients */ },
  pipeline: [ async function step(ctx) { /* ... */ } ],
  // Optional:
  schedule: { cron: '*/10 * * * *', handler: async (ctx) => {} },
};
```
2. No registration needed — bus auto-discovers on restart.
3. Context available in pipeline steps: `ctx.payload`, `ctx.result`, `ctx.secrets`,
   `ctx.stateSet(key, state)`, `ctx.stateGet(key)`, `ctx.circuitBreaker`.

---

## Running Locally

```bash
npm install
node server.js
```

Required env vars:
```
AWS_REGION=ap-southeast-1
PORT=3012
# XENDIT_MODE=sandbox  (optional — uses sandbox API key)
```

---

## Testing

```bash
npm test          # runs vitest
npx vitest run    # same thing
```

143 tests across 21 test files. Tests mock all external APIs (Zoho, Xendit, AWS).

---

## Deployment

Push to `main` — GitHub Actions self-hosted runner deploys automatically.

```bash
git push origin main
```

Monitor:
```bash
gh run watch --repo Padma-Medical-Group/pmg-integrations
ssh pmg-chatwoot "sudo journalctl -u padma-integrations -f"
ssh pmg-chatwoot "curl -s http://localhost:3012/health"
```

---

## Known Issues

### 1. State store is in-memory only
`worker.js` state store does not survive restarts. If the service restarts mid-signup,
`GET /api/status/padmacare-signup?key=email` will return `not_found`. Acceptable for v1;
Redis is deferred.

### 2. Auth middleware not wired at bus level
The `middleware/auth.js` factory exists but isn't applied per-integration at the bus
webhook route. Currently, auth verification (e.g., Xendit callback token) happens
inside each connector's pipeline step. This works but is less clean than bus-level
middleware.

### 3. Zoho Desk API: custom fields must be nested
Desk API v1 rejects flat `cf_*` keys on create/update — they must be nested under a
`cf` property in the request body. The `zoho-desk.js` client handles this via
`nestCustomFields()`. The GET response returns both flat and nested formats.

### 4. Zoho Desk Managed Care layout constraints
- `cf_crew_id_1` (CrewID) is a required Number(9) field — Padma Care contacts use `0`
- Custom fields NOT on the Managed Care layout are rejected with "extra parameter" 422
- Layout ID: `829219000000074005`, Account ID: `829219000050566555`
- Desk OAuth scopes must be lowercase: `Desk.contacts.ALL,Desk.search.READ,Desk.tickets.ALL,Desk.settings.READ,Desk.basic.READ`

### 5. Signup cache is file-based, cross-worker
`lib/signup-cache.js` writes to `data/signup-cache/` with 72hr TTL. Survives restarts
(unlike the in-memory state store). Cache is written by `padmacare-signup` (store-result
step) and consumed by `xendit-session` (create-desk-contact step). The cache dir is
owned by `pmg-services` user on the server.
