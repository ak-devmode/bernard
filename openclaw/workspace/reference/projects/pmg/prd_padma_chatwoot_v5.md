
# Padma Medical Group — Chatwoot Platform PRD v5.0

**Version:** 5.0
**Date:** 11 March 2026
**Previous Version:** v4.1 (17 February 2026)
**Status:** Draft
**Owner:** Alex Knecht — Dir Growth

### Key Changes (v4.1 → v5.0)
- Restructured phases around go-live on self-hosted (`chat.pbmcgroup.com`)
- Broadcast module elevated to Phase 2 pre-launch requirement with 3-screen spec
- Migration from app.chatwoot.com scoped as API-based (no DB access on hosted cloud)
- Router resilience redesigned: ALB failover → S3 DLQ with manual replay instead of parallel router
- CI pipeline added as Phase 5
- Upstream tracking added as Phase 6
- Backup & DR added as Phase 4 (pre-go-live hard requirement + post-go-live maturation)
- DNS cutover plan added: `chat.pbmcgroup.com` as production, `integration-{service}.pbmcgroup.com` convention for future services
- Template management Screen 2 split: read-only template list for go-live, full CRUD as Phase 3 enhancement
- Broadcast send-path authentication documented as security requirement
- Removed stale items: 677 fallback (4907 now live), WATI references, native Ruby install references
- Docker architecture confirmed: all services (app, Sidekiq, Redis, Postgres) containerized; docker-compose.yml must be committed to repo
- User table and role mapping finalized (12 users, 3 roles)

---

## 1. Executive Summary

### 1.1 Goal
Complete the transition from the paid hosted Chatwoot instance (`app.chatwoot.com`) to the free self-hosted instance running on AWS (`chat.pbmcgroup.com`), with broadcast functionality and clean data migration as launch requirements.

### 1.2 Current State
- **Hosted production** (`app.chatwoot.com`): Live with 3 WhatsApp inboxes, ~7,000 messages/month. Paid subscription. Contains ~5 weeks of conversation and contact data (since early February 2026).
- **Self-hosted staging** (`staging-chat.pbmcgroup.com`): Running on AWS EC2 in `ap-southeast-1`. Dockerized (Chatwoot app, Sidekiq, Redis, Postgres in separate containers). Receives real inbound messages via router dual-delivery. Broadcast module built and tested. Will become production at `chat.pbmcgroup.com` on cutover.
- **Router**: Running on webhost, routes Meta webhooks. Currently dual-delivers to both app.chatwoot.com and staging.
- **WATI**: Fully migrated off. No longer relevant.
- **Broadcast numbers**: 4907 (Padma Clinics) is the permanent broadcast number. 677 backup is available but not actively used.

### 1.3 Timeline
| Milestone | Target Date |
|-----------|-------------|
| Phase 1 complete (pre-launch blockers resolved) | Thursday 13 March |
| CS team UAT on staging | Friday 14 March |
| **Go-live cutover to self-hosted** | **Tuesday 18 March** |
| app.chatwoot.com kept as fallback/archive | Until 10 April |
| app.chatwoot.com decommissioned | 10 April |

### 1.4 Minimum Viable Cutover
Go-live requires all three:
1. Data migration from app.chatwoot.com complete (contacts + conversations)
2. User accounts created with correct roles and inbox assignments
3. Broadcast module working (send from staging with Google Sheets audience)

If data migration is close but not fully validated, go-live may be delayed. This is acceptable — data integrity for the CS team is worth a short delay.

### 1.5 Rollback Strategy
- app.chatwoot.com remains live until 10 April as an archive and emergency fallback.
- Router on webhost can be pointed back to app.chatwoot.com within minutes if needed.
- Outbound chat history will not be duplicated across both systems during any rollback period — this is an accepted risk (similar to the WATI transition earlier this year).
- Broadcasts will run in parallel on both systems during the transition window for safety.

### 1.6 DNS Cutover Plan

**Production domain:** `chat.pbmcgroup.com` — new Route 53 A-record (alias) pointing to the ALB. This is the URL agents will use post-cutover.

**Staging domain:** `staging-chat.pbmcgroup.com` — remains intact and continues pointing to the same ALB. Staging containers will be stopped after transition stabilization and only started for patch validation.

**Integration subdomain convention:** All future integration services use `integration-{service}.pbmcgroup.com` (e.g., `integration-broadcast.pbmcgroup.com`, `integration-zoho.pbmcgroup.com`). ALB listener rules route each subdomain to the appropriate target group. In the interim, before `padma-integrations` has its own deployment, integration traffic routes to the Chatwoot server.

**Cutover DNS steps:**
1. Create `chat.pbmcgroup.com` A-record → ALB (can be done pre-cutover with low TTL)
2. Update Chatwoot env var `FRONTEND_URL=https://chat.pbmcgroup.com`
3. Restart Chatwoot web container
4. Update Meta webhook URLs in the router to point to `chat.pbmcgroup.com`
5. Verify inbound message delivery on the new domain
6. Communicate new URL to CS team (see §1.7)

**Note:** The router and broadcast service do not currently depend on the Chatwoot domain URL — they call the Meta API directly. The domain change only affects the webhook delivery path and agent-facing URLs.

### 1.7 Agent Cutover Communication

Owned by **Kezia**. On cutover day:
- Notify all 12 agents of the new URL (`chat.pbmcgroup.com`) and confirm login credentials
- Confirm that agents do not need to re-authenticate WhatsApp sessions — this is handled server-side via the router switch

---

## 2. Repository & Branch Structure

### 2.1 Repositories

| Repo | Org | Purpose |
|------|-----|---------|
| `pmg-chatwoot` | `padma-medical-group` | Forked Chatwoot with PMG customizations (broadcast module, UI mods, cosmetic changes). This is the deployable application. |
| `padma-integrations` | `padma-medical-group` | Future home for external integrations: Zoho CRM sync, Kyoo relay, Jotform flows. Services that are not tightly coupled to the Chatwoot codebase. |
| `chatwoot/chatwoot` | upstream | Upstream Chatwoot open-source repo. Tracked for patches and releases (see Phase 5). |

**Decision:** The broadcast module lives in `pmg-chatwoot` because it is tightly coupled to the Chatwoot data model (Postgres tables), Sidekiq job processing, and the Vue.js frontend. External integrations that consume Chatwoot APIs from outside belong in `padma-integrations`.

### 2.2 Branch Strategy

| Branch | Purpose | Deployed To |
|--------|---------|-------------|
| `main` | Production-ready code | Self-hosted production instance |
| `staging` | Pre-production validation | `staging-chat.pbmcgroup.com` |
| `develop` | Active development, runs locally | Developer machines |

All three branches exist in `pmg-chatwoot` and mirror the structure used across `kalpa-health` repos.

### 2.3 Merge Flow
```
develop → staging → main
           ↑
     (feature branches)
```
- Feature branches are cut from `develop`.
- PRs merge to `develop` first (local validation).
- `develop` merges to `staging` for UAT and integration testing.
- `staging` merges to `main` for production deployment.
- Docker images are built from `main` for production, from `staging` for the staging environment.

---

## 3. Phase 1 — Pre-Launch Blockers

**Gate:** All items in this phase must be complete before CS team UAT on Friday 14 March.

### 3.1 Data Migration from app.chatwoot.com

**Context:** The hosted Chatwoot cloud instance does not provide direct database (pg_dump) access. Migration must use the Chatwoot REST API for export and the import mechanisms on the self-hosted instance.

**What to migrate:**

| Data | Method | Priority |
|------|--------|----------|
| Contacts (~40k records) | Export CSV from app.chatwoot.com Contacts screen → clean/validate → import via Chatwoot CSV import on staging | Critical |
| Conversations + messages (~5 weeks) | Export via Application API (`GET /api/v1/accounts/{id}/conversations` with pagination) → replay into staging via API | Critical |
| Canned responses | Manual recreation or API export/import | Important |
| Automation rules | Manual recreation | Important |
| Labels | Manual recreation | Low effort |

**Contact import — lessons from previous attempt:**

3.1.1 The previous 40k-record import was split into ~15 slices and produced name/phone number mismatches. The root cause needs to be diagnosed:
- [ ] Examine the import code in the local `pmg-chatwoot` repo to identify batch size limits (Sidekiq job size? Application-level validation?)
- [ ] Determine whether the mismatch was caused by the slicing process or by the import handler itself
- [ ] Build a validated import script that verifies attribution (name ↔ phone number) post-import
- [ ] Test with a small batch (100 records) on staging before running the full import

3.1.2 Contact import must include custom attributes. The Chatwoot CSV import maps non-key columns to the `custom_attributes` JSONB column. Key columns are: `identifier`, `email`, `name`, `phone_number`. Everything else becomes a custom attribute.

3.1.3 After import, `contact_inbox` associations must be created so contacts are linked to the correct WhatsApp inboxes. This may require a Rails console script:
```ruby
account = Account.find(ACCOUNT_ID)
inbox = Inbox.find(INBOX_ID)
account.contacts.each do |contact|
  contact.contact_inboxes.find_or_create_by!(
    inbox_id: inbox.id,
    source_id: contact.phone_number
  )
end
```

**Conversation migration:**

3.1.4 Export conversations from app.chatwoot.com using the Application API with pagination. The API returns conversations with messages, timestamps, contact associations, and status.

3.1.5 Import into staging by creating conversations via API, preserving:
- Contact association (matched by phone number)
- Message content and timestamps
- Conversation status (open/pending/resolved)
- Inbox assignment

3.1.6 Attachments (images, files) stored on app.chatwoot.com's infrastructure will not transfer. This is an accepted trade-off — app.chatwoot.com remains accessible as an archive until 10 April for any historical attachment lookups.

> **⚠️ OPEN QUESTION:** @Alex — Confirm the API access token for app.chatwoot.com has admin scope and test a paginated conversation export before committing to this approach. If the API is too rate-limited or lossy, the fallback is: migrate contacts only, skip conversations, and keep app.chatwoot.com as the conversation archive until April 10.

### 3.2 Custom Attributes & Labels Visibility

3.2.1 Custom attributes must be visible in two places:
- The contact card (right panel when viewing a contact)
- The conversation sidebar (right panel when viewing a conversation)

3.2.2 Define the custom attribute set for each business unit:

| Attribute | Type | Applies To | Display |
|-----------|------|-----------|---------|
| Membership Type | List (Padma Care, Crew Care, Clinics) | All contacts | Contact card + sidebar |
| Vessel Name | Text | Crew Care contacts | Contact card + sidebar |
| Zoho CRM Link | Link | All contacts | Contact card |
| Last Visit Date | Date | Clinics contacts | Contact card |

3.2.3 Labels to create on staging:
- `Pending Response` (yellow) — auto-applied when status = Pending
- Additional labels to be added based on need post-launch

### 3.3 User Accounts & Role Structure

**User table (12 users):**

| User | Chatwoot Role | Primary Inbox | Additional Inboxes | Broadcast Access |
|------|--------------|---------------|-------------------|-----------------|
| Okto | Administrator | Padma Care | Crew Care, Clinics | Yes |
| Alex | Administrator | Padma Care | Crew Care, Clinics | Yes |
| Kezia | Administrator | Padma Care | Crew Care, Clinics | Yes |
| Gita | Manager* | Padma Care | Crew Care | Yes |
| Pebri | Manager* | Crew Care | Padma Care | Yes |
| Santhi | Manager* | Clinics | — | Yes |
| Bello | Agent | Clinics | — | No |
| Gek_Yu | Agent | Clinics | — | No |
| Dewi | Agent | Clinics | — | No |
| Febri | Agent | Clinics | — | No |
| Widya | Agent | Padma Care | — | No |
| Puspa | Agent | Crew Care | — | No |

*Chatwoot does not have a native "Manager" role. The built-in roles are `administrator` and `agent`. Manager-level permissions (broadcast access, cross-inbox visibility) will be handled through:
- Inbox membership (which inboxes the user can see)
- Pundit policy on the broadcast module (a `cs_lead` flag or custom role check)

3.3.1 Tasks:
- [ ] Create all 12 user accounts on staging with correct email addresses
- [ ] Assign inbox memberships per the table above
- [ ] Implement broadcast access control — either a custom attribute on the user model or a simple allowlist in the broadcast module's Pundit policy
- [ ] Test that agents can only see their assigned inboxes
- [ ] Test that managers/admins can access the broadcast module

### 3.4 Broadcast Module — Minimum Viable (see Phase 2 for full spec)

3.4.1 For go-live, the broadcast module must support:
- Selecting a WhatsApp message template (per inbox)
- Loading audience from a Google Sheet (with tab selection)
- Auto-mapping template variables from sheet columns
- Preview recipients before sending
- Sending via Sidekiq background jobs
- Basic history (who sent, when, how many sent/failed)

3.4.2 The existing broadcast functionality built and tested on staging satisfies most of these requirements. Remaining work is documented in Phase 2.

### 3.5 Router Migration

3.5.1 The router service (`router.sh`) currently runs on the webhost and dual-delivers Meta webhook payloads to both app.chatwoot.com and staging-chat.pbmcgroup.com.

3.5.2 For go-live, the router must point exclusively to the self-hosted instance. The router code should be moved to the Chatwoot server (or co-located in the same VPC).

3.5.3 The webhost router can be decommissioned after cutover, replaced by the ALB-based resilience pattern described in §3.6.

> **⚠️ OPEN QUESTION:** @Okto — Confirm whether the current broadcast flow on the webhost (`broadcast.sh`) is still being called independently, or if all broadcast sends now go through the Chatwoot staging module. This determines whether there's a separate service to migrate or just the router.

### 3.6 Router Resilience (ALB + Dead Letter Queue)

**Problem:** Meta only retries webhook delivery for ~15 minutes. If the Chatwoot instance is down (deployment, crash, maintenance), inbound messages are lost.

**Solution:** ALB health check failover to a lightweight Lambda that dumps raw webhook payloads to S3. Manual replay when service recovers.

```
Meta Webhook → ALB
                ├─ Primary target: Chatwoot instance (port 3000)
                │   (health check: HTTP 200 on /health or /)
                │
                └─ Failover (when primary unhealthy):
                    → Lambda → S3 bucket (s3://pmg-webhook-dlq/{date}/{timestamp}.json)
                    → Manual replay script when primary recovers
```

3.6.1 Design principles:
- The DLQ path only activates on extended outages (10+ minutes of failed health checks). Brief restarts (~30 seconds) are handled by ALB connection draining and Meta's own retry logic. Temporary outages are the 99.99% case — this is a safety net, not a primary path.
- No SQS, no auto-replay. A simple replay script reads the S3 bucket, re-delivers payloads to the Chatwoot webhook endpoint in chronological order, and checks for duplicates (by Meta message ID) as it runs. Operator runs it manually after confirming the service is healthy.
- This is far simpler than maintaining a parallel router and eliminates version drift concerns.

3.6.2 This is **not a go-live blocker**. The webhost router serves as the temporary resilience layer until this is built. Target: implement within 2 weeks of go-live.

---

## 4. Phase 2 — Broadcast Module (Full Spec)

### 4.1 Overview

The broadcast module is a custom addition to the Chatwoot UI that allows CS leads and admins to send WhatsApp template messages to audiences sourced from Google Sheets. It lives in the `pmg-chatwoot` repo as a feature-flagged module.

### 4.2 Architecture

**Backend:** Rails controllers + Sidekiq jobs within the Chatwoot application. Uses the existing `broadcasts` and `broadcast_recipients` database tables.

**Frontend:** Vue.js components added to the Chatwoot dashboard, accessible via a sidebar menu item.

**Template management:** Interfaces with the Meta WhatsApp Business API to create, delete, and submit templates for approval. Webhook listener catches approval/rejection status updates and auto-refreshes the UI.

**Audience source (v1):** Google Sheets via Google Sheets API. Config-driven variable mapping (sheet columns → template variables).

**Audience source (future):** Pluggable architecture. Any source that returns an array of `{ phone_number, variables: {} }` objects can be connected. Planned: JSON file upload, scheduled JSON sources via cron, Chatwoot contact filters.

### 4.3 Three Screens

#### 4.3.1 Screen 1 — Broadcast Dashboard

**Purpose:** Overview of all broadcast activity. Entry point for creating new broadcasts.

**Layout:**
- **Top right:** "Create New Broadcast" button
- **Main area:** Table/card list of past broadcasts, sorted by most recent. Each row shows:
  - Template name
  - Inbox (which WhatsApp number)
  - Sent by (agent name)
  - Date/time
  - Status (completed, in progress, failed, scheduled)
  - Sent/failed counts (e.g., "142/145 sent")
- **Lower right:** Broadcast leaderboard by user (who has sent the most broadcasts, total recipients reached). Useful for tracking team activity.
- Each row is clickable → navigates to Screen 3 (Broadcast Detail)

#### 4.3.2 Screen 2 — Template Management

**Purpose:** Template selection, audience assignment, variable mapping, and sending. Full template lifecycle management (create/delete via Meta API) is a post-launch enhancement.

**Go-live MVP functionality:**

**Template list (read-only from Meta):**
- Searchable list of all approved templates, filtered by inbox (WhatsApp number)
- Status indicator per template (approved, pending approval, rejected)
- Auto-sync with Meta: pulls template list from Meta WhatsApp Business API on page load
- Templates are created and managed in Meta Business Manager directly (existing workflow). No in-app template CRUD for go-live.

**Audience assignment (per template):**
- Select Google Sheet (by name/URL)
- Select tab within the sheet
- System reads column headers and displays mapping UI
- Config-driven auto-mapping: template variables → sheet columns (e.g., `{{1}}` → Column B "first_name")
- Row filter: optional filter expression (e.g., `status = "ready"`, `group = "Padma Care"`)

**Preview & send:**
- Preview shows: total recipient count, first 5–10 recipients with name + phone + resolved variable values
- "Send Now" button (available to admins and managers with broadcast access)
- Confirmation dialog before send

**Variable preview:**
- Live preview of the composed message with variables filled in from the first sheet row

**Post-launch enhancement — Template CRUD (Phase 3):**

Adding template creation, editing, and deletion directly in the Chatwoot UI avoids training agents on two tools (Meta Business Manager + Chatwoot). This is valuable but not a go-live blocker since all active templates are already configured.

- "New Template" button: form for name, category, language, header, body with `{{variables}}`, footer, buttons
- On submit: sends to Meta WhatsApp Business API for approval
- Webhook listener: catches Meta template approval/rejection status changes → auto-refreshes status in Chatwoot DB
- Delete button: calls Meta API to delete → removes from local DB

#### 4.3.3 Screen 3 — Broadcast Detail

**Purpose:** Detailed view of a single broadcast's performance and recipient-level status. Reached by clicking a row on the Dashboard.

**Layout:**
- **Top section — error callout box:** If any errors occurred, display them prominently (red/orange alert box). Shows error categories and counts (e.g., "3 recipients failed: invalid phone number").
- **Summary tiles:**
  - Total recipients
  - Sent successfully
  - Failed
  - Delivered (if delivery receipts available)
  - Read (if read receipts available)
  - Timestamp (started at, completed at, duration)
- **Recipient list:** Scrollable table showing each recipient:
  - Name
  - Phone number
  - Status (sent, delivered, read, failed)
  - Error message (if failed)
  - Timestamp
- **Responses:** If recipients replied to the broadcast template, show response count and link to the relevant conversations in Chatwoot

### 4.4 Broadcast Access Control

4.4.1 The broadcast sidebar menu item is visible to all authenticated users.

4.4.2 The "Create New Broadcast" and "Send Now" actions are restricted:
- Administrators: full access
- Managers (Gita, Pebri, Santhi): full access
- Agents: read-only (can view dashboard and detail screens, cannot create or send)

4.4.3 Implementation: Pundit policy on the `BroadcastsController`. Manager access is determined by a list of user IDs or a custom `broadcast_sender` flag on the user record. This avoids modifying Chatwoot's core role system.

4.4.4 **Broadcast send-path authentication.** The broadcast module calls the Meta WhatsApp API to send messages. This is a sensitive path — a compromised or unauthorized caller could abuse the Meta API credentials to send messages on behalf of PMG. The broadcast send endpoint within Chatwoot should authenticate requests to confirm they originate from an authorized Chatwoot session (enforced by the Pundit policy + Rails session auth). If the broadcast backend is ever extracted as a separate microservice, it must authenticate inbound requests from Chatwoot (e.g., via a shared secret or signed JWT stored in Secrets Manager) before forwarding to the Meta API. This prevents a malicious actor from directly hitting the broadcast endpoint and using the Meta API pipe.

### 4.5 Scheduled Broadcasts (Future — Admin Only)

4.5.1 A "Schedule" button on the send confirmation dialog, visible only to administrators.

4.5.2 Scheduling allows:
- Select date/time for a one-time future send
- Configure a recurring schedule (cron expression) for repeated broadcasts
- Assign a data source: Google Sheet (default) or a JSON file (uploaded to S3 or referenced by filename on the server)

4.5.3 Recurring broadcasts register a Sidekiq cron job that:
- Reads the configured data source at the scheduled time
- Resolves the audience and variables
- Sends the broadcast
- Logs the result to broadcast history

4.5.4 A "Test" workflow for scheduled broadcasts: runs the full pipeline but sends only to a designated test number (admin's own number), allowing validation of the data source and variable mapping before it goes live.

4.5.5 This feature is **not required for go-live**. Target: Phase 3 or later.

### 4.6 Audience Source Architecture (Future)

4.6.1 The broadcast module's audience resolution is designed as a pluggable interface:

```
AudienceSource (interface)
├── GoogleSheetsSource (v1 — current)
│   Input: sheet_id, tab_name, column_mapping, row_filter
│   Output: [{ phone_number, variables }]
│
├── JsonFileSource (v2 — planned)
│   Input: file_path (S3 or local), column_mapping
│   Output: [{ phone_number, variables }]
│
├── ChatwootContactFilterSource (v3 — planned)
│   Input: contact_filter_query (Chatwoot native filters)
│   Output: [{ phone_number, variables }]
│
└── ApiSource (v4 — future)
    Input: endpoint_url, auth_config, response_mapping
    Output: [{ phone_number, variables }]
```

4.6.2 Each source returns the same shape. The broadcast send pipeline doesn't care where the recipients came from.

4.6.3 New sources are added by implementing the interface and registering them in the template management screen's "Select Audience Source" dropdown.

---

## 5. Phase 3 — Post-Launch Backlog

**Context:** These items improve the platform but are not blockers for go-live. They should be prioritized and worked through as quickly as possible after cutover.

### 5.1 UI Cleanup (Cosmetic)

These reduce cognitive load for the CS team. Low effort, high impact on usability.

| Change | Current | Target |
|--------|---------|--------|
| Hide "All Conversations" | Visible in sidebar | Hidden |
| Hide "Mentions" | Visible in sidebar | Hidden |
| Hide "Campaigns" | Visible in sidebar | Hidden |
| Hide "Help Center" | Visible in sidebar | Hidden |
| Hide "Captain" | Visible in sidebar | Hidden |
| Rename "Conversations" | Section header | "Channels" |
| Move "Unattended" | Default position | Bottom of sidebar |

Target sidebar layout:
```
🔍 Search
📥 My Inbox
📺 Channels
  ├─ WhatsApp: Clinics CS
  ├─ WhatsApp: Padma Care
  └─ WhatsApp: Crew Care
👥 Contacts
📊 Reports
📢 Broadcasts
⚙️ Settings
  └─ Unattended (bottom)
```

### 5.2 Known Bugs

**5.2.1 Resolved conversations not reappearing on reopen (display bug)**
- Conversations marked as "Resolved" disappear from the UI and do not reappear when a customer sends a new message (which should reopen the conversation).
- Confirmed: data is still in the database — this is a display/state issue, not data loss.
- Bug was reported to Chatwoot upstream — no response received.
- Investigation needed: examine the conversation state machine in the `pmg-chatwoot` codebase (likely in `app/models/conversation.rb` and the associated Vue.js conversation list component).
- The CS team is currently not using the Resolve function because of this bug — so it degrades workflow but is not a show-stopper.

**5.2.2 Assignment rules partial functionality**
- Auto-assignment rules appear to be partially working but have not been fully validated.
- Post-launch: systematically test assignment rules per inbox and document expected behavior.

### 5.3 Canned Responses Expansion

- Current set is minimal. CS team leads should provide a list of common response templates by business unit.
- Canned responses can be imported via API or created in the UI.

### 5.4 Agent Training Materials

Five Loom training videos planned:

| Video | Topic | Duration | Status |
|-------|-------|----------|--------|
| 1 | Getting Started — login, navigation, sidebar | 5 min | Not started |
| 2 | Handling Conversations — reply, canned responses, templates, statuses | 10 min | Not started |
| 3 | Status & Handoff — Pending, Resolved, shift handoffs, filters | 5 min | Not started |
| 4 | Contact Management — contact card, custom attributes, notes, assignment | 5 min | Not started |
| 5 | Business Unit Workflows — unit-specific scenarios | Varies | Not started |

Target: record after go-live once the UI is finalized and cleanup is complete.

### 5.5 Performance Monitoring & Alerting

5.5.1 Current state: CloudWatch agent installed on the EC2 instance. Logs go to `/aws/chatwoot/staging/*`. SES alert for router downtime is configured and tested on the webhost.

5.5.2 Needed:
- CloudWatch alarms for: CPU > 80%, memory > 85%, disk > 80%, Sidekiq queue depth > 100 jobs
- SNS topic → email/Slack notification to Alex and Okto
- Sidekiq monitoring: failed job alerts, dead job queue monitoring
- Uptime check on the Chatwoot web endpoint (external, e.g., AWS Route 53 health check or a simple Lambda ping)

### 5.6 SES Email Configuration

5.6.1 Outbound email notifications (agent assignment alerts, conversation updates) require SES SMTP configuration.

5.6.2 Required Chatwoot env vars:
```
MAILER_SENDER_EMAIL=notifications@pbmcgroup.com
SMTP_ADDRESS=email-smtp.ap-southeast-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=<SES SMTP credential>
SMTP_PASSWORD=<SES SMTP credential>
SMTP_AUTHENTICATION=login
SMTP_ENABLE_STARTTLS_AUTO=true
```

5.6.3 SES domain verification for `pbmcgroup.com` must be completed (DKIM + SPF records in Route 53).

### 5.7 S3 File Uploads Validation

5.7.1 Bucket `chatwoot-staging-attachments` is configured but not tested end-to-end.

5.7.2 Test: send an image via WhatsApp → verify it appears in the conversation → verify it's stored in S3 → verify it's retrievable.

### 5.8 Pending + Escalation Workflow

5.8.1 Notification rules by inbox: configure so that conversations in "Pending" status for > X minutes trigger an alert.

5.8.2 This feeds into the SLA monitoring work in Phase 5 (Advanced Features). For now, a simple automation rule (Pending > 30 min → apply "Escalation" label → email notification) would be a pragmatic first step.

### 5.9 Quality of Life — Discussion Items

> **⚠️ OPEN QUESTION:** @Alex + dev team — What other QoL improvements would benefit CS agents or platform maintainers? Examples to consider:
> - Keyboard shortcuts for common actions
> - Custom notification sounds per inbox
> - Dark mode (if agents work night shifts for Crew Care)
> - Quick-switch between inbox views
> - Bulk actions on conversations (mass resolve, mass reassign)

---

## 6. Phase 4 — Backup & Disaster Recovery

### 6.1 Pre-Go-Live (Hard Requirement)

6.1.1 Automated daily `pg_dump` to S3. This is non-negotiable before production traffic hits the self-hosted instance.

```bash
# Cron job (daily at 2am WIB / 19:00 UTC)
0 19 * * * docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production | gzip > /tmp/chatwoot_backup_$(date +\%Y\%m\%d).sql.gz && aws s3 cp /tmp/chatwoot_backup_$(date +\%Y\%m\%d).sql.gz s3://pmg-chatwoot-backups/daily/ && rm /tmp/chatwoot_backup_$(date +\%Y\%m\%d).sql.gz
```

6.1.2 S3 lifecycle policy: keep daily backups for 30 days, weekly snapshots for 90 days.

6.1.3 Test the restore procedure at least once before go-live: dump from staging → restore into a fresh Postgres container → verify data integrity.

### 6.2 Post-Go-Live Maturation

6.2.1 **Pre-deploy backup as part of the PR-to-main workflow.** When code is merged to `main` and a new Docker image is built, the deployment script should automatically take a pg_dump before restarting containers. This is especially important given the vibecoding workflow — AI-assisted code changes can introduce subtle data issues that are easier to roll back if you have a point-in-time snapshot from immediately before the deploy.

6.2.2 **Redis backup:** Redis AOF persistence is already enabled. Add periodic RDB snapshots to S3 as a secondary safety net.

6.2.3 **S3 attachment backup:** The `chatwoot-staging-attachments` bucket (to be renamed for production) should have versioning enabled and cross-region replication to a backup bucket if attachment data becomes critical.

6.2.4 **Restore runbook:** Document the full restore procedure (stop services → restore Postgres → flush Redis → restart services → verify) as a step-by-step runbook. Test quarterly.

---

## 7. Phase 5 — CI Pipeline

### 7.1 Scope

Continuous Integration for the `pmg-chatwoot` repository. **Not** Continuous Deployment — Docker images will be built manually from tagged releases given the current scale.

### 7.2 Stack

| Component | Tool |
|-----------|------|
| CI platform | GitHub Actions |
| Test framework | RSpec (Rails) + Jest (Vue.js) — Chatwoot already has both |
| Linting | RuboCop (Ruby) + ESLint (JS) |
| Container build | Docker (manual, on release) |

### 7.3 Pipeline

```yaml
# Triggered on: PR to develop, PR to staging, PR to main
jobs:
  lint:
    - RuboCop (Ruby style)
    - ESLint (Vue.js/JS style)

  test:
    - RSpec (existing Chatwoot tests + PMG custom module tests)
    - Jest (Vue.js component tests)

  build-check:
    - Verify Docker image builds successfully (does not push)
```

### 7.4 Implementation Notes

7.4.1 Chatwoot upstream already has a CI configuration (`.github/workflows/`). Start by examining their existing setup and adapting it for the PMG fork.

7.4.2 Add test coverage for all custom code:
- Broadcast module: model specs, controller specs, Sidekiq job specs
- UI modifications: component tests for sidebar changes
- Import scripts: validation tests for contact import

7.4.3 CI should run the existing Chatwoot test suite as well as PMG-specific tests. If upstream tests break due to PMG customizations, those failures must be investigated — they indicate a merge conflict with upstream changes.

7.4.4 Target: CI pipeline operational within 1 week of go-live.

---

## 8. Phase 6 — Upstream Tracking & Merge Strategy

### 8.1 Problem

`pmg-chatwoot` is a fork of `chatwoot/chatwoot`. The upstream repo receives regular patches (security fixes, bug fixes, new features). Without a strategy for tracking and merging upstream changes, the fork will drift and become increasingly difficult to maintain.

### 8.2 Tracking Upstream Releases

8.2.1 Configure GitHub's "Watch" on `chatwoot/chatwoot` for **Releases only**. This sends an email notification when a new version is tagged.

8.2.2 Optionally: set up a GitHub Actions workflow in `pmg-chatwoot` that runs on a weekly schedule, checks the upstream repo for new tags, and creates an issue if a new release is detected:

```yaml
name: Check Upstream Releases
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9am
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check for new Chatwoot releases
        run: |
          # Compare latest upstream tag vs last merged tag
          # Create issue if new release found
```

### 8.3 Merge Strategy

8.3.1 **Keep PMG customizations isolated.** All PMG-specific changes should live in clearly identifiable commits and files. The broadcast module is already in its own directory structure. UI modifications should be in clearly labeled commits.

8.3.2 **Merge process for upstream updates:**
1. Create a branch: `upstream/v4.X.X`
2. Merge the upstream tag into the branch
3. Resolve conflicts (the better-isolated our changes, the fewer conflicts)
4. Run CI (existing Chatwoot tests + PMG tests)
5. Test on staging
6. Merge to `develop` → `staging` → `main`

8.3.3 **Assessment criteria for upstream updates:**
- Security patches: merge immediately
- Bug fixes relevant to our usage: merge promptly
- New features: evaluate whether they conflict with or supersede PMG customizations
- Major version upgrades: evaluate carefully, may require significant merge effort

8.3.4 **Minimize fork divergence.** Avoid modifying core Chatwoot files when possible. Prefer:
- Adding new files (new controllers, new Vue components)
- Using Chatwoot's extension points (if available)
- Feature flags to toggle PMG customizations
- CSS overrides for cosmetic changes rather than modifying core templates

---

## 9. Infrastructure Reference

### 9.1 Docker Architecture

All services run as separate Docker containers on a single EC2 instance:

| Container | Image | Port | Notes |
|-----------|-------|------|-------|
| `chatwoot-web` | PMG custom build | 3001 (→ ALB) | Rails app server |
| `chatwoot-sidekiq` | PMG custom build | — | Background job processing |
| `chatwoot-postgres` | postgres:15 (pgvector) | 5432 (localhost) | Primary database |
| `chatwoot-redis` | redis:7-alpine | 6379 (localhost) | Cache + job queue |

**Production plan:** Both staging and production run on the same VM. After go-live and transition stabilization, staging containers will be stopped and only started when validating patches/updates.

**Docker Compose:** The `docker-compose.yml` must be committed to the `pmg-chatwoot` repo (or a co-located infrastructure directory). This is the single source of truth for the container configuration. All secrets are pulled from AWS Secrets Manager at container start via `fetch-secrets.sh` — no credentials are stored in the compose file or in `.env` files committed to the repo.

### 9.2 AWS Resources

| Resource | Detail |
|----------|--------|
| EC2 Instance | `i-053b3845a7aa0850d` (10.10.3.112), t4g.medium (ARM64, 4GB RAM, 2 vCPU, 20GB EBS) |
| Region | ap-southeast-1 (Singapore) |
| OS | Ubuntu 24.04 LTS |
| IAM Role | `ec2_chatwoot_role` |
| S3 Bucket | `chatwoot-staging-attachments` (to be renamed or duplicated for production) |
| Secrets | `chatwoot/production` in AWS Secrets Manager |
| ALB | Routes HTTPS → target group (port 3001), SSL termination |
| DNS | `chat.pbmcgroup.com` (production), `staging-chat.pbmcgroup.com` (staging) → ALB (wildcard SSL: `*.pbmcgroup.com`) |

### 9.3 Security

- UFW firewall: ports 22, 3000, 3001
- Fail2ban: SSH brute force protection
- Automatic security updates enabled
- 2GB swap configured for compilation stability
- SSH access: VPN security group only
- Secrets: AWS Secrets Manager (no tokens in code, config files, or env on dev machines)

### 9.4 Meta WhatsApp Configuration

| Number | Phone Number ID | Inbox | Purpose |
|--------|----------------|-------|---------|
| +62 813-3939-4907 | (stored in Secrets Manager) | Padma Clinics | Clinics CS + Broadcasts |
| +62 822-6632-3030 | (stored in Secrets Manager) | Padma Care | Member services |
| +62 821-3109-6767 | (stored in Secrets Manager) | Crew Care | Maritime medical |
| +62 821-3109-677 | (stored in Secrets Manager) | Backup | Available, not actively used |

Meta Bearer tokens stored in AWS Secrets Manager:
- Prod: `/pmg/meta/access_token`
- Dev: `/pmg/meta/tokens/dev`
- WABA ID: `/pmg/meta/waba_id`
- Phone IDs: `/pmg/meta/phone_numbers/{number}`

### 9.5 Service Management Quick Reference

```bash
# Docker container status
docker compose ps
docker compose logs -f

# Restart all services
docker compose restart

# Restart specific service
docker compose restart chatwoot-web
docker compose restart chatwoot-sidekiq

# Database console
docker exec -it chatwoot_postgres psql -U chatwoot -d chatwoot_production

# Rails console
docker exec -it chatwoot-web bundle exec rails console

# Check system health
free -h && df -h && uptime

# Database backup (manual)
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production > backup_$(date +%Y%m%d).sql

# Reload secrets from AWS
source ~/fetch-secrets.sh

# View logs
docker compose logs -f chatwoot-web
docker compose logs -f chatwoot-sidekiq
docker compose logs -f postgres
docker compose logs -f redis
```

---

## 10. Advanced Features (Phase 7+)

These are documented for roadmap visibility. None block go-live or near-term operations.

| Feature | Description | Dependency |
|---------|-------------|------------|
| SLA monitoring | 30min warning → email lead, 60min critical → email admin. Business hours respected. | SES configured, monitoring in place |
| Response time dashboard | Per-inbox response time metrics, trend tracking | Chatwoot Reports baseline |
| Zoho CRM → Chatwoot contact sync | Real-time on create, daily batch for updates. Contact naming convention per BU. | `padma-integrations` repo |
| Zoho CRM → Google Contacts | For future WhatsApp Business App integration | Zoho native integration |
| Kyoo reservation confirmation relay | Router accepts Kyoo payloads, converts to Meta template send | Blocked: Meta billing issue |
| Jotform signup flow | New patient signup → Chatwoot contact + welcome template | `padma-integrations` repo |
| AI / Captain evaluation | Translation, FAQ deflection, auto-summary | Phase 7+ |
| Scheduled broadcasts | Cron-based recurring sends with JSON data sources | Broadcast module v2 (see §4.5) |

### 10.1 Contact Sync Architecture (Future)

**Source of truth:** Zoho CRM.

**Sync directions:**
- Zoho CRM → Chatwoot Contacts (via Chatwoot API, custom sync in `padma-integrations`)
- Zoho CRM → Google Contacts (native Zoho integration, for future Business App)

**Contact naming convention:**

| Business Unit | Format | Example |
|--------------|--------|---------|
| Clinics CS | `FirstName LastName` | Rina Dewi |
| Crew Care | `FirstName LastName - Vessel` | John Smith - MV Aurora |
| Padma Care | `FirstName LastName - PC` | Sarah Chen - PC |

---

## 11. Open Questions

| # | Question | Owner | Deadline | Status |
|---|----------|-------|----------|--------|
| 1 | Confirm API access token scope on app.chatwoot.com for data export. Test paginated conversation export. | @Alex | 12 March | Open |
| 2 | Confirm whether Okto's broadcast flow on webhost is still independently active or fully replaced by the staging module. | @Alex / @Okto | 12 March | Open |
| 3 | Determine batch size limit for contact import (Sidekiq vs. application-level). Root-cause the name/phone mismatch from the previous import. | @Dev team | 13 March | Open |
| 4 | Define the full list of canned responses per business unit (CS leads to provide). | @Gita / @Pebri / @Santhi | Post go-live | Open |
| 5 | QoL improvements wishlist — gather input from CS team during UAT. | @Alex | 14 March (UAT) | Open |

---

## 12. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 4.0 | Feb 2026 | Initial PRD | PC |
| 4.1 | 17 Feb 2026 | Staging environment built, restructured as working document | PC + Claude |
| 5.0 | 11 March 2026 | Full restructure around self-hosted go-live. Phases reordered. Broadcast spec expanded. Migration scoped. CI and upstream tracking added. | Alex + Claude |
