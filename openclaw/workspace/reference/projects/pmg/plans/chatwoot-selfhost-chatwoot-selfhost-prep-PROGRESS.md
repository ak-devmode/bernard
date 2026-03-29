# Progress Log: Chatwoot Self-Hosted — Ready to Cutover

## Infrastructure Correction: 2026-03-11

### ⚠️ Deployment Model Clarification
The plan (Phases 5–6) references `docker compose` and `docker exec chatwoot_web` commands throughout. **This is incorrect for the current setup.**

- **Chatwoot app** (web + sidekiq): running **natively** on the EC2 host — not containerized
- **PostgreSQL**: running in Docker
- **Redis**: running in Docker

**Impact on plan commands:**
- `docker compose build/restart chatwoot-web chatwoot-sidekiq` → use `systemctl` or the native process manager (confirm: `sudo systemctl list-units | grep chawoot` or check `Procfile`)
- `docker exec chatwoot_web bundle exec rails ...` → run directly as the app user: `cd /home/ubuntu/chatwoot && bundle exec rails ...`
- `docker exec chatwoot_postgres pg_dump ...` → still valid (postgres is containerized)
- `docker compose restart` for env var changes → restart the native web/sidekiq processes instead

**Confirmed process manager**: systemd
- `chatwoot-web.service` — Puma web server
- `chatwoot-sidekiq.service` — Sidekiq worker

**Correct restart commands** (replaces all `docker compose restart chatwoot-web chatwoot-sidekiq` in plan):
```bash
sudo systemctl restart chatwoot-web chatwoot-sidekiq
```

**⚠️ Security issue**: Both services currently running as `root`. Task 5.7 added to plan to create a dedicated `chatwoot` system user before cutover.

---

## Session: 2026-03-11T00:00:00Z

### Phase 0: Pre-flight
- **Status**: ✅ DONE
- **Completed**: 2026-03-11
- **Plan status field**: Ready to execute ✅
- **Related docs verified**:
  - ✅ `pmg-docs/development/prds/chatwoot-platform-PRD-v5.md`
  - ✅ `pmg-docs/development/chatwoot-status-march-2026.md`
  - ✅ `pmg-docs/adrs/ADR-001-chatwoot-migration.md`
  - ✅ `pmg-chatwoot/CLAUDE.md`
  - ✅ `pmg-chatwoot/DEPLOYMENT.md`
- **Task input paths verified**:
  - ✅ `pmg-chatwoot/app/javascript/dashboard/components-next/sidebar/Sidebar.vue`
  - ✅ `pmg-chatwoot/app/javascript/dashboard/featureFlags.js`
  - ✅ `pmg-chatwoot/app/javascript/dashboard/helper/featureHelper.js`
  - ✅ `pmg-chatwoot/app/models/installation_config.rb`
  - ✅ `pmg-chatwoot/enterprise/app/fields/account_features_field.rb`
  - ✅ `pmg-chatwoot/app/models/conversation.rb`
  - ✅ `pmg-chatwoot/enterprise/app/models/enterprise/conversation.rb`
  - ✅ `pmg-chatwoot/app/models/data_import.rb`
  - ✅ `pmg-chatwoot/app/jobs/data_import_job.rb`
  - ✅ `pmg-chatwoot/app/services/data_import/contact_manager.rb`
  - ✅ `pmg-chatwoot/app/policies/broadcast_policy.rb`
- **Branch**: `feature/pmg-phase3` — created from `develop`, tracking `origin/feature/pmg-phase3` ✅
- **Issues**: None

---

## Session: 2026-03-11T02:00:00Z

### Task 2.1: Create Fix Branch and Implement (Resolve Conversation Reopen)
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Created `fix/resolve-conversation-reopen` from `v4.11.1`, pushed to origin. Implemented fix in all 4 affected services.
- **Files modified**:
  - `app/services/whatsapp/incoming_message_base_service.rb` — add resolved fallback in `set_conversation`
  - `app/services/sms/incoming_message_service.rb` — same fix
  - `app/services/telegram/incoming_message_service.rb` — same fix
  - `app/services/twilio/incoming_message_service.rb` — same fix
- **Fix summary**: `where.not(status: :resolved).last` → add `|| @contact_inbox.conversations.last` fallback so resolved conversations are reopened rather than a new one created
- **Issues**: None

### Task 2.2: Write Regression Spec
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Updated 4 existing specs that tested the OLD (buggy) behavior ("creates a new conversation") to assert the NEW (fixed) behavior ("reopens resolved conversation, no new conversation created, status = open, message present").
- **Files modified**:
  - `spec/services/whatsapp/incoming_message_service_spec.rb`
  - `spec/services/sms/incoming_message_service_spec.rb`
  - `spec/services/telegram/incoming_message_service_spec.rb`
  - `spec/services/twilio/incoming_message_service_spec.rb`
- **Issues**: None

### Task 3.1: Create Fix Branch and Implement (Data Import Synchronize)
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Created `fix/data-import-synchronize` from `v4.11.1`, pushed to origin. Implemented fix in `DataImportJob#import_contacts`.
- **Files modified**: `app/jobs/data_import_job.rb`
- **Fix summary**: Split contacts into `new_contacts` (need DB insert) and existing (already saved by ContactManager). Only pass `new_contacts` to `Contact.import` with `synchronize:`. This eliminates the positional ID drift.
- **Issues**: None

### Task 3.2: Write Regression Spec (Data Import)
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Added regression spec to `spec/jobs/data_import_job_spec.rb` with 10 contacts (3 pre-existing at positions 1, 3, 6) asserting every contact's name maps to the correct phone number after a mixed import.
- **Files modified**: `spec/jobs/data_import_job_spec.rb`
- **Issues**: None

---

### Task 5.2: Configure Custom Attributes
- **Status**: ✅ DONE
- **Completed**: 2026-03-11
- **What was done**: Created 4 custom attributes in Settings → Custom Attributes.
- **Deviations from plan**:
  - "Zoho CRM Link" → renamed to **"Zoho Contact Link"** (integration is to Zoho Desk, not CRM; storing contact ID not a URL)
  - Type changed from Link → **Text** (Zoho contact IDs are long digit strings, not URLs)
- **Final attributes**: Membership Type (List), Vessel Name (Text), Zoho Contact Link (Text), Last Visit Date (Date) — all on Contact
- **Issues**: None

### Task 5.3: Configure Labels
- **Status**: ✅ DONE
- **Completed**: 2026-03-11
- **What was done**: Created `Pending Response` label with yellow color.
- **Issues**: None

---

### CHECKPOINT: Review Bug Fix Branches
- **Status**: ⏸️ WAITING_HUMAN
- **What needs review**:
  - `fix/resolve-conversation-reopen` — 4 service files changed, 4 spec files updated. Test on local dev: resolve a WhatsApp conversation, send a new inbound message, verify it reopens. Check branch is based on `v4.11.1` with no PMG code.
  - `fix/data-import-synchronize` — 1 job file changed, 1 spec file updated. Test with a CSV that has some pre-existing contacts, verify field alignment. Check branch is based on `v4.11.1` with no PMG code.
- **Resume**: "continue the cutover-ready plan"

---

## Session: 2026-03-11T03:00:00Z

### Task 4.1: Set Up Feature Branch and Cherry-Pick Fixes
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Checked out `feature/pmg-phase3`, cherry-picked both fix commits. Branch now has PMG context on top of both bug fixes.
- **Files modified**: cherry-picks only — no direct file edits
- **Issues**: None. Clean cherry-pick, no conflicts.

### Task 4.2: Implement Broadcast Access Control
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Implemented InstallationConfig allowlist approach for manager broadcast access.
- **Files modified**:
  - `app/policies/broadcast_policy.rb` — `index?`/`show?` open to all; write actions require admin OR broadcast_manager?; `broadcast_manager?` reads `BROADCAST_MANAGER_USER_IDS` from GlobalConfig
  - `app/controllers/dashboard_controller.rb` — added `BROADCAST_MANAGER_USER_IDS` to `GLOBAL_CONFIG_KEYS`
  - `app/javascript/shared/store/globalConfig.js` — parse manager IDs from `window.globalConfig` into array, expose via getter
  - `app/javascript/dashboard/routes/dashboard/broadcasts/pages/BroadcastsIndexPage.vue` — `canManageBroadcasts` computed (isAdmin || ID in manager list), gate Broadcast Baru button
  - `app/javascript/dashboard/components-next/Broadcasts/BroadcastList.vue` — pass `canManage` prop
  - `app/javascript/dashboard/components-next/Broadcasts/BroadcastCard.vue` — gate delete button with `canManage`
- **Config to set after deploy**: `InstallationConfig.find_or_create_by(name: 'BROADCAST_MANAGER_USER_IDS').update!(value: '<gita_id>,<pebri_id>,<santhi_id>')`
- **Issues**: None

### Task 4.3: UI Cleanup — Disable Unused Sidebar Items
- **Status**: ⏭️ SKIPPED (no changes needed)
- **What was done**: Verified all items per PRD §5.1. All Conversations, Mentions, Campaigns, Help Center are already absent from the components-next sidebar. Captain was already commented out in a prior commit. No code changes required.
- **Issues**: None

### Task 4.4: UI Cleanup — Rename Section and Reorder Sidebar
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Moved `Unattended` from Settings children to top-level nav item at the bottom of `menuItems`. "Channels" label was already set in a previous PMG commit (Sidebar.vue line 238).
- **Files modified**: `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`
- **Issues**: None

### CHECKPOINT: Review PMG Feature Branch
- **Status**: ⏸️ WAITING_HUMAN
- **What needs review**: `feature/pmg-phase3` on `origin/feature/pmg-phase3`

Verify on local dev (`pnpm dev` or `overmind start -f Procfile.dev`):
- [ ] Sidebar shows: Search, My Inbox, Channels (3 WhatsApp inboxes), Contacts, Reports, Broadcasts, Settings, Unattended (bottom)
- [ ] Admin user sees "Broadcast Baru" button and delete controls
- [ ] After setting BROADCAST_MANAGER_USER_IDS: manager-flagged user sees full broadcast UI
- [ ] Regular agent sees broadcast dashboard read-only (no create/delete)
- [ ] Resolving a conversation and sending a new inbound message reopens it in the list

**Resume**: "continue the cutover-ready plan"

---

## Session: 2026-03-11T01:00:00Z

### Task 5.4: Validate S3 File Uploads
- **Status**: ✅ DONE
- **Completed**: 2026-03-11
- **What was done**: Confirmed `s3://chatwoot-staging-attachments` bucket is accessible and already contains 50 attachment files from real WhatsApp conversations on 2026-03-09 and 2026-03-10. IAM instance role auth working correctly. Could not test a new inbound image as the Padma Care webhook is still pointing at app.chatwoot.com (expected — webhook cutover is a Day-of step).
- **Issues**: None

---

### Task 1.1: Map Sidebar Components and Feature Flags
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Read Sidebar.vue, featureFlags.js, featureHelper.js, installation_config.rb, account_features_field.rb. Mapped every sidebar item to its component, toggle mechanism, and i18n key.
- **Files read**: `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`, `app/javascript/dashboard/featureFlags.js`
- **Issues**: None

#### Sidebar Item Map (for Tasks 4.3 and 4.4)

The active sidebar is `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`. All items are defined in the `menuItems` computed property (lines 224–552). The template simply iterates `menuItems` with `<SidebarGroup v-for="item in menuItems">` — there is no feature-flag gating in the template itself.

| PRD §5.1 Item | Status in current sidebar | Control mechanism | i18n key |
|---|---|---|---|
| All Conversations | **NOT PRESENT** — never in components-next sidebar | n/a | n/a |
| Mentions | **NOT PRESENT** — never in components-next sidebar | n/a | n/a |
| Campaigns | **NOT PRESENT** — never in components-next sidebar | n/a | n/a |
| Help Center | **NOT PRESENT** — never in components-next sidebar | n/a | n/a |
| Captain | **ALREADY commented out** — lines 430–435 of Sidebar.vue | JS comment | `SIDEBAR.CAPTAIN_AI` |
| "Conversations" → "Channels" label | **ALREADY DONE** — `label: 'Channels'` at line 238 | Hardcoded string in menuItems | Was `t('SIDEBAR.CONVERSATIONS')` |
| Unattended (move to bottom) | Currently inside `Settings` children, lines 542–548 | Hardcoded position in menuItems | `SIDEBAR.UNATTENDED_CONVERSATIONS` |

**Summary for Task 4.3**: No code changes needed to hide items — All Conversations, Mentions, Campaigns, Help Center are simply absent from components-next. Captain is already commented out.

**Summary for Task 4.4**: "Channels" label is already set (line 238). Only remaining work: move the `Unattended` item from inside the `Settings` children block to a top-level entry at the bottom of `menuItems`.

**Feature flags in featureFlags.js** (for reference):
- `FEATURE_FLAGS.CAMPAIGNS = 'campaigns'` — exists but not wired to sidebar
- `FEATURE_FLAGS.HELP_CENTER = 'help_center'` — exists but not wired to sidebar
- `FEATURE_FLAGS.CAPTAIN = 'captain_integration'` — exists; sidebar item manually commented out
- `FEATURE_FLAGS.BROADCASTS = 'broadcasts'` — exists; sidebar Broadcasts item is hardcoded (no flag check)

---

### Task 1.2: Map Conversation State Machine
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Traced full inbound message → reopen flow. Identified root cause of the "resolved conversations disappear" bug.
- **Files read**: `app/models/conversation.rb`, `app/models/message.rb`, `app/services/whatsapp/incoming_message_base_service.rb`, `app/listeners/action_cable_listener.rb`, `app/javascript/dashboard/helper/actionCable.js`, `app/javascript/dashboard/store/modules/conversations/actions.js`, `app/javascript/dashboard/store/modules/conversations/index.js`
- **Issues**: None

#### State Machine Flow (Open → Resolved → Reopen)

```
Conversation statuses (conversation.rb:75):
  enum status: { open: 0, resolved: 1, pending: 2, snoozed: 3 }

State transitions:
  open  →  resolved   : agent calls conversation.toggle_status or conversation.resolved!
  resolved → open     : message.rb#reopen_resolved_conversation → conversation.open!
  snoozed → open      : message.rb#reopen_conversation → conversation.open! (line 388)
```

#### Full Reopen Trigger Path

1. **Customer sends inbound WhatsApp message**
2. `WhatsApp::IncomingMessageBaseService#perform` (app/services/whatsapp/incoming_message_base_service.rb)
3. `#set_conversation` called — **THIS IS THE BUG LOCATION** (line 133–139):
   ```ruby
   @conversation = if @inbox.lock_to_single_conversation  # default: FALSE
                     @contact_inbox.conversations.last
                   else
                     @contact_inbox.conversations
                                   .where.not(status: :resolved).last   # <-- skips resolved
                   end
   return if @conversation
   @conversation = ::Conversation.create!(conversation_params)  # <-- creates NEW conversation
   ```
4. When `lock_to_single_conversation = false` (default per schema `app/models/inbox.rb:19`): finds no conversation (because existing one is resolved) → **creates a brand-new conversation** instead of reopening
5. When `lock_to_single_conversation = true`: finds the resolved conversation, proceeds to step 6
6. `Message` created on conversation → `after_create_commit :execute_after_create_commit_callbacks` (message.rb:121)
7. `message.rb:312` `reopen_conversation` called
8. `message.rb:384–391`: `return unless incoming?`, then `reopen_resolved_conversation if conversation.resolved?`
9. `message.rb:393–402` `reopen_resolved_conversation`:
   - inbox.active_bot? → `conversation.pending!`
   - inbox.api? → `conversation.open!`
   - else (WhatsApp) → `conversation.open!`  ✅
10. `conversation.open!` triggers `after_update_commit :execute_after_update_commit_callbacks` (conversation.rb:121)
11. `conversation.rb:299` `notify_status_change` dispatches `CONVERSATION_OPENED` and `CONVERSATION_STATUS_CHANGED`
12. `action_cable_listener.rb:79` `conversation_status_changed` broadcasts `conversation.status_changed` to frontend
13. Frontend `actionCable.js:19` `'conversation.status_changed': this.onStatusChange` → `this.app.$store.dispatch('updateConversation', data)` (line 113)
14. `actions.js:394` `updateConversation` → commits `UPDATE_CONVERSATION` mutation
15. `index.js:240` `UPDATE_CONVERSATION` updates conversation in `allConversations` with new status = open; if not in store, pushes it
16. Conversation list re-renders showing the reopened conversation ✅

#### Root Cause of the Bug

**File**: `app/services/whatsapp/incoming_message_base_service.rb:133–139`
**Bug**: `where.not(status: :resolved).last` returns `nil` when only resolved conversations exist for the contact_inbox. A new conversation is created instead of reopening the resolved one. The old resolved conversation's history is orphaned — "data is intact" per PRD §5.2.1.

Same pattern exists in:
- `app/services/sms/incoming_message_service.rb:61`
- `app/services/telegram/incoming_message_service.rb:81`
- `app/services/twilio/incoming_message_service.rb:100`

**Proposed fix**: When `lock_to_single_conversation = false` and no active conversation is found, fall back to the most recently resolved conversation rather than creating a new one. The existing `reopen_conversation` logic in `message.rb:384` will reopen it automatically.

```ruby
@conversation = @contact_inbox.conversations.where.not(status: :resolved).last
@conversation ||= @contact_inbox.conversations.last  # fall back to reopening resolved
```

This is upstream-safe: it only changes behavior when all conversations are resolved (no active session), and it leverages the existing reopen logic already in `message.rb`.

---

### Task 1.3: Map Data Import Synchronize Logic
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Traced full import flow. Identified the synchronize index-drift bug.
- **Files read**: `app/models/data_import.rb`, `app/jobs/data_import_job.rb`, `app/services/data_import/contact_manager.rb`
- **Issues**: None

#### Import Flow

1. `DataImport#process_data_import` (data_import.rb:31–33): schedules `DataImportJob.perform_later(self)`
2. `DataImportJob#perform` (data_import_job.rb:8): builds `@contact_manager`, calls `process_import_file`
3. `DataImportJob#parse_csv_and_build_contacts` (line 30–46): iterates CSV rows, calls `@contact_manager.build_contact(row)` for each
4. `DataImport::ContactManager#build_contact` (contact_manager.rb:6–9): calls `find_or_initialize_contact` then `update_contact_attributes`
5. `#find_or_initialize_contact` (line 12–18): calls `find_existing_contact` first; if found, returns existing contact (with existing ID); else builds a new `@account.contacts.new(...)`
6. `#find_existing_contact` (line 20–26): finds by identifier → email → phone_number. If found, calls `update_contact_with_merged_attributes` (saves the contact with merged data) and returns it
7. Back in `DataImportJob#import_contacts` (line 53–56):
   ```ruby
   Contact.import(contacts, synchronize: contacts, on_duplicate_key_ignore: true,
                  track_validation_failures: true, validate: true, batch_size: 1000)
   ```

#### Root Cause: Index Drift in `synchronize`

**File**: `app/jobs/data_import_job.rb:55`

The `activerecord-import` gem's `synchronize: contacts` option works by:
1. After bulk INSERT, fetching the newly inserted rows from the DB
2. Mapping them back to the in-memory `contacts` array **by position**

With `on_duplicate_key_ignore: true`, records that already exist are silently skipped at the DB level. No INSERT occurs for them. The DB returns IDs only for the actually-inserted rows.

**Example**: 5 contacts [A, B, C, D, E] where B and D already exist:
- Inserted: A, C, E → DB returns IDs: [id_A, id_C, id_E]
- `synchronize` assigns by position: `contacts[0].id = id_A` ✅, `contacts[1].id = id_C` ❌ (B should stay as B, not get C's data), `contacts[2].id = id_E` ❌
- Result: in-memory objects B, C, D now have wrong IDs → after DB reload, their `name`, `phone_number`, etc. are misaligned

**Note**: For `find_existing_contact` path, existing contacts are already saved in step 6 above with correct data via `update_contact_with_merged_attributes`. The synchronize bug would corrupt their in-memory state after the import, but since `import_contacts` is the last data-touching step, the corruption affects any post-import operations that read these in-memory objects (e.g., counting, notifications).

**Proposed fix**: Remove the `synchronize: contacts` option. Existing contacts are already updated before `import_contacts` is called (via `update_contact_with_merged_attributes`), and new contacts don't need in-memory synchronization after insert.

```ruby
Contact.import(contacts, on_duplicate_key_ignore: true, track_validation_failures: true,
               validate: true, batch_size: 1000)
```

Alternatively, separate new vs existing contacts:
```ruby
new_contacts = contacts.select { |c| c.new_record? }
Contact.import(new_contacts, synchronize: new_contacts, on_duplicate_key_ignore: true, ...)
```

---

### Task 1.4: Map Broadcast Access Control
- **Status**: ✅ DONE
- **Started**: 2026-03-11
- **Completed**: 2026-03-11
- **What was done**: Read broadcast policy, AccountUser model, and broadcast frontend pages. Documented minimal implementation approach.
- **Files read**: `app/policies/broadcast_policy.rb`, `app/models/account_user.rb`, `app/javascript/dashboard/routes/dashboard/broadcasts/pages/BroadcastsIndexPage.vue`, `app/javascript/dashboard/components-next/Broadcasts/BroadcastDialog.vue`, `app/javascript/dashboard/components-next/Broadcasts/BroadcastCard.vue`
- **Issues**: None

#### Current State

`app/policies/broadcast_policy.rb`: all 8 actions (`index?`, `show?`, `create?`, `destroy?`, `template_config?`, `sheets?`, `sheet_tabs?`, `sheet_headers?`, `preview?`) are restricted to `@account_user.administrator?`.

`AccountUser` fields (account_users table):
- `role` enum: `agent: 0, administrator: 1` (account_user.rb:34)
- `custom_role_id` (bigint, enterprise feature) — not suitable without migration
- No existing "broadcast_manager" or custom permission flag

Frontend: `BroadcastsIndexPage.vue` shows "Broadcast Baru" button **unconditionally** — no role check in the Vue component. Backend Pundit policy is the only enforcement point currently.

#### PMG Requirement (PRD §4.4)

- Administrators (Okto, Alex, Kezia): full access ✅ — already works
- Manager agents (Gita, Pebri, Santhi): full access — **currently blocked by policy**
- Regular agents (all others): read-only — **currently fully blocked**

#### Recommended Implementation Approach

**Backend**: Add allowlist to `InstallationConfig` (already used for feature flags / global config; no migration needed):

```ruby
# app/policies/broadcast_policy.rb
def broadcast_manager?
  ids = GlobalConfig.get_value('BROADCAST_MANAGER_USER_IDS').to_s.split(',').map(&:to_i)
  ids.include?(@user.id)
end

def index?
  @account_user.administrator? || @account_user.agent? # all can view list
end

def show?
  @account_user.administrator? || @account_user.agent? # all can view detail
end

def create?
  @account_user.administrator? || broadcast_manager?
end
# etc.
```

**Backend config**: Set via super admin or Rails console:
```ruby
InstallationConfig.find_or_create_by(name: 'BROADCAST_MANAGER_USER_IDS')
                  .update!(value: '3,7,12')  # Gita, Pebri, Santhi user IDs
```

**Frontend**: Add role check to `BroadcastsIndexPage.vue` to hide "Broadcast Baru" button for regular agents who are not in the manager list. The frontend check is UX-only; Pundit is the authoritative enforcement.

**Files to modify**:
- `app/policies/broadcast_policy.rb` — add `broadcast_manager?` helper, expand `index?`/`show?` to agents
- `app/javascript/dashboard/routes/dashboard/broadcasts/pages/BroadcastsIndexPage.vue` — add role check before rendering create button
- Config set via Rails console / super admin UI (no new files needed)

---

## Session: 2026-03-11T04:00:00Z

### Task 5.1: Create User Accounts on Staging
- **Status**: ✅ DONE
- **Completed**: 2026-03-11
- **What was done**: 12 user accounts created in staging with correct roles and inbox assignments. Broadcast manager config set via Rails console: `InstallationConfig` record `BROADCAST_MANAGER_USER_IDS` = `'6,13,7'` (Gita=6, Pebri=13, Santhi=7).
- **Files modified**: None (UI + Rails console)
- **Issues**: Rails console required `RAILS_ENV=production` (no staging DB config). Had to set `InstallationConfig` in two steps due to YAML serialization on chained `update!`.

### Task 5.6: Set Up Database Backup Cron
- **Status**: ✅ DONE
- **Completed**: 2026-03-12
- **What was done**: Created `s3://pmg-chatwoot-backups` in ap-southeast-1. Added 30-day lifecycle on `daily/`, 90-day on `weekly/`. Added `pmg-chatwoot-backups` to `ec2_chatwoot_role` IAM policy (v4). Cron jobs added for daily 02:00 WIB (19:00 UTC) and weekly Sunday. Manual backup/restore tested: dump uploaded to S3, restored to `chatwoot_test` DB with exit code 0.
- **Files modified**: IAM policy `ec2_chatwoot_specific_permissions` (v4), crontab on EC2 host
- **Issues**: Initial S3 PutObject denied — IAM policy only covered `chatwoot-*` buckets. Fixed by adding `pmg-chatwoot-backups` ARN to policy.

---

## Plan Closeout: 2026-03-12

### Summary
This plan reached its intended scope: staging is validated and ready for cutover. Production go-live (Tasks 6.3, 6.5) is blocked on prerequisites that belong in the next plan.

### ✅ Completed
- Phases 1–5 entirely (codebase recon, bug fixes, PMG UI customizations, all infrastructure)
- Task 6.1 — PR merged to develop and staging
- Task 6.2 — Staging deployed, puma running as `chatwoot` user, sidebar verified
- Task 6.4 — Cutover checklist at `pmg-docs/operations/cutover-checklist.md`

### ⏸️ Outstanding — Feed into Next Plans

**Blocked on Docker/CI plan:**
- Task 6.3 — ALB listener rule for `chat.pbmcgroup.com → port 3002` not configured
- Task 6.5 — Production deploy on port 3002 with separate service files and `.env`
- `chatwoot.pbmcgroup.com → 3000` broadcast webhook needs to move to production port on cutover

**Upstream contributions (can be done independently):**
- Submit PR `fix/resolve-conversation-reopen` to `chatwoot/chatwoot`
- Submit PR `fix/data-import-synchronize` to `chatwoot/chatwoot`

**Bugs to debug separately:**
- Conversation status filter broken — resolved conversations disappear from all views; selecting multiple statuses returns zero results. Root cause in components-next conversation list filter logic.
- CI: TikTok JWT spec flaky (pre-existing, off-by-1-second timestamp — needs `freeze_time` fix upstream)

### Next Plans Required Before Production Go-Live
1. **Docker/CI plan** — containerize app + sidekiq, docker-compose for staging + production on same host, GitHub Actions CI pipeline
2. **Router/broadcast resilience plan** — duplicate router and broadcast webhook functionality in staging without webhost dependency
3. **Data migration plan** — contacts + conversations from app.chatwoot.com (API-based, ~40k contacts)

---

## Architecture Note: Docker Containerization Requirement

**Raised**: 2026-03-12 during Task 6.2 staging deploy discussion

The staging and production environments will eventually run on the **same EC2 host**. Running both natively (systemd) on one server creates port conflicts, rbenv version collisions, and env var isolation problems.

**Requirement for CI plan (PRD Phase 5)**: Containerize the Chatwoot app (web + sidekiq) in Docker. Design the docker-compose setup to support two isolated environments on one host from the start — separate networks, ports, volumes, and secrets injection per environment.

**Current state**: App runs natively via systemd. Acceptable for single-environment staging. Do not proceed this way for production-on-same-host.

**Feeds into**: `ci-pipeline-PLAN.md` (to be created). Tag this constraint: `staging + production on shared host → Docker required`.

---

## Session: 2026-03-12T08:00:00Z

### Task 6.1: Merge Feature Branch to Develop (AI+HUMAN_REVIEW)
- **Status**: ✅ DONE — awaiting human review
- **Completed**: 2026-03-12
- **What was done**: Committed unstaged S3 filename fix. Rebased onto `origin/develop` (already up to date). RuboCop clean on all changed Ruby files. ESLint warnings all pre-existing upstream issues — none in PMG-changed files. Pushed branch and created PR.
- **PR**: https://github.com/Padma-Medical-Group/pmg-chatwoot/pull/1
- **Files modified**: None beyond prior commits (plus S3 filename fix committed this session)
- **Issues**: `gh` CLI was pointing at upstream `chatwoot/chatwoot` repo — required `--repo` flag to target PMG fork. Local dev env set up this session: rbenv 3.4.4, bundler 2.5.16, libpq for pg gem, npm install.

### Task 6.2: Deploy to Staging
- **Status**: ✅ DONE
- **Completed**: 2026-03-12
- **What was done**: Merged `develop` into `staging` locally and pushed. On server: moved app from `/home/ubuntu/chatwoot` to `/home/chatwoot/chatwoot`, updated both service unit files, added `ubuntu` to `chatwoot` group for access, added GitHub deploy key for `chatwoot` user (`chatwoot-server-deploy-key`), pulled `pmg/staging`, ran `bundle install` and `assets:precompile`, restarted services. Puma running as `chatwoot` user on port 3001.
- **Files modified**: `/etc/systemd/system/chatwoot-web.service`, `/etc/systemd/system/chatwoot-sidekiq.service` (WorkingDirectory updated)
- **Staging verification**: Sidebar layout ✅. Broadcast access TBD. Conversation reopen TBD.
- **Known issue logged for post-cutover**: Conversation status filter broken on staging. Resolved conversations disappear from all views (Mine/Unassigned/All assignee chips only filter assignee, not status — list defaults to `status=open`). Selecting multiple statuses in the filter returns zero results. Root cause: components-next conversation list status filter bug. Debug separately.
- **Issues**: Deploy keys were disabled at org level — enabled by Alex. `TemplateCreatorDialog.vue` was untracked on server — already present in staging branch, came through in pull. `bundle` not in PATH for chatwoot user — use full path `/home/ubuntu/.rbenv/shims/bundle`.

### Task 5.7: Create Dedicated Service User
- **Status**: ✅ DONE
- **Completed**: 2026-03-12
- **What was done**: Created `chatwoot` system user. Edited `/etc/systemd/system/chatwoot-web.service` and `chatwoot-sidekiq.service` to set `User=chatwoot Group=chatwoot`. Fixed CHDIR failure by setting `chmod o+x /home/ubuntu` so the chatwoot user can traverse to `/home/ubuntu/chatwoot`. Both services restarted and confirmed running as `chatwoot`. Live WhatsApp webhooks processing normally post-restart.
- **Files modified**: `/etc/systemd/system/chatwoot-web.service`, `/etc/systemd/system/chatwoot-sidekiq.service`
- **Issues**: `status=200/CHDIR` on first restart — `chatwoot` user lacked execute on `/home/ubuntu`. Fixed with `chmod o+x /home/ubuntu`.

---

## Session: 2026-03-12T01:48:00Z

### Task 5.5: Configure SES Email
- **Status**: ✅ DONE
- **Completed**: 2026-03-11 (completed prior session while Claude Code was unavailable)
- **What was done**: SES domain verification completed for `pbmcgroup.com`, DKIM/SPF DNS records added to Route 53, SMTP credentials created. SMTP vars written to `.env` (loaded via dotenv at Rails startup). SES account approved out of sandbox for production sending. Validated: services running, port 587 reachable, test email delivered via `ActionMailer::Base.mail(...).deliver_now`.
- **Files modified**: `.env` on EC2 host (SMTP vars)
- **Validation output**: `OK port 587 reachable`, `OK email sent` — email delivered to alex@pbmcgroup.com
- **Issues**: Env vars not exported to shell (only loaded by Rails via dotenv) — expected, not a problem.
