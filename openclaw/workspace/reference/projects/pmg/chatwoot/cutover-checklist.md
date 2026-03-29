# Chatwoot Cutover Checklist — chat.pbmcgroup.com

**Target date:** Tuesday 18 March 2026
**Owner:** Alex / Kezia
**Server:** `ubuntu@10.10.3.112` (key: `16_chatwoot_services.pem`)
**Rollback trigger:** Any item in §4 that cannot be resolved within 30 minutes

---

## 1. Pre-Cutover Verification (Day before or morning of)

- [ ] Staging (`staging-chat.pbmcgroup.com`) is healthy — agents can log in, inbound messages flowing
- [ ] All 12 user accounts exist with correct roles and inbox assignments
- [ ] Gita (ID 6), Pebri (ID 13), Santhi (ID 7) have broadcast access confirmed
- [ ] `chat.pbmcgroup.com` DNS A-record exists in Route 53 pointing to ALB (TTL 60s)
- [ ] `curl -I https://chat.pbmcgroup.com` returns a response (even if it hits staging for now)
- [ ] Database backup taken and verified in S3:

```bash
DUMP=/tmp/chatwoot_pre_cutover_$(date +%Y%m%d).sql.gz
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production | gzip > $DUMP
aws s3 cp $DUMP s3://pmg-chatwoot-backups/pre-deploy/
echo "Backup complete: $DUMP"
```

---

## 2. Merge and Deploy Production

### 2.1 Merge staging → main

On your local machine:

```bash
cd ~/Projects/pmg/pmg-chatwoot
git fetch origin
git checkout main
git merge origin/staging --no-edit
git push origin main
```

### 2.2 Deploy to production server

SSH into server:

```bash
ssh -i 16_chatwoot_services.pem ubuntu@10.10.3.112
cd /home/chatwoot/chatwoot
sudo -u chatwoot git pull pmg main
sudo -u chatwoot /home/ubuntu/.rbenv/shims/bundle install
sudo -u chatwoot RAILS_ENV=production /home/ubuntu/.rbenv/shims/bundle exec rails assets:precompile
sudo systemctl restart chatwoot-web chatwoot-sidekiq
```

Wait 30 seconds, then verify:

```bash
ps aux | grep puma | grep -v grep
sudo systemctl status chatwoot-web --no-pager | tail -3
```

- [ ] Puma running as `chatwoot` user
- [ ] No errors in service status

---

## 3. Switch Domain

### 3.1 Update FRONTEND_URL

In `/home/chatwoot/chatwoot/.env`, update:

```
FRONTEND_URL=https://chat.pbmcgroup.com
```

Then restart:

```bash
sudo systemctl restart chatwoot-web chatwoot-sidekiq
```

- [ ] App accessible at `https://chat.pbmcgroup.com`
- [ ] Login works for at least one admin account

### 3.2 Update Meta webhook URLs (router switch)

In the router config on webhost, update webhook delivery URLs from `staging-chat.pbmcgroup.com` to `chat.pbmcgroup.com` for all three inboxes:

| Inbox | Old URL | New URL |
|-------|---------|---------|
| Padma Care | `staging-chat.pbmcgroup.com/webhooks/whatsapp/...` | `chat.pbmcgroup.com/webhooks/whatsapp/...` |
| Crew Care | `staging-chat.pbmcgroup.com/webhooks/whatsapp/...` | `chat.pbmcgroup.com/webhooks/whatsapp/...` |
| Clinics | `staging-chat.pbmcgroup.com/webhooks/whatsapp/...` | `chat.pbmcgroup.com/webhooks/whatsapp/...` |

- [ ] Router updated and saved

---

## 4. Per-Inbox Verification

For each inbox, send a test message from a personal WhatsApp number:

- [ ] **Padma Care** — inbound message appears in Chatwoot at `chat.pbmcgroup.com`
- [ ] **Crew Care** — inbound message appears
- [ ] **Clinics** — inbound message appears
- [ ] Reply to each test message — outbound delivery confirmed

---

## 5. Broadcast Send Test

- [ ] Log in as Gita, Pebri, or Santhi — confirm "Broadcast Baru" button is visible
- [ ] Create a test broadcast to a single known number using a Clinics template
- [ ] Message delivered to the test number
- [ ] Broadcast status shows `completed` (not `failed`)

---

## 6. Agent Communication

Owned by **Kezia**:

- [ ] WhatsApp message to all 12 agents: new URL is `https://chat.pbmcgroup.com`, same credentials
- [ ] Confirm agents do not need to re-authenticate WhatsApp — router handles this server-side
- [ ] Agents acknowledge receipt

---

## 7. Post-Cutover Monitoring (first 2 hours)

- [ ] Check Sidekiq dashboard (`/sidekiq`) — no failed jobs piling up
- [ ] Check server logs for errors: `sudo journalctl -u chatwoot-web -f`
- [ ] Confirm S3 attachments loading in conversations
- [ ] Confirm SES email notifications arriving for conversation assignments

---

## 8. Rollback Procedure

**Trigger rollback if:** App unreachable for >10 minutes, inbound messages not flowing after router switch, or data integrity concern.

**Steps (estimated 5 minutes):**

1. Point router webhook URLs back to `staging-chat.pbmcgroup.com`
2. Notify agents: revert to `app.chatwoot.com` temporarily
3. Investigate on production server without time pressure
4. `app.chatwoot.com` remains live until 10 April as archive/fallback

**Note:** Router switch is the only user-visible change. Reverting it is immediate and requires no server access.

---

## 9. Known Pre-Cutover Dependencies (resolve before go-live)

### 9.1 Production port assignment
Production Chatwoot will run on **port 3002** (staging is 3001). Requires:
- [ ] New systemd service files (`chatwoot-web-prod.service`, `chatwoot-sidekiq-prod.service`) with port 3002
- [ ] New ALB target group pointing to port 3002
- [ ] ALB listener rule: `chat.pbmcgroup.com` → port 3002 target group
- [ ] Separate app directory: `/home/chatwoot/chatwoot-prod` (cloned from `main`)
- [ ] Separate `.env` with `FRONTEND_URL=https://chat.pbmcgroup.com`

**Note:** This is a stopgap until Docker containerization (CI plan). Two native environments on one server is manageable short-term with separate ports and service files.

### 9.2 ALB listener rules — current state
| Domain | Port | Target | Status |
|--------|------|--------|--------|
| `staging-chat.pbmcgroup.com` | 3001 | Chatwoot staging | ✅ Working |
| `chatwoot.pbmcgroup.com` | 3000 | Broadcast Meta webhook receiver | ⚠️ Update on cutover |
| `chat.pbmcgroup.com` | 3002 | Chatwoot production | ❌ Not yet configured |

### 9.3 Broadcast Meta webhook update
`chatwoot.pbmcgroup.com` → port 3000 is currently where Meta sends broadcast webhooks. On cutover this needs to point to the production instance. Update ALB rule and confirm with Meta app webhook config.

**Action on cutover day**: After production is live on 3002, update `chatwoot.pbmcgroup.com` ALB rule to point to port 3002 target group (or consolidate to `chat.pbmcgroup.com`).

---

## Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 12 March 2026 | Alex + Claude | Initial checklist from PRD §1.5, §1.6, §1.7 and plan task outputs |
