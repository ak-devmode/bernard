# Progress Log: Chatwoot Go-Live Plan — chat.pbmcgroup.com

## Session: 2026-03-13T00:00:00+08:00

### Phase 0: Pre-flight
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **Related docs verified**:
  - ✅ `pmg-docs/development/prds/chatwoot-platform-PRD-v5.md`
- **Plan status**: "In Progress" — valid, proceeding
- **Git**: `pmg-chatwoot/` repo on branch `staging`. `pmg` root is not a git repo. Plan has no `**Branch:**` field — @Dev code tasks (docker-compose.yml, systemd files, etc.) must be committed to pmg-chatwoot on a branch confirmed by Alex before first commit.
- **Issues**: No branch specified in plan. Flagged for human confirmation before first @Dev commit.

---

### Task 2.1.1: Create Docker bridge network
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Created `pmg_net` Docker bridge network on EC2. Attached existing `chatwoot_redis` and `chatwoot_postgres` containers to it.
- **Files modified**: None (EC2 Docker state)
- **Issues**: None. Network created, both containers connected cleanly.

---

### Task 3.1.2: Identify failing filter logic
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Traced the full filter code path. Root cause: `conversationFilters.status` always used a single `activeStatus` ref (defaulting to `'open'`) for all three tabs (Mine, Unassigned, All). When status is `'open'`, the backend only returns open conversations, so resolved ones are never in the store. Switching to the All tab doesn't help because it still fetches with `status=open`. Secondary issue: `filterByStatus()` only handled string comparison, failing silently if an array was passed.
- **Files read**: `ChatList.vue`, `ChatListHeader.vue`, `ConversationBasicFilter.vue`, `helpers.js`, `getters.js`, `filterHelpers.js`, `filterQueryGenerator.js`, `conversation_finder.rb`
- **Issues**: None. Backend already handles `status=all` correctly (skips status filter entirely).

---

### Task 3.1.3: Fix status filter
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Two changes committed to `develop` (commit `d57a13efb`):
  1. `ChatList.vue` — `conversationFilters` computed now forces `status: 'all'` when on the All tab. Mine/Unassigned keep user-controlled status (default `open`). Added `effectiveStatus` computed passed to ChatListHeader so the badge correctly reads "All" when on All tab.
  2. `helpers.js` — `filterByStatus` now handles array values: returns true if array includes 'all' or includes the chat's status.
- **Behavior after fix**: All tab shows all conversations including resolved; resolved conversations move out of Mine (open-only) but remain visible in All. Multi-status array values handled correctly client-side.
- **Files modified**: `app/javascript/dashboard/components/ChatList.vue`, `app/javascript/dashboard/store/modules/conversations/helpers.js`
- **Issues**: None. ESLint clean.

---

### Task 3.1.4: Sidebar navigation restructure
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Restructured sidebar nav across two sessions (commits on `develop`):
  1. Renamed "Conversation" group label to "Conversations"
  2. Moved Mentions, Unassigned (formerly Unattended), and Pending inside the Conversations group as children — same level as Folders/Teams/Channels/Labels
  3. Added Pending as a new nav item (routes to `conversation_pending` / `conversation_through_pending`) using `defaultStatus: 'pending'` prop
  4. Renamed Unattended → Unassigned in nav label (routes unchanged to `conversation_unattended`)
  5. Captain remains commented out; Campaigns not present; Broadcasts retained
  6. Added two new routes for Pending in `conversation.routes.js`
- **Files modified**: `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`, `app/javascript/dashboard/routes/dashboard/conversation/conversation.routes.js`
- **Issues**: None. Confirmed visually in local dev.

---

### Task 3.2.5 + 3.2.6: CloudWatch alarms + SNS
- **Status**: ✅ DONE (partial — disk alarm deferred)
- **Completed**: 2026-03-13
- **What was done**: SNS topic `PBMC-CloudWatch-Alarm` already existed with `it-alerts@pbmcgroup.com` subscribed. Created 3 of 4 alarms via AWS CLI from local machine (EC2 role lacks CloudWatch/SNS permissions):
  1. `chatwoot-high-cpu` — CPUUtilization >80% for 5 min
  2. `chatwoot-instance-status` — StatusCheckFailed ≥1 for 2 consecutive minutes
  3. `chatwoot-sidekiq-queue-depth` — custom metric `PMG/Chatwoot:sidekiq_queue_size` >500 (alarm created; metric publishing requires Sidekiq instrumentation)
- **Deferred**: `chatwoot-disk-full` — CWAgent on chatwoot instance is not publishing disk metrics (only logs). Will add after task 3.2.4 updates the agent config post-Docker.
- **Files modified**: `/Users/alexknecht/create-chatwoot-alarms.sh` (local helper, not committed)
- **Issues**: None.

---

### Task 3.3: Integration User
- **Status**: ✅ DONE (staging only — app.chatwoot.com skipped)
- **Completed**: 2026-03-13
- **What was done**: Created integration user on staging Chatwoot. Stored API token in Secrets Manager at `chatwoot/staging/integration_api_token` (ap-southeast-1). app.chatwoot.com integration user skipped — legacy instance, would cost an additional seat, migrating away from it.
- **Files modified**: None
- **Issues**: None.

---

### Task 2.1.2: Write docker-compose.pmg.yml
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Created `docker-compose.pmg.yml` in repo root with `staging` (port 3001) and `production` (port 3002) profiles. Each profile has a web and sidekiq service using profile-specific images and env files. Both profiles use `pmg_net` (external). No DB services — Redis and Postgres are pre-existing on the network. Named `docker-compose.pmg.yml` (not `docker-compose.yml`) to avoid collision with upstream compose files.
- **Files modified**: `pmg-chatwoot/docker-compose.pmg.yml` (new)
- **Issues**: None. Committed to `develop` branch.

---

## Session: 2026-03-13 (continued)

### Task 3.5.4 + 3.5.6: chatwoot-services in repo + systemd units
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Moved `chatwoot-services/` (router + broadcast) into `pmg-chatwoot` repo. Added `chatwoot-services.target` systemd unit for grouped service management. Added `pmg-router.service` unit (`PartOf=chatwoot-services.target`). Added `deploy.sh` script for EC2 deployment. Broadcast service is job-based (not a daemon) so no broadcast service unit needed.
- **Files modified**: `chatwoot-services/` (new directory tree), `chatwoot-services/chatwoot-services.target`, `chatwoot-services/router/pmg-router.service`, `chatwoot-services/deploy.sh`
- **Issues**: None. Committed and pushed to staging.

---

### fetch-secrets.sh
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Created `fetch-secrets.sh` at repo root. Reads from SSM `/pmg/chatwoot`, writes `.env.staging` or `.env.production`. Sets `FRONTEND_URL` per profile. DB name hardcoded as `chatwoot_production` for both profiles at time of creation (pending update once DB rename done).
- **Files modified**: `fetch-secrets.sh` (new)
- **Issues**: None.

---

### Code preservation: Okto's staging changes
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Identified 10 commits by Okto on staging that were not in develop or repo. Merged `1a75af249` back into staging branch. Resolved merge conflicts in `broadcast_from_sheet_service.rb` — kept Okto's code (META_ERROR_MESSAGES, sync_contact, improved send_to with message_id check, nil-safe failed_recipients) and added rubocop:disable comments. Also recovered `message_finder.rb` fix (created_at cursor for messages_before) from live instance, committed to staging (PR #5) and develop.
- **Files modified**: `app/services/whatsapp/broadcast_from_sheet_service.rb`, `app/finders/message_finder.rb`
- **Issues**: Force push to staging had previously overwritten Okto's commits — fully recovered.

---

### Task 2.1.3 + 2.1.4: Build Docker images + validate env
- **Status**: ✅ DONE (image built; full no-cache rebuild in progress as of session end)
- **Completed**: 2026-03-13
- **What was done**: Docker image `pmg-chatwoot:staging` built on EC2. Later discovered the cached build did not include nav changes (sidebar restructure). Triggered `--no-cache` rebuild via `docker build --no-cache ... > /tmp/docker-build.log 2>&1 &`. Rebuild running at session end — expect 20-30 min. Generated `.env.staging` on EC2 with correct Docker networking (`POSTGRES_HOST=chatwoot_postgres`, `REDIS_URL=redis://chatwoot_redis:6379`, `POSTGRES_DATABASE=chatwoot_staging`).
- **Files modified**: `.env.staging` on EC2 (not in repo — generated from SSM)
- **Issues**: Initial cached build silently missed nav changes. Resolved with --no-cache.

---

### Task 2.1.5: Stop native services + start Docker staging stack
- **Status**: ✅ DONE
- **Completed**: 2026-03-13
- **What was done**: Stopped `chatwoot-web.service` and `chatwoot-sidekiq.service` (native systemd). Renamed `chatwoot_production` DB → `chatwoot_staging` (inside Docker postgres container). Created fresh empty `chatwoot_production`. Started `docker compose -f docker-compose.pmg.yml --profile staging up -d`. Containers `chatwoot-web-staging` (port 3001) and `chatwoot-sidekiq-staging` are running and processing live WhatsApp webhooks. Reset alex@pbmcgroup.com password to `Changeme2024!`.
- **Files modified**: EC2 Docker state, `.env` on EC2 (POSTGRES_DATABASE updated to chatwoot_staging)
- **Issues**: Image is stale (missing nav changes) — no-cache rebuild in progress.

---

---

## Session: 2026-03-14

### Docker image rebuild + staging cutover
- **Status**: ✅ DONE
- **Completed**: 2026-03-14
- **What was done**:
  - Fixed `assets:precompile` failure caused by `sass-embedded@1.98` injecting `@use "sass:meta"` into Vue SFC style blocks. Fix: aliased `sass-embedded` → `sass@1.79.3` via `pnpm add -D sass-embedded@npm:sass@1.79.3`. Committed as `cafae8c8f` on staging.
  - Freed 17GB of Docker build cache + old images to resolve "no space left on device" error during image export.
  - Successfully built `pmg-chatwoot:staging` (SHA `fcfd8c6b`) with all code changes.
  - Diagnosed Captain and Campaigns still visible in nav — merge conflict resolution in `1290216e7` had accidentally retained upstream nav items alongside our changes.
  - Fixed: commented out Captain (lines 324–394) and Campaigns (lines 450–471) in `Sidebar.vue`. Committed as `73947b28f`, pushed to staging.
  - Disabled and stopped native `chatwoot-web.service` and `chatwoot-sidekiq.service` (were auto-restarting and holding port 3001).
  - Rebuilt image with nav fix, restarted Docker staging stack. Nav verified correct: Pending visible, Captain and Campaigns hidden.
- **Files modified**: `package.json`, `pnpm-lock.yaml`, `app/javascript/dashboard/components-next/sidebar/Sidebar.vue`
- **Issues**: Multiple disk space and port-conflict blockers resolved. Native systemd services now permanently disabled.

### Pending next session
- [ ] nginx / reverse proxy: find what's routing traffic to the instance and update to port 3001 (no nginx found on instance — may be ALB or other)
- [ ] chatwoot-services deploy: run `chatwoot-services/deploy.sh` on EC2
### Tasks 3.2.4 + disk alarm: CloudWatch Docker logging + disk alarm
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**:
  - Switched all 4 Docker containers to `awslogs` logging driver — logs ship directly to CloudWatch without CWAgent file tailing
  - Log groups: `/aws/chatwoot/staging/web`, `/aws/chatwoot/staging/sidekiq`, `/aws/chatwoot/production/web`, `/aws/chatwoot/production/sidekiq` (auto-created on first container start)
  - Created `chatwoot-disk-full` CloudWatch alarm: `DISK_USED >= 85%` for 2 consecutive periods → SNS `PBMC-CloudWatch-Alarm` (disk metrics already publishing from CWAgent)
- **Files modified**: `docker-compose.pmg.yml`
- **Issues**: `docker logs` command no longer works locally — use CloudWatch console or `aws logs` CLI instead.

### Task 3.3.4: Integration user on production
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**: Stored production integration user API token in SSM at `/pmg/chatwoot/production/integration_api_token` (SecureString). User is `integrations@pbmcgroup.com` (SuperAdmin). Token should be rotated post-go-live.
- **Files modified**: None

---

### Tasks 3.5.5–3.5.10: Router + broadcast deployed to EC2
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**:
  - Deployed `chatwoot-services/` to EC2 via `deploy.sh` — router + broadcast at `/var/www/chatwoot-services/`
  - Fixed broadcast config files gitignored by overly broad `*.json` rule — updated `.gitignore` to only exclude actual secrets/output files; `phone_numbers.json`, `sheets.json`, `conditional_modes.json` now tracked in git
  - `pmg-router.service` enabled and running on port 3000
  - DNS `whatsapp.pbmcgroup.com` → ALB → EC2:3000 created (cleaner name than `chatwoot.pbmcgroup.com`; Meta webhook will permanently point here post-cutover)
  - Meta webhook temporarily updated to `https://whatsapp.pbmcgroup.com/webhook` for testing — verified working
  - Updated router to triple-deliver: `app.chatwoot.com` (cloud legacy) + `staging-chat.pbmcgroup.com` + `chat.pbmcgroup.com` (production)
  - End-to-end confirmed: real WhatsApp message received and forwarded to all three instances ✅
- **Files modified**: `chatwoot-services/router/router.js`, `chatwoot-services/broadcast/.gitignore`, `chatwoot-services/broadcast/config/*.json`
- **Next**: Revert Meta webhook back to `chatwoot.pbmcgroup.com` (webhost) when done testing, flip permanently to `whatsapp.pbmcgroup.com` at cutover

---

### Tasks 2.2.1–2.2.5 + 2.3.1–2.3.3: Production stack + ALB
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**:
  - Fixed `fetch-secrets.sh` docker networking (POSTGRES_HOST/REDIS_URL were pulling 127.0.0.1 from SSM — hardcoded container names instead, no duplicates)
  - Started production Docker stack (port 3002): `chatwoot-web-production` + `chatwoot-sidekiq-production`
  - UFW port 3002 opened
  - Fixed migration `20231211010807_add_cached_labels_list.rb` — `ActsAsTaggableOn::Taggable::Cache` NameError resolved by editing file inside container (permanent fix committed to staging branch)
  - Restored staging config (without conversations/messages/attachments/notifications/reporting_events/conversation_participants/mentions/csat_survey_responses) to `chatwoot_production` DB — users, inboxes, contacts, teams all present
  - Tagged `pmg-chatwoot:staging` → `pmg-chatwoot:production` to apply nav/sass fixes; force-recreated containers
  - ALB target group (port 3002) + listener rule for `chat.pbmcgroup.com` already configured by Alex
  - `https://chat.pbmcgroup.com` returns Chatwoot login with correct nav ✅
- **Files modified**: `fetch-secrets.sh` (docker networking fix)
- **Issues**: `pmg-chatwoot:production` image was stale — resolved by tagging from staging image. Production image rebuild deferred (will happen when production branch is built properly).

---

## Session: 2026-03-15

### Task 2.1.4: Fix fetch-secrets.sh DB names
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**: Fixed two bugs in `fetch-secrets.sh`: (1) variable name was `POSTGRES_DB` — Chatwoot expects `POSTGRES_DATABASE`; (2) staging profile was writing `chatwoot_production` instead of `chatwoot_staging`. Production profile correctly writes `chatwoot_production`. DB rename was already done on EC2 (Task 2.1.5, 13 March session).
- **Files modified**: `fetch-secrets.sh`
- **Issues**: None.

---

### Task 2.1.6: Systemd Docker auto-start units
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**: Created two systemd unit files for Docker stack boot management. Both use `Type=oneshot RemainAfterExit=yes` so systemd tracks the stack as a unit. `ExecStop` runs `docker compose down` cleanly. Run as `chatwoot` user in `docker` group.
- **Files modified**: `deployment/chatwoot-staging-docker.service` (new), `deployment/chatwoot-production-docker.service` (new)
- **Install steps (on EC2)**:
  ```bash
  sudo cp deployment/chatwoot-staging-docker.service /etc/systemd/system/
  sudo cp deployment/chatwoot-production-docker.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable chatwoot-staging-docker   # staging only until production is ready
  ```
  Prerequisites: `sudo usermod -aG docker chatwoot` (verify chatwoot user is in docker group first).
- **Issues**: None.

---

### Task 2.1.7: Rewrite DEPLOYMENT.md
- **Status**: ✅ DONE
- **Completed**: 2026-03-15
- **What was done**: Full rewrite. Previous version referenced native systemd services, old paths (`/home/ubuntu/chatwoot`), old branch names (`custom-production`), and pre-ALB network setup. New version documents: Docker profile-based deployment, fetch-secrets.sh usage, EC2 commands for logs/console/migrations, systemd unit install steps, router service, branch strategy, and upstream upgrade notes.
- **Files modified**: `DEPLOYMENT.md`
- **Issues**: None.
