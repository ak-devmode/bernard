# PMG Chatwoot — Deployment Guide

**Stack:** Docker (app + Sidekiq) + standalone Docker containers (Postgres, Redis)
**Host:** EC2 `10.10.3.112` (ap-southeast-1, private VPC) — SSH alias `chatwoot-staging`
**Repo:** `Padma-Medical-Group/pmg-chatwoot` — fork of chatwoot/chatwoot v4.11.1
**App path on EC2:** `/home/chatwoot/chatwoot`

---

## 1. Environments

| Environment | URL | Port | Docker profile | DB |
|-------------|-----|------|----------------|----|
| Staging | `https://staging-chat.pbmcgroup.com` | 3001 | `staging` | `chatwoot_staging` |
| Production | `https://chat.pbmcgroup.com` | 3002 | `production` | `chatwoot_production` |

Both environments run on the same EC2 instance. Traffic reaches the instance via the AWS ALB:
- `staging-chat.pbmcgroup.com` → ALB rule → target group port 3001
- `chat.pbmcgroup.com` → ALB rule → target group port 3002

---

## 2. Service Architecture

```
ALB (443/HTTPS)
  ├── staging-chat.pbmcgroup.com  → EC2:3001 → chatwoot-web-staging  (Docker)
  │                                          → chatwoot-sidekiq-staging (Docker)
  └── chat.pbmcgroup.com          → EC2:3002 → chatwoot-web-production (Docker)
                                             → chatwoot-sidekiq-production (Docker)

Shared infrastructure (Docker, pmg_net):
  chatwoot_postgres  (pgvector/pg15)
  chatwoot_redis     (redis:7-alpine)

Port 3000 (EC2):
  pmg-router.service (Node.js Express — WhatsApp webhook router)
```

---

## 3. SSH Access

```bash
ssh -i "16_chatwoot_services.pem" ubuntu@10.10.3.112
# Or using alias:
ssh chatwoot-staging
```

---

## 4. Day-to-Day Deployment

### 4.1 Standard deploy (code changes only, no asset changes)

```bash
# On EC2
cd /home/chatwoot/chatwoot
git pull pmg staging        # or: git pull pmg main (after go-live)

# Restart staging containers
docker compose -f docker-compose.pmg.yml --profile staging restart
```

### 4.2 Deploy with image rebuild (frontend/asset changes)

Images are now built by CI on the `pmg-build` runner and pushed to ECR. Staging auto-deploys after the build. Production requires a manual step.

**Staging:** Automatic after merge to `staging` branch (CI handles pull + recreate).

**Production:** After merging to `main`, CI builds and pushes to ECR, then prints the image tag. Run the deploy script on the server:

```bash
ssh pmg-chatwoot
cd /home/chatwoot/chatwoot
bash scripts/production-deploy.sh <IMAGE_TAG>
```

The `IMAGE_TAG` is in the GitHub Actions run → "Build image" job → look for the `✅ Image pushed` line. Format: `main-<sha>-<run_number>`.

The script handles: DB backup → ECR login → pull → tag → recreate containers → migrate → health check.

**Legacy (local build, only if CI is unavailable):**
```bash
# On EC2 — takes 20–30 min
cd /home/chatwoot/chatwoot
git pull pmg main
docker build -f docker/Dockerfile -t pmg-chatwoot:production .
docker compose -f docker-compose.pmg.yml --profile production up -d --force-recreate
docker exec chatwoot-web-production bundle exec rails db:migrate
```

### 4.3 Check running containers

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Expected output (staging running):
```
chatwoot-web-staging      Up X hours   0.0.0.0:3001->3000/tcp
chatwoot-sidekiq-staging  Up X hours
chatwoot_postgres         Up X hours   5432/tcp
chatwoot_redis            Up X hours   6379/tcp
```

---

## 5. Environment Files

Env files are **generated on the EC2 host from AWS SSM** — they are never committed to git.

```bash
# Generate (or regenerate) env file for a profile
cd /home/chatwoot/chatwoot
bash fetch-secrets.sh staging      # writes .env.staging
bash fetch-secrets.sh production   # writes .env.production
```

SSM parameters live under `/pmg/chatwoot/` in `ap-southeast-1`. The EC2 IAM role has read access.

Profile-specific overrides written by `fetch-secrets.sh`:

| Variable | Staging | Production |
|----------|---------|------------|
| `FRONTEND_URL` | `https://staging-chat.pbmcgroup.com` | `https://chat.pbmcgroup.com` |
| `POSTGRES_DATABASE` | `chatwoot_staging` | `chatwoot_production` |

---

## 6. Database

Both databases live inside the `chatwoot_postgres` Docker container.

```bash
# Connect to Postgres
docker exec -it chatwoot_postgres psql -U chatwoot

# List databases
\l

# Manual backup (before risky operations)
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_staging | gzip > /tmp/staging_$(date +%Y%m%d_%H%M).sql.gz
docker exec chatwoot_postgres pg_dump -U chatwoot chatwoot_production | gzip > /tmp/prod_$(date +%Y%m%d_%H%M).sql.gz

# Upload backup to S3
aws s3 cp /tmp/prod_*.sql.gz s3://pmg-chatwoot-backups/manual/

# Rails console (staging)
docker exec -it chatwoot-web-staging bundle exec rails console

# Rails console (production)
docker exec -it chatwoot-web-production bundle exec rails console

# Run migrations (production)
docker exec chatwoot-web-production bundle exec rails db:migrate
```

---

## 7. Logs

```bash
# Live container logs
docker logs -f chatwoot-web-staging
docker logs -f chatwoot-sidekiq-staging
docker logs -f chatwoot-web-production

# Router logs
sudo journalctl -u pmg-router -f

# CloudWatch log groups
#   /aws/chatwoot/staging/*
#   /aws/chatwoot/production/*
```

---

## 8. Systemd Units (boot auto-start)

The Docker stacks are managed by systemd units in `deployment/`. To install on a fresh host:

```bash
sudo cp deployment/chatwoot-staging-docker.service /etc/systemd/system/
sudo cp deployment/chatwoot-production-docker.service /etc/systemd/system/
sudo cp chatwoot-services/router/pmg-router.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatwoot-staging-docker chatwoot-production-docker pmg-router
```

> **Note:** The `chatwoot` user must be in the `docker` group: `sudo usermod -aG docker chatwoot`

To start/stop/status:

```bash
sudo systemctl start chatwoot-staging-docker
sudo systemctl stop chatwoot-staging-docker
sudo systemctl status chatwoot-staging-docker
```

---

## 9. Docker Network

All containers communicate over the `pmg_net` bridge network.

```bash
# Verify network and attached containers
docker network inspect pmg_net --format '{{range .Containers}}{{.Name}} {{end}}'
# Expected: chatwoot_postgres chatwoot_redis chatwoot-web-staging chatwoot-sidekiq-staging (+ production equivalents)
```

If a container is missing from the network after recreation:
```bash
docker network connect pmg_net <container_name>
```

---

## 10. WhatsApp Router (chatwoot-services)

The `pmg-router` Node.js service receives Meta webhooks and forwards to Chatwoot. It runs as a systemd service on port 3000.

Code lives in `chatwoot-services/router/` (within this repo). Deployed to `/var/www/chatwoot-services/` on EC2.

```bash
sudo systemctl status pmg-router
curl http://localhost:3000/health

# Redeploy after changes
cd /home/chatwoot/chatwoot
git pull pmg staging
bash chatwoot-services/deploy.sh
sudo systemctl restart pmg-router
```

---

## 11. Branch Strategy

```
upstream (chatwoot/chatwoot v4.11.1)
        ↓ fork
pmg-chatwoot (Padma-Medical-Group/pmg-chatwoot)
  ├── staging      — deployed to staging; base for all PMG work
  ├── develop      — integration branch; PRs merge here first
  └── main         — production branch (post go-live)
```

PMG customizations live entirely in `staging`/`develop`. Upstream merges go via `develop` to avoid clobbering PMG changes.

---

## 12. Upstream Version Upgrade

```bash
# On local machine
git fetch upstream
git checkout develop
git merge upstream/v4.x.x   # specific release tag
# Resolve conflicts — PMG changes are in: Sidebar.vue, ChatList.vue, helpers.js,
#   broadcast_from_sheet_service.rb, message_finder.rb, conversation.routes.js
git push pmg develop
# Then rebuild image on EC2 (Section 4.2)
```
