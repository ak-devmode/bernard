# Manual Test Checklist — Pre-Production Push

**Branch:** `feature/broadcast-refactor` → `develop` → `main`
**Date:** Monday 2026-03-24
**Environment:** Staging (chat-staging.pbmcgroup.com)
**Tester(s):** _______________

---

## Pre-Test Setup

- [ ] Deploy `feature/broadcast-refactor` to staging
- [ ] Verify router is running: `curl https://<staging-host>:3000/health` returns `{"status":"ok"}`
- [ ] Verify SSM parameters exist: `/pmg/router/webhook_routes`, `/pmg/router/direct_chat_token`, `/pmg/chatwoot/api_access_token`
- [ ] Note the current time for log checking later

---

## 1. Sidebar Navigation

**What changed:** Restructured sidebar — Pending queue added, Mentions/Unassigned moved under Conversations group, Captain/Campaigns hidden via feature flags, Broadcasts nav item added.

- [ ] 1.1 Login to Chatwoot as **admin**
- [ ] 1.2 Verify "Conversations" group contains: Mine, Unassigned, Pending, Mentions
- [ ] 1.3 Click "Pending" — verify it shows conversations with pending status
- [ ] 1.4 Verify "Captain" is NOT visible in sidebar (feature flag disabled)
- [ ] 1.5 Verify "Campaigns" is NOT visible in sidebar (feature flag disabled)
- [ ] 1.6 Verify "Broadcasts" is visible in sidebar (admin only)
- [ ] 1.7 Login as **agent** — verify "Broadcasts" is NOT visible (unless agent is in BROADCAST_MANAGER_USER_IDS)

---

## 2. Conversation Status Filter (All Tab)

**What changed:** All tab now shows resolved conversations. Previously only showed open.

- [ ] 2.1 Create a test conversation and resolve it
- [ ] 2.2 Switch to the "All" tab
- [ ] 2.3 Verify the resolved conversation appears in the list
- [ ] 2.4 Switch to "Mine" tab — verify resolved conversation does NOT appear
- [ ] 2.5 Switch back to "All" — verify open, pending, and resolved conversations all visible

---

## 3. Broadcast Feature (Google Sheets Flow)

**What changed:** Refactored controller (extracted template concern), preserved failed messages instead of destroying, English translations, delivery failure tracking.

- [ ] 3.1 Navigate to Broadcasts in sidebar
- [ ] 3.2 Create a new broadcast:
  - Select a WhatsApp inbox
  - Select a Google Sheet + tab
  - Select a template
  - Preview recipients
  - Send
- [ ] 3.3 Verify broadcast appears in list with status progression: draft → processing → completed/failed
- [ ] 3.4 Click into broadcast detail — verify recipient counts (sent/failed) are correct
- [ ] 3.5 If any recipients failed, verify failure details are preserved (not destroyed)
- [ ] 3.6 Verify broadcast messages appear in the recipient's conversation history
- [ ] 3.7 Test "Copy as New" — creates a new broadcast from an existing one
- [ ] 3.8 Test delete — confirmation dialog appears, broadcast is removed

---

## 4. Direct Chat API (Kyoo Integration) — NEW

**What changed:** New endpoint for programmatic WhatsApp template sends via the router.

- [ ] 4.1 **Auth — valid token:** Send POST to router with correct API token
  ```bash
  curl -X POST https://<staging-host>:3000/api/v1/sendTemplateMessages \
    -H "Authorization: <direct_chat_token>" \
    -H "Content-Type: application/json" \
    -d '{
      "template_name": "kyoo_appt_qr_in",
      "broadcast_name": "Test Direct Send",
      "receivers": [{
        "whatsappNumber": "<test_phone>",
        "customParams": [
          {"name": "patient_name", "value": "Test Patient"},
          {"name": "qr_code", "value": "https://example.com/qr"}
        ]
      }]
    }'
  ```
  - [ ] Verify response: `{"success": true, "broadcastId": "...", "recipientCount": 1}`
  - [ ] Verify WhatsApp message received on test phone
  - [ ] Verify Broadcast record created in Chatwoot (visible in Broadcasts list)
  - [ ] Verify contact created/updated in Chatwoot contacts

- [ ] 4.2 **Auth — invalid token:** Same request with wrong Authorization header
  - [ ] Verify response: `401 {"success": false, "error": "AUTH_INVALID"}`

- [ ] 4.3 **Validation — missing receivers:**
  ```bash
  curl -X POST https://<staging-host>:3000/api/v1/sendTemplateMessages \
    -H "Authorization: <direct_chat_token>" \
    -H "Content-Type: application/json" \
    -d '{"template_name": "test"}'
  ```
  - [ ] Verify response: `400 {"success": false, "error": "VALIDATION_ERROR: ..."}`

- [ ] 4.4 **Error handling:** Send with an invalid template name
  - [ ] Verify response includes error details
  - [ ] Check S3 DLQ bucket (`pmg-webhook-dlq/direct_chat/`) for failed payload
  - [ ] Check SES alert email received

---

## 5. Webhook Routing

**What changed:** Router rewritten — loads routes from SSM, removed broadcast/ imports, added DLQ on forward failure, WABA override check on startup.

- [ ] 5.1 Send a test WhatsApp message to **Padma Care** number (+6282266323030)
  - [ ] Verify message appears in Chatwoot Padma Care inbox
- [ ] 5.2 Send a test WhatsApp message to **Crew Care** number (+6282131096676)
  - [ ] Verify message appears in Chatwoot Crew Care inbox
- [ ] 5.3 Send a test WhatsApp message to **Padma Clinics** number (+6281339394907)
  - [ ] Verify message appears in Chatwoot Padma Clinics inbox
- [ ] 5.4 Reply to a message from Chatwoot — verify reply received on WhatsApp
- [ ] 5.5 Check router logs for clean startup (no errors, route count matches)

---

## 6. DLQ & Alerting

**What changed:** Extracted DLQ (S3) and alert (SES) modules from router. Used by both webhook routing and direct chat.

- [ ] 6.1 Check router startup log for `[WabaCheck]` line — should say "no override_callback_uri detected"
- [ ] 6.2 If any webhook forward fails (check logs), verify payload appears in S3 DLQ bucket
- [ ] 6.3 If any direct chat send fails (test 4.4), verify SES alert email received

---

## 7. CI/CD Pipeline

**What changed:** Build on pmg-build runner, ARM64 images, ECR layer cache, auto-deploy to staging, pre-deploy pg_dump.

- [ ] 7.1 Push to `develop` — verify CI workflow triggers and passes
- [ ] 7.2 Verify Docker image built and pushed to ECR
- [ ] 7.3 Verify staging auto-deployed after build
- [ ] 7.4 Before pushing to `main` — verify pg_dump snapshot is taken

---

## 8. Regression Checks

These features should work exactly as before — no changes, just verifying nothing broke.

- [ ] 8.1 Regular conversation flow: new inbound message → assign → reply → resolve
- [ ] 8.2 Conversation reopens on new inbound message after resolution
- [ ] 8.3 Contact import (data import) works correctly
- [ ] 8.4 Attachment handling — send/receive images, files
- [ ] 8.5 Agent assignment and mentions work
- [ ] 8.6 Canned responses work

---

## Sign-Off

| Area | Pass/Fail | Tester | Notes |
|------|-----------|--------|-------|
| Sidebar Navigation | | | |
| Status Filter | | | |
| Broadcasts (Sheets) | | | |
| Direct Chat API | | | |
| Webhook Routing | | | |
| DLQ & Alerting | | | |
| CI/CD | | | |
| Regression | | | |

**Overall:** [ ] PASS — ready for production push Monday night
**Blockers:** _______________
