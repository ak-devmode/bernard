# TODOS

## COMPLETED

### Zoho Desk contact creation from Jotform signup
- [x] Add a new pipeline step — `xendit-session/steps/create-desk-contact.js`
- [x] Map Jotform fields to Desk Managed Care layout (cf_ fields nested under `cf` object)
- [x] Google Drive folder creation (Active Members / LastName, FirstName — MemberID / {Administrative, Medical})
- [x] Update onboarding stage to Provisioned in Zoho Subscriptions
- [x] Signup cache (file-based) for cross-worker data sharing
**Completed:** 2026-03-25

---

## Phase 1 — Go-Live Cleanup (2026-03-22)

### Reminder emails for incomplete card auth
- [x] Build email reminder flow: every 12hrs for 72hrs — `cron/auth-retry.js` handles remind/renew/abandon thresholds
- [x] Recreate payment URL every 24hrs — auth-retry renews at 24hr and 48hr
- [x] Choose email provider — SES (pbmcgroup.com domain verified, 50k/day)
- [x] Build email template with refreshed payment link — 4 templates (1hr, 12hr, 24hr, 60hr)
- [x] Scheduling logic — processedMap tracks per-record thresholds, 72hr abandon with SNS alert
- [x] **Create SSM param `/pmg/integrations/ses_from_address`** — SES is live and sending
- [x] **Create SSM param `/pmg/integrations/xendit_callback_token`** — webhook auth is working
- [x] WhatsApp reminder at 2hr via Chatwoot direct chat API (ca7978c)
**Completed:** 2026-03-27

### Disable Zoho Deluge payment_session webhook handler
- [ ] Old Zoho Deluge function still receives Xendit `payment_session` webhooks in parallel with pmg-integrations
- [ ] Sends error emails ("ERROR: New Payment Session Completed" / "Webhook Processing Error") to integrations@pbmcgroup.com when it can't find cm_session_history records
- [ ] Either disable the Deluge function in Zoho, or remove the Zoho webhook URL from Xendit dashboard callbacks
- [ ] pmg-integrations handles these correctly (expired = log only, completed = update + notify)
**Priority:** High — generates false alarm emails on every expired session
**Added:** 2026-03-28

### Disable Zoho Deluge subscription.created custom function
- [ ] Required for Make.com cutover — old Deluge function fires on subscription creation alongside pmg-integrations
- [ ] Disable in Zoho Subscriptions → Settings → Workflow → Custom Functions
**Priority:** Medium — may cause duplicate processing
**Added:** 2026-03-22

### Move Xendit payment webhook to pmg-integrations
- [ ] `payment_request.completed` / `payment_request.failed` webhooks currently go to Zoho Deluge
- [ ] Build `xendit-payment` connector (similar to `xendit-session`)
- [ ] Update Xendit webhook URL from Zoho to `integrations.pbmcgroup.com/webhooks/xendit-payment`
**Priority:** Medium — works via Zoho for now, move in next phase
**Added:** 2026-03-22

### Clean up test data in Zoho
- [ ] Delete test customers: `test-refid@`, `test-ref2@`, `test-idr@`, `test-duration@` (and any from earlier testing)
- [ ] Delete `alex1@`, `alex2@`, `alex3@` test customers, subscriptions, and cm_session_history records
- [ ] Delete test Desk contact (829219000052825001 — alex2@pbmcgroup.com)
- [ ] Delete associated test subscriptions and cm_session_history records
**Priority:** Low — cosmetic, won't affect production
**Added:** 2026-03-22

### Remove old Whello overlay script
- [ ] Find and remove the old loading overlay script (Indonesian comments, `#loading-overlay`, 5-second timeout)
- [ ] Not in Code Snippets — likely in whdev-oxygen-dev plugin or Oxygen template JS
- [ ] Worked around with `pmg-overlay` ID but orphaned code should be cleaned up
**Priority:** Low — not blocking, cosmetic
**Added:** 2026-03-25

### Update project CLAUDE.md
- [ ] Port is 3012 not 3011
- [ ] Deploy branch is main (not develop)
- [ ] Architecture is parent/child (bus + worker), not flat Express
- [ ] Connectors section: padmacare-signup, xendit-session
- [ ] SSM params: add zoho_org_id, xendit keys
**Priority:** Low — helps future Claude sessions
**Added:** 2026-03-22

### Commit dashboard JSON to repos
- [ ] `docs/grafana-integration-health.json` — latest version needs PR to main
- [ ] `pmg-docs/infrastructure/pmg-dashboard-v4.json` — copied but not git committed
**Priority:** Low — dashboards are live in Grafana, JSON is for version control
**Added:** 2026-03-22

### Merge email-reminders-go-live plan items
- [ ] Review & polish email templates (branding, logo, unsubscribe note)
- [ ] Test email delivery end-to-end with a real signup flow
- [ ] Merge PR #22 if still open (or confirm it was merged/superseded by drip campaign PR)
**Priority:** Medium — drip campaign code is live but plan had QA steps
**Added:** 2026-03-28

### 48-hour production monitoring
- [ ] Watch Grafana Integration Health dashboard for failures
- [ ] Watch CloudWatch logs for errors
- [ ] Confirm first real signup flows through cleanly
**Started:** 2026-03-22
**Added:** 2026-03-22

## Phase 2 — Resilience & Observability

### WhatsApp follow-up at +4 hours for incomplete auth
- [x] WhatsApp at 2hr added via Chatwoot direct chat API (ca7978c) — uses `pc_payment_auth_2hr` template
- [ ] Consider adding a PHA human-touch WhatsApp at +4 hours (between automated 2hr WA and 12hr email)
- [ ] Would require manual trigger or different template with personal tone
**Priority:** Low — 2hr automated WA is live, 4hr human touch is nice-to-have
**Added:** 2026-03-25, updated 2026-03-28

### Run /review and build state tree for testing, alerts and resiliency
- [ ] Run full code review across the integration bus
- [ ] Build state tree diagram showing all possible states and transitions
- [ ] Expand test coverage based on state tree (happy paths, edge cases, failure modes)
- [ ] Add alerting for gaps identified in review
- [ ] Harden resiliency (retry policies, circuit breaker tuning, DLQ verification)
**Priority:** High — production hardening
**Added:** 2026-03-25

## Deferred

### Port auth factory pattern to wellmed-gateway-go
**What:** Port the Node.js auth middleware factory (hmac/apikey/none with configurable headers) back to the Go `apiclient` package.
**Why:** The Go `AuthConfig` struct (config.go:52-60) is less flexible than the factory pattern — it doesn't compose as middleware and adding new auth types requires modifying the struct.
**Pros:** Unified auth patterns across PMG (Node.js) and WellMed (Go) stacks. Easier to add OAuth2, webhook signatures, etc.
**Cons:** Touches a stable Go package that's working fine. Different languages may warrant different idioms.
**Context:** Go version at `wellmed-gateway-go/pkg/apiclient/config.go` lines 52-60. Node.js factory built in `padma-integrations/middleware/auth.js` during Phase 2.5. The factory pattern creates Express middleware per auth type — the Go equivalent would be `http.Handler` wrappers.
**Depends on:** Phase 2.5 completion (build the Node.js version first, validate the pattern, then port).
**Added:** 2026-03-21

### Xendit API key hardcoded in Zoho Deluge scripts
**What:** Production Xendit API key (`xnd_production_...`) is in plain text in at least 3 Deluge custom functions (subscription creation, sync customer, invoice payment). Anyone with Zoho Subscriptions admin access can read it.
**Why:** Security hygiene. If someone leaves the org or Zoho is compromised, the key is exposed. Deluge supports 'connections' which could wrap the key.
**Pros:** Reduces blast radius of a Zoho account compromise. Follows least-privilege.
**Cons:** Requires Zoho connection setup for Xendit + updating 3+ custom functions. Deluge connections have quirks.
**Context:** If auth URL creation migrates from Deluge to Node.js (pmg-integrations), the key moves to SSM and this TODO is moot. Decision pending as part of padmacare-signup Phase 2 (auth retry loop).
**Depends on:** Phase 2 auth retry implementation decision (Xendit direct from Node.js vs. trigger Deluge).
**Added:** 2026-03-21
