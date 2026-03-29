# Post-Mortem: WhatsApp Webhook Override Hijacking Production Traffic

**Date:** 17 March 2026
**Duration:** ~5 hours active debugging (17 March 00:30 – 04:00, resumed 08:30 – 09:00 GMT+8)
**Severity:** High — production inbound messages not reaching new Chatwoot instance
**Author:** Alex Knecht
**Status:** Resolved

---

## 1. Summary

During the Chatwoot cutover from `app.chatwoot.com` (cloud) to `chat.pbmcgroup.com` (self-hosted), inbound WhatsApp messages continued routing to the old staging and cloud instances despite the router being correctly configured for production-only delivery. The root cause was a Meta Graph API feature called `override_callback_uri` — registered automatically by Chatwoot when WhatsApp Cloud API inboxes are created — which silently redirected all WABA webhook traffic away from our router to a stale endpoint.

---

## 2. Timeline

| Time (GMT+8) | Event |
|---|---|
| **Sat 15 Mar** | Router deployed with triple-delivery (cloud + staging + production). All three destinations receiving messages. Production delivery confirmed. |
| **Sun 16 Mar 23:57** | Router updated to production-only (staging + cloud commented out). Committed, pushed, deployed to EC2, `pmg-router` restarted. |
| **Mon 17 Mar 00:07** | First message routed through new config — `Successfully forwarded to Padma Care (production)`. Router appears to be working. |
| **Mon 17 Mar 00:39** | Alex sends test messages to Padma Care. Messages appear in **staging** DB but **not** production. Router logs show **no entries** for these messages at this timestamp. |
| **Mon 17 Mar 00:45** | Begin debugging. Check router file on VM — correct. Check ALB rules — correct. Check Redis isolation — correct. Check .env files — correct. |
| **Mon 17 Mar 01:00–04:00** | Extensive debugging with Sonnet. Hypotheses tested: wrong router file loaded, stale process, orphan node process, ALB misconfiguration, Redis cross-contamination, FRONTEND_URL misconfiguration. All ruled out. |
| **Mon 17 Mar 04:00** | Switched to Opus. STATUS doc written capturing findings and hypothesis about WABA-level webhook subscription. |
| **Mon 17 Mar 08:30** | Resumed with Opus. SSH into VM. Verified all 3 router.js copies are identical and correct. |
| **Mon 17 Mar 08:40** | Checked staging Docker container logs — POSTs arriving from ALB IP (`18.142.12.57`), **not** from router (`127.0.0.1`). Router has zero logs during same window. Confirmed traffic bypassing router entirely. |
| **Mon 17 Mar 08:45** | Queried Meta Graph API: `GET /1853014602084429/subscribed_apps`. Found `override_callback_uri: "https://chatwoot.pbmcgroup.com/webhook"` — the old webhost endpoint. |
| **Mon 17 Mar 08:48** | Removed override: `DELETE /1853014602084429/subscribed_apps`. Re-subscribed app without override. |
| **Mon 17 Mar 08:50** | Test message sent. Router logs: `Routing webhook for Padma Clinics → Successfully forwarded (production)`. Production receives message. Staging receives nothing. **Resolved.** |

---

## 3. Root Cause

### 3.1 The mechanism

Chatwoot's `WebhookSetupService` runs automatically when a WhatsApp Cloud API inbox is created (`after_commit :setup_webhooks`). It calls two Meta Graph API endpoints:

```ruby
# Step 1: Subscribe app to WABA
POST /{WABA_ID}/subscribed_apps

# Step 2: Override the callback URL for this WABA
POST /{WABA_ID}/subscribed_apps
  body: { override_callback_uri: "https://staging-chat.pbmcgroup.com/webhooks/whatsapp/+62..." }
```

The `override_callback_uri` tells Meta: "for this WABA, ignore the app-level webhook URL and send events here instead." This completely bypasses the app-level webhook configured in Meta Developer Console (`whatsapp.pbmcgroup.com/webhook`).

### 3.2 How it was triggered

When staging Chatwoot inboxes were created with WhatsApp Cloud API credentials (access token, phone number IDs, WABA ID), the setup service registered an override pointing to `chatwoot.pbmcgroup.com/webhook`. This ALB rule routed to the old webhost (`i-0e836f1779a297dc9`) which still ran the pre-cutover router config (delivering to `app.chatwoot.com` + `staging-chat.pbmcgroup.com`).

### 3.3 Why it wasn't obvious

- The `override_callback_uri` is not visible in Meta Developer Console — the app-level webhook URL still shows `whatsapp.pbmcgroup.com/webhook`, which looks correct
- The override is only visible via the Graph API: `GET /{WABA_ID}/subscribed_apps`
- The router was receiving *some* traffic (2 messages got through on Sunday), creating a misleading partial-success signal
- The Chatwoot documentation does not mention this override behavior

### 3.4 Why it appeared to work on the weekend

When the router was in triple-delivery mode (cloud + staging + production), the override was already active — but since staging was one of the intended destinations anyway, the duplicate delivery was invisible. The override only became apparent when we switched to production-only and expected staging to stop receiving messages.

---

## 4. What We Tried (and Why It Didn't Help)

| Investigation | Result | Why it was a dead end |
|---|---|---|
| Verified router.js on VM (all 3 copies) | All correct, production-only | The file was never the problem |
| Checked for orphan node processes | Only pmg-router running | No stale process |
| Verified ALB listener rules | Rule 4: `whatsapp.pbmcgroup.com` → correct target group | ALB was fine |
| Checked Redis db isolation | Production db 0, staging db 1 | No cross-contamination |
| Verified .env FRONTEND_URL | Correct for both staging and production | Not the issue |
| Restarted pmg-router multiple times | Same behavior | Router was already correct |
| Checked Meta webhook URL in Developer Console | Shows `whatsapp.pbmcgroup.com/webhook` | Override is invisible here |

---

## 5. What Fixed It

```bash
# 1. Query current WABA subscriptions
curl -s 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'
# Revealed: override_callback_uri: "https://chatwoot.pbmcgroup.com/webhook"

# 2. Remove the override
curl -X DELETE 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'

# 3. Re-subscribe app without override
curl -X POST 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'
```

### Preventive measure

Added `DISABLE_WHATSAPP_WEBHOOK_SETUP=true` env var to staging. The `Channel::Whatsapp` model now checks this before running `WebhookSetupService`, preventing staging from re-registering the override when WhatsApp inboxes are created.

---

## 6. Learnings

### 6.1 When the hotfix doesn't work, trace the full path

We spent hours verifying components in isolation (router config, ALB rules, Redis, .env). Each component checked out individually. The breakthrough came from **tracing the actual HTTP request path end-to-end**:

1. What IP is hitting staging? → ALB (`18.142.12.57`)
2. Is the router involved? → No (zero logs during the window)
3. Therefore: traffic is reaching staging without going through the router
4. What could send traffic to staging externally? → Check WABA subscriptions

**Rule: When a "simple config change" doesn't work, stop verifying the config and start observing actual traffic. `docker logs`, source IPs, and timestamps don't lie.**

### 6.2 Don't trust what the UI shows you

The Meta Developer Console showed the correct webhook URL (`whatsapp.pbmcgroup.com/webhook`). The override was only visible via the Graph API. When debugging integrations with third-party platforms, always check the API directly — UIs often show a simplified or incomplete view.

### 6.3 Understand what your frameworks do behind the scenes

Chatwoot's inbox creation triggers a chain: `after_commit → setup_webhooks → WebhookSetupService → subscribe_waba_webhook → override_waba_callback`. This registers a Meta webhook override that's invisible from the Meta console and persists even after the Chatwoot code is changed. We didn't know this mechanism existed.

**Rule: When using a framework that integrates with external APIs, read the service classes that run on create/update/destroy. Side effects in callbacks can outlast the objects that triggered them.**

### 6.4 Stop jumping, start walking

At 1am, debugging looked like: check router → check ALB → check Redis → check .env → re-check router → restart router → check ALB again. This is understandable under time pressure but unproductive.

**Better approach:**
1. Pick the starting point (Meta sends webhook)
2. Verify it arrives at the next hop (ALB → which target group?)
3. Verify the next hop (target group → which instance?)
4. Verify the instance (what process receives it? what are the logs?)
5. Follow through to destination

Each step either confirms or breaks the chain. The break point IS the problem.

---

## 7. Action Items

- [x] Remove Meta WABA override
- [x] Re-subscribe app without override
- [x] Add `DISABLE_WHATSAPP_WEBHOOK_SETUP` env guard to staging
- [x] Delete staging WhatsApp inboxes
- [ ] Rebuild staging Docker image with env guard
- [ ] Recreate staging inboxes (with test numbers) to verify guard works
- [ ] Document `override_callback_uri` risk in runbook
- [ ] Consider adding a startup check to pmg-router that queries `GET /{WABA_ID}/subscribed_apps` and warns if an override exists

---

## 8. Additional Cleanup Completed

While debugging, several long-standing issues were addressed:

- Eliminated redundant router.js copy (`/var/www/chatwoot-services/` deleted; systemd now points at git repo)
- Deleted stale local `chatwoot-services/` directory (non-git copy causing confusion)
- Consolidated chatwoot docs from pmg-docs into pmg-chatwoot/docs/
- Deleted 8 stale files (old systemd units, unused docker-compose files, deploy.sh)
- Updated README.md (was referencing wrong repo, branch names, and version)
- Cleaned up stale `/home/ubuntu/fetch-secrets.sh` on VM
- Fixed file ownership to `chatwoot:chatwoot` in chatwoot-services/
