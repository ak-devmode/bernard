# 1. Chatwoot Infrastructure — Architecture Overview

**Last updated:** 15 March 2026
**Status:** Production live as of 18 March 2026 (target)

---

## 1.1 Summary

PMG runs a self-hosted fork of Chatwoot v4.11.1 on a single AWS EC2 instance in `ap-southeast-1` (Singapore). Two isolated environments (staging and production) share the same host, databases, and Redis. Traffic arrives via an AWS Application Load Balancer. WhatsApp webhooks are received by a Node.js router service that forwards to the correct Chatwoot inbox.

---

## 1.2 Repository

| Repo | Purpose |
|------|---------|
| `Padma-Medical-Group/pmg-chatwoot` | Fork of `chatwoot/chatwoot` v4.11.1 with PMG customisations |
| `Padma-Medical-Group/pmg-docs` | Architecture, operations, and planning docs |

Branch strategy:
```
upstream (chatwoot/chatwoot v4.11.1)
        ↓ fork
pmg-chatwoot
  ├── staging    — deployed to EC2; base for all PMG work
  ├── develop    — integration branch; PRs merge here first (CI-gated)
  └── main       — production branch (post go-live)
```

PMG customisations are documented in `pmg-chatwoot/PMG-CHANGES.md`.

---

## 1.3 EC2 Instance

| Property | Value |
|----------|-------|
| Instance ID | `i-053b3845a7aa0850d` |
| Private IP | `10.10.3.112` |
| Type | `t4g.medium` (ARM64, 2 vCPU, 4GB RAM + 2GB swap) |
| AZ | `ap-southeast-1a` |
| OS | Ubuntu 22.04 |
| SSH user | `ubuntu` |
| SSH alias | `chatwoot-staging` |
| Key | `16_chatwoot_services.pem` (Dropbox/IT_Infra/AWS/Keypairs-Credentials) |
| App user | `chatwoot` (owns app processes, member of `docker` group) |

---

## 1.4 Service Architecture

```
Internet
    │
    ▼
AWS ALB (HTTPS 443, ACM cert *.pbmcgroup.com)
    │
    ├── staging-chat.pbmcgroup.com  ──► EC2:3001  chatwoot-web-staging  (Docker)
    │                                             chatwoot-sidekiq-staging (Docker)
    │
    ├── chat.pbmcgroup.com          ──► EC2:3002  chatwoot-web-production (Docker)
    │                                             chatwoot-sidekiq-production (Docker)
    │
    └── whatsapp.pbmcgroup.com      ──► EC2:3000  pmg-router (Node.js, systemd)

EC2 — shared infrastructure (Docker containers, pmg_net bridge network)
    chatwoot_postgres  (pgvector/pgvector:pg15)  — port 5432
    chatwoot_redis     (redis:7-alpine)           — port 6379
```

### 1.4.1 Port Summary

| Port | Service | UFW |
|------|---------|-----|
| 22 | SSH | ✅ open |
| 3000 | pmg-router (WhatsApp webhook receiver) | ✅ open |
| 3001 | chatwoot-web-staging | ✅ open |
| 3002 | chatwoot-web-production | ✅ open |
| 5432 | chatwoot_postgres | internal only |
| 6379 | chatwoot_redis | internal only |

---

## 1.5 Docker Setup

All four Chatwoot application containers are defined in `pmg-chatwoot/docker-compose.pmg.yml` using Docker Compose profiles.

### 1.5.1 Images

| Image | Built from | Used by |
|-------|-----------|---------|
| `pmg-chatwoot:staging` | `docker/Dockerfile` on EC2 (ARM64) | staging profile |
| `pmg-chatwoot:production` | Tagged from staging image | production profile |

Images must be built on the EC2 host (ARM64) — do not cross-compile. Build takes ~20–30 minutes on a t4g.medium. The `NODE_OPTIONS=--max-old-space-size=4096` flag is set in the Dockerfile to prevent OOM during Vite compilation.

### 1.5.2 Compose Profiles

```bash
# Start staging
docker compose -f docker-compose.pmg.yml --profile staging up -d

# Start production
docker compose -f docker-compose.pmg.yml --profile production up -d
```

### 1.5.3 Docker Network

All containers communicate via the `pmg_net` bridge network (declared `external: true` in compose). Created once:

```bash
docker network create pmg_net
docker network connect pmg_net chatwoot_redis
docker network connect pmg_net chatwoot_postgres
```

Within the network, containers reference each other by container name:
- `POSTGRES_HOST=chatwoot_postgres`
- `REDIS_URL=redis://chatwoot_redis:6379`

### 1.5.4 Persistent Volumes

| Volume | Contents |
|--------|---------|
| `pmg-chatwoot_staging-storage` | Active Storage file uploads (staging) |
| `pmg-chatwoot_production-storage` | Active Storage file uploads (production) |

S3 is the primary attachment backend — these volumes are a fallback only.

### 1.5.5 Systemd Boot Units

Docker stacks auto-start on reboot via systemd units in `deployment/`:

| Unit | Starts |
|------|--------|
| `chatwoot-staging-docker.service` | staging profile |
| `chatwoot-production-docker.service` | production profile |

Both use `Type=oneshot RemainAfterExit=yes`. Run as `chatwoot` user (must be in `docker` group).

---

## 1.6 Environment Management

Environment files are generated on the EC2 host from AWS SSM Parameter Store — they are never committed to git.

```bash
cd /home/chatwoot/chatwoot
bash fetch-secrets.sh staging      # writes .env.staging
bash fetch-secrets.sh production   # writes .env.production
```

SSM parameters live under `/pmg/chatwoot/` in `ap-southeast-1`. The EC2 IAM role has read access.

Profile-specific values hardcoded in `fetch-secrets.sh`:

| Variable | Staging | Production |
|----------|---------|------------|
| `FRONTEND_URL` | `https://staging-chat.pbmcgroup.com` | `https://chat.pbmcgroup.com` |
| `POSTGRES_DATABASE` | `chatwoot_staging` | `chatwoot_production` |
| `POSTGRES_HOST` | `chatwoot_postgres` | `chatwoot_postgres` |
| `REDIS_URL` | `redis://chatwoot_redis:6379` | `redis://chatwoot_redis:6379` |

Note: `POSTGRES_HOST` and `REDIS_URL` are hardcoded (not from SSM) because SSM stores the native `127.0.0.1` values which are invalid inside Docker.

---

## 1.7 Databases

Both databases live inside the `chatwoot_postgres` container.

| Database | Used by | State |
|----------|---------|-------|
| `chatwoot_staging` | Staging stack | Live data (receiving WhatsApp messages since ~14 March 2026) |
| `chatwoot_production` | Production stack | Seeded from staging config (users, inboxes, contacts) — conversations imported via migration |

Backup location: `s3://pmg-chatwoot-backups/`

---

## 1.8 WhatsApp Router (`pmg-router`)

The router is a Node.js Express service that:
1. Receives Meta webhook POST requests at `/webhook`
2. Routes by `phone_number_id` to the correct Chatwoot inbox URL(s)
3. Handles the Kyoo integration endpoint (`/api/v1/sendTemplateMessages`)

| Property | Value |
|----------|-------|
| Code | `pmg-chatwoot/chatwoot-services/router/router.js` |
| Deployed to | `/var/www/chatwoot-services/router/` on EC2 |
| Systemd unit | `pmg-router.service` |
| Port | 3000 |
| Health check | `GET /health` → `{"status":"ok","routes":3}` |
| Webhook URL | `https://whatsapp.pbmcgroup.com/webhook` |

### 1.8.1 Routing Table

| Inbox | Phone | `phone_number_id` |
|-------|-------|-----------------|
| Padma Care | +62 822-6632-3030 | `1040379045817892` |
| Crew Care | +62 821-3109-676 | `983987788132351` |
| Padma Clinics | +62 813-3939-4907 | `950941214777802` |

All three numbers are on WABA `1853014602084429` (new WABA, migrated Feb 2026).

### 1.8.2 Delivery Mode

| Period | Delivery |
|--------|---------|
| Pre-cutover (now) | Dual: `app.chatwoot.com` + staging |
| Cutover day | Single: production only (uncomment 3 lines, remove cloud + staging) |

---

## 1.9 Broadcast Module

The broadcast feature is implemented natively in Rails (not as an external script call):

```
User → Chatwoot UI → BroadcastsController
                   → BroadcastExecutorJob (Sidekiq)
                   → Whatsapp::BroadcastFromSheetService
                        ├── GoogleSheetsService (reads recipient list)
                        └── channel.send_template (sends via Meta Cloud API)
```

Google service account credentials are fetched from SSM at `/pmg/google/service_account_key` automatically via the EC2 IAM role. No external service call or SSH required.

The standalone `broadcast.sh` CLI in `chatwoot-services/broadcast/` is a separate tool for manual command-line sends only.

---

## 1.10 Logging

All containers use the `awslogs` Docker logging driver. Logs ship directly to CloudWatch — `docker logs` is not available on EC2.

| Container | CloudWatch Log Group |
|-----------|---------------------|
| `chatwoot-web-staging` | `/aws/chatwoot/staging/web` |
| `chatwoot-sidekiq-staging` | `/aws/chatwoot/staging/sidekiq` |
| `chatwoot-web-production` | `/aws/chatwoot/production/web` |
| `chatwoot-sidekiq-production` | `/aws/chatwoot/production/sidekiq` |

Router logs: `sudo journalctl -u pmg-router -f`

CWAgent also ships system logs:
- `/var/log/syslog` → `/aws/chatwoot/staging/syslog`
- `/var/log/fail2ban.log` → `/aws/chatwoot/staging/fail2ban`

---

## 1.11 Monitoring

CloudWatch alarms — all route to SNS topic `PBMC-CloudWatch-Alarm` → `it-alerts@pbmcgroup.com`:

| Alarm | Metric | Threshold |
|-------|--------|-----------|
| `chatwoot-instance-status` | `StatusCheckFailed` | ≥ 1 for 2 min |
| `chatwoot-high-cpu` | `CPUUtilization` | > 80% for 5 min |
| `chatwoot-sidekiq-queue-depth` | `PMG/Chatwoot:sidekiq_queue_size` | > 500 jobs |
| `chatwoot-disk-full` | `Chatwoot:DISK_USED` | ≥ 85% for 10 min |

Note: `sidekiq_queue_size` metric requires instrumentation to publish — alarm created but metric not yet publishing.

---

## 1.12 Secrets Management

All secrets stored in AWS SSM Parameter Store (`ap-southeast-1`), encrypted with default KMS key:

| SSM Path | Contents |
|----------|---------|
| `/pmg/chatwoot/*` | Shared app secrets (SECRET_KEY_BASE, DB/SMTP credentials) |
| `/pmg/chatwoot/staging/integration_api_token` | Staging Chatwoot integration user API token |
| `/pmg/chatwoot/production/integration_api_token` | Production Chatwoot integration user API token |
| `/pmg/google/service_account_key` | Google service account JSON (for Sheets access) |
| `/pmg/kyoo/api_token` | Kyoo gateway authentication token |
