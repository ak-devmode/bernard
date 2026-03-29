# 1. Chatwoot Operations Runbook

**Last updated:** 17 March 2026
**Applies to:** `chat.pbmcgroup.com` (production) and `staging-chat.pbmcgroup.com`

For architecture context see: `pmg-docs/infrastructure/chatwoot-infrastructure.md`

---

## 1.1 SSH Access

```bash
ssh chatwoot-staging
# Expands to: ssh -i ~/path/to/16_chatwoot_services.pem ubuntu@10.10.3.112
```

---

## 1.2 Check Service Status

```bash
# All Docker containers
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Expected healthy state:
# chatwoot-web-production      Up X hours   0.0.0.0:3002->3000/tcp
# chatwoot-sidekiq-production  Up X hours
# chatwoot-web-staging         Up X hours   0.0.0.0:3001->3000/tcp
# chatwoot-sidekiq-staging     Up X hours
# chatwoot_postgres            Up X hours   5432/tcp
# chatwoot_redis               Up X hours   6379/tcp

# Router
sudo systemctl status pmg-router

# Health check
curl http://localhost:3000/health
curl http://localhost:3001/health    # staging Chatwoot
curl http://localhost:3002/health    # production Chatwoot
```

---

## 1.3 Logs

```bash
# Production web (Rails/Puma)
aws logs tail /aws/chatwoot/production/web --follow --region ap-southeast-1

# Production Sidekiq
aws logs tail /aws/chatwoot/production/sidekiq --follow --region ap-southeast-1

# Staging web
aws logs tail /aws/chatwoot/staging/web --follow --region ap-southeast-1

# Router (live)
sudo journalctl -u pmg-router -f

# Router (last 100 lines)
sudo journalctl -u pmg-router -n 100 --no-pager

# System log
sudo journalctl -f
```

Note: `docker logs` does not work — all containers use the `awslogs` driver, logs go to CloudWatch only.

---

## 1.4 Start / Stop / Restart

### 1.4.1 Production stack

```bash
cd /home/chatwoot/chatwoot

# Restart (rolling — containers restart one at a time)
docker compose -f docker-compose.pmg.yml --profile production restart

# Full stop and start (brief downtime)
docker compose -f docker-compose.pmg.yml --profile production down
docker compose -f docker-compose.pmg.yml --profile production up -d

# Restart individual container
docker restart chatwoot-web-production
docker restart chatwoot-sidekiq-production
```

### 1.4.2 Staging stack

```bash
docker compose -f docker-compose.pmg.yml --profile staging restart
```

### 1.4.3 Router

```bash
sudo systemctl restart pmg-router
sudo systemctl status pmg-router
```

### 1.4.4 Databases (handle with care)

```bash
# These are standalone containers — restart only if necessary
docker restart chatwoot_postgres
docker restart chatwoot_redis
```

---

## 1.5 Deploy (Code Changes Only — No Asset Changes)

```bash
cd /home/chatwoot/chatwoot
git pull pmg staging        # or main after go-live

# Restart to pick up code changes
docker compose -f docker-compose.pmg.yml --profile production restart
docker compose -f docker-compose.pmg.yml --profile staging restart
```

## 1.6 Deploy (Frontend/Asset Changes — Image Rebuild Required)

Takes 20–30 minutes. Watch `free -h` during build — OOM surfaces as cryptic JS errors.

```bash
cd /home/chatwoot/chatwoot
git pull pmg staging

# Build new image
docker build -f docker/Dockerfile -t pmg-chatwoot:staging .
docker tag pmg-chatwoot:staging pmg-chatwoot:production

# Recreate containers with new image
docker compose -f docker-compose.pmg.yml --profile staging up -d --force-recreate
docker compose -f docker-compose.pmg.yml --profile production up -d --force-recreate
```

---

## 1.7 Rails Console

```bash
# Production
docker exec -it chatwoot-web-production bundle exec rails console

# Staging
docker exec -it chatwoot-web-staging bundle exec rails console
```

---

## 1.8 Database

### 1.8.1 Connect

```bash
docker exec -it chatwoot_postgres psql -U chatwoot chatwoot_production
docker exec -it chatwoot_postgres psql -U chatwoot chatwoot_staging
```

### 1.8.2 Run Migrations

```bash
docker exec chatwoot-web-production bundle exec rails db:migrate
```

### 1.8.3 Manual Backup

```bash
# Production
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production | gzip > /tmp/prod_$(date +%Y%m%d_%H%M).sql.gz
aws s3 cp /tmp/prod_*.sql.gz s3://pmg-chatwoot-backups/manual/

# Staging
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_staging | gzip > /tmp/staging_$(date +%Y%m%d_%H%M).sql.gz
```

### 1.8.4 Restore from Backup

```bash
# 1. Stop the app containers (leave Postgres running)
docker compose -f docker-compose.pmg.yml --profile production down

# 2. Drop and recreate the database
docker exec chatwoot_postgres psql -U chatwoot -d postgres -c "DROP DATABASE chatwoot_production;"
docker exec chatwoot_postgres psql -U chatwoot -d postgres -c "CREATE DATABASE chatwoot_production OWNER chatwoot;"

# 3. Download backup from S3
aws s3 cp s3://pmg-chatwoot-backups/manual/prod_YYYYMMDD_HHMM.sql.gz /tmp/

# 4. Restore
gunzip -c /tmp/prod_YYYYMMDD_HHMM.sql.gz | docker exec -i chatwoot_postgres psql -U chatwoot chatwoot_production

# 5. Flush Redis (clears stale Sidekiq jobs and session cache)
docker exec chatwoot_redis redis-cli FLUSHALL

# 6. Start app containers
docker compose -f docker-compose.pmg.yml --profile production up -d

# 7. Verify
curl http://localhost:3002/health
docker exec chatwoot-web-production bundle exec rails runner "puts Account.count"
```

---

## 1.9 Environment Files

Environment files are generated from SSM — never edit them manually.

```bash
cd /home/chatwoot/chatwoot
bash fetch-secrets.sh production   # regenerates .env.production
bash fetch-secrets.sh staging      # regenerates .env.staging

# After regenerating, force-recreate containers to pick up changes
docker compose -f docker-compose.pmg.yml --profile production up -d --force-recreate
```

---

## 1.10 Router Config Changes

The router config lives in two places — keep them in sync:

```bash
# 1. Edit source in git repo
vim /home/chatwoot/chatwoot/chatwoot-services/router/router.js
# (or edit locally and push)

# 2. Copy to deployed location
sudo cp /home/chatwoot/chatwoot/chatwoot-services/router/router.js /var/www/chatwoot-services/router/router.js

# 3. Restart
sudo systemctl restart pmg-router
```

### 1.10.1 Cutover router change

On go-live day, uncomment 3 lines (one per inbox) and remove cloud + staging URLs:

```javascript
// Change FROM (pre-cutover dual-delivery):
urls: [
  'https://app.chatwoot.com/webhooks/whatsapp/+62...',
  STAGING_URL + '/webhooks/whatsapp/+62...',
  // PRODUCTION_URL + '/webhooks/whatsapp/+62...'
]

// Change TO (post-cutover, production only):
urls: [
  PRODUCTION_URL + '/webhooks/whatsapp/+62...'
]
```

---

## 1.11 Common Issues

### Containers not starting after reboot

```bash
# Check systemd units
sudo systemctl status chatwoot-production-docker
sudo journalctl -u chatwoot-production-docker -n 50

# Likely cause: chatwoot user not in docker group
groups chatwoot
sudo usermod -aG docker chatwoot
# Then reboot or start manually:
docker compose -f docker-compose.pmg.yml --profile production up -d
```

### Router not receiving webhooks

```bash
# Check router is running
sudo systemctl status pmg-router
curl http://localhost:3000/health

# Check ALB target group health in AWS Console
# whatsapp.pbmcgroup.com → ALB → target group → EC2:3000

# Check Meta webhook URL in developers.facebook.com
# Should be: https://whatsapp.pbmcgroup.com/webhook
```

### WhatsApp messages routing to wrong destination (override_callback_uri active)

**What it is:** Meta's Graph API supports an `override_callback_uri` per WABA. When set, Meta ignores the app-level webhook URL and sends all events for that WABA directly to the override URL — bypassing our router entirely. Chatwoot's `WebhookSetupService` registers this override automatically every time a WhatsApp Cloud API inbox is created.

**The override is invisible in the Meta Developer Console** — the app-level webhook URL still shows correctly. It is only detectable via the API.

**Detect:**

```bash
# Replace {WABA_ID} and {TOKEN} with real values (from SSM or .env)
curl -s 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'

# Healthy output (no override):
# {"data":[{"whatsapp_business_api_data":{"id":"...","name":"..."}}]}

# Unhealthy output (override active):
# {"data":[{...,"override_callback_uri":"https://some-stale-endpoint/webhook"}]}
```

**Remove override and re-subscribe:**

```bash
# Step 1: Remove the override (and unsubscribe)
curl -X DELETE 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'

# Step 2: Re-subscribe without override (restores app-level webhook)
curl -X POST 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'

# Step 3: Verify — output should have no override_callback_uri
curl -s 'https://graph.facebook.com/v22.0/{WABA_ID}/subscribed_apps' \
  -H 'Authorization: Bearer {TOKEN}'
```

**Prevention:** `DISABLE_WHATSAPP_WEBHOOK_SETUP=true` in staging `.env` prevents `WebhookSetupService` from running on staging inbox creation. **Never create WhatsApp inboxes in staging without this guard in place.**

**WABAs in use:**

**WABA in use:** `1853014602084429` (Padma Medical Group - Core Account) — shared by all three inboxes.

| Inbox | Phone number | Notes |
|---|---|---|
| Padma Care | +62 822-6632-3030 | |
| Crew Care | +62 821-3109-6676 | |
| Padma Clinics | +62 813-3939-4907 | Migrated to this WABA 2026-02-19 |

**Reference:** Post-mortem 2026-03-17 — WhatsApp Webhook Override Hijacking Production Traffic (`pmg-docs/postmortems/2026-03-17-whatsapp-webhook-override.md`)

### Sidekiq queue backing up

```bash
# Check queue depth via Rails console
docker exec -it chatwoot-web-production bundle exec rails runner \
  "puts Sidekiq::Stats.new.queues.inspect"

# Restart Sidekiq
docker restart chatwoot-sidekiq-production
```

### Disk space low

```bash
df -h /
# If >80%:

# Clear Docker build cache (safe — doesn't affect running containers)
docker buildx prune -f
docker image prune -f

# Check largest directories
du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -10
```

### Broadcast failing (Google Sheets auth)

```bash
# Test SSM credential fetch
aws ssm get-parameter --name "/pmg/google/service_account_key" --with-decryption --region ap-southeast-1

# Test from Rails console
docker exec -it chatwoot-web-production bundle exec rails runner \
  "puts GoogleSheetsService.new.get_tabs('1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck').inspect"
```

---

## 1.13 DLQ Failover Procedure

Two-layer DLQ protects against Meta's 15-minute webhook retry window.
S3 bucket: `s3://pmg-webhook-dlq` (ap-southeast-1, objects expire after 30 days).

### Layer 1 — Chatwoot containers down, router running

The router automatically writes failed payloads to S3. No manual action needed during the outage.
Once Chatwoot is back up, replay:

```bash
# Dry run first — verify targets
node chatwoot-services/router/replay.js --dry-run --date YYYY-MM-DD

# Live replay
node chatwoot-services/router/replay.js --date YYYY-MM-DD
```

### Layer 2 — EC2 or router process down (activate DLQ mode)

1. **Switch ALB to Lambda:**
   AWS Console → EC2 → Load Balancers → select ALB →
   Listeners → `whatsapp.pbmcgroup.com:443` →
   Raise the Lambda target group rule (`pmg-webhook-dlq`) priority **above** the EC2 rule.
   Meta webhooks now write directly to S3 via Lambda.

2. **Restore router, then switch ALB back:**
   Lower the Lambda rule priority back below the EC2 rule.

3. **Replay any objects written during the outage:**
   ```bash
   # Check what's in the bucket
   aws s3 ls s3://pmg-webhook-dlq/ --region ap-southeast-1
   aws s3 ls s3://pmg-webhook-dlq/YYYY-MM-DD/ --region ap-southeast-1

   # Replay
   node chatwoot-services/router/replay.js --date YYYY-MM-DD
   ```

### Notes
- Replay is idempotent within a single run (wamid dedup in memory).
- Run replay once per affected date. If you replay the same date twice, duplicate messages may be delivered — check Chatwoot for duplicates.
- Layer 2 Lambda env var: `DLQ_BUCKET=pmg-webhook-dlq`.

---

## 1.12 Escalation

| Issue | First contact | Notes |
|-------|--------------|-------|
| Chatwoot app down | Alex Knecht | Check CloudWatch alarm email first |
| WhatsApp messages not routing | Alex Knecht | Check router logs + ALB target health |
| Broadcast failures | Okto | Check Sidekiq logs + Google Sheets access |
| Agent access issues | Kezia | Login credentials, URL = `chat.pbmcgroup.com` |
| Data/conversation issues | Okto | Migration scripts, app.chatwoot.com stays live until 10 April |
