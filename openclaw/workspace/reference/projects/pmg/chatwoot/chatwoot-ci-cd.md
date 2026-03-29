# 2. CI/CD — pmg-chatwoot

**Last updated:** 15 March 2026
**Repo:** `Padma-Medical-Group/pmg-chatwoot`

---

## 2.1 Branch Strategy

| Branch | Purpose | Deploy target |
|--------|---------|---------------|
| `develop` | Integration branch. PRs merge here first. Protected — no direct push (Husky enforces locally; branch protection on GitHub). | — |
| `staging` | Deployed branch. All active work happens here. | `staging-chat.pbmcgroup.com` (port 3001) |
| `main` | Production branch. Mirrors staging after go-live. | `chat.pbmcgroup.com` (port 3002) |

Normal flow: feature branch → PR to `develop` → merge → PR `develop → staging` → merge → auto-deploy to staging. On go-live: PR `staging → main` → auto-deploy to production.

**Note on Husky:** Upstream Chatwoot installs a pre-push hook that blocks direct pushes to `develop`. This is intentional — use PRs. For admin branch sync operations, this can be bypassed with `git push --no-verify` but only when explicitly consolidating branches.

---

## 2.2 Workflows

All workflow files live in `.github/workflows/`. Six upstream workflows have been moved to `.github/workflows/disabled/` (Heroku deploy check, Docker registry publish, nightly installer, logging coverage check) — they are irrelevant to PMG's self-hosted setup.

### 2.2.1 `pmg-ci.yml` — Tests and Linting

| Trigger | Jobs |
|---------|------|
| PR opened/updated (targeting `develop`, `staging`, or `main`) | `lint-ruby` (RuboCop), `lint-js` (ESLint) |
| Push to `develop` | `lint-ruby`, `lint-js`, `specs-changed` (specs for changed files only) |
| Nightly at midnight SGT (16:00 UTC) | `nightly-backend` (full RSpec, 6 parallel nodes), `nightly-frontend` (full Jest) |
| Manual (`workflow_dispatch`) | Nightly suite on demand |

Runs on **GitHub-hosted `ubuntu-latest`** runners (CI jobs need PostgreSQL and Redis service containers).

**Changed-file spec detection:** on `develop` pushes, the workflow maps each changed `app/**/*.rb` file to its corresponding `spec/**/*_spec.rb` and runs only those. If no spec exists for a changed file, that file is skipped silently.

### 2.2.2 `pmg-deploy.yml` — Deployment

| Trigger | Jobs |
|---------|------|
| Push to `staging` | Detect changes → restart or rebuild for staging |
| Push to `main` | Detect changes → restart or rebuild for production |
| Manual (`workflow_dispatch`) | Optional `force_rebuild` boolean toggle |

Runs entirely on the **self-hosted `pmg-ec2` runner** (see §2.3). No GitHub-hosted minutes used.

**Path detection logic:**

| Changed files | Deploy path | Time |
|--------------|-------------|------|
| Ruby, config, migrations only | `deploy-restart`: git pull → db:migrate → `docker compose restart` | ~45s |
| Frontend files (`*.vue`, `*.js`, `package.json`, `pnpm-lock.yaml`, `Dockerfile`, `Gemfile`) | `deploy-rebuild`: git pull → `docker build` → tag → `--force-recreate` → db:migrate | ~25 min |
| Manual `force_rebuild: true` | Always takes rebuild path | ~25 min |

The concurrency group `deploy-${{ github.ref_name }}` ensures only one deploy runs per branch at a time — a newer push cancels a running deploy.

Health check retries every 5s for up to 60s after restart/recreate.

### 2.2.3 `pr-review.yml` — Claude Haiku Code Review

Fires after `PMG CI` completes successfully on a PR. Posts an automated review comment covering:
- Summary of changes
- Risk level (GREEN / YELLOW / RED)
- Findings (max 5)
- Recommendations
- Whether `PMG-CHANGES.md` needs updating

Uses `ANTHROPIC_API_KEY` stored as a Padma Medical Group org-level GitHub secret. Replaces its own comment on re-runs (one comment per PR).

---

## 2.3 Self-Hosted Runner

The deploy workflow runs on a GitHub Actions self-hosted runner installed on the EC2 instance.

| Property | Value |
|----------|-------|
| Location | `/opt/github-runner/` |
| Runner name | `pmg-ec2` |
| Labels | `self-hosted`, `pmg-ec2` |
| Runs as | `chatwoot` user (member of `docker` group) |
| Systemd unit | `actions.runner.Padma-Medical-Group-pmg-chatwoot.pmg-ec2.service` |
| Work directory | `/opt/github-runner/_work/` |

### Check runner status
```bash
sudo systemctl status actions.runner.Padma-Medical-Group-pmg-chatwoot.pmg-ec2
```

### Runner logs
```bash
sudo journalctl -u actions.runner.Padma-Medical-Group-pmg-chatwoot.pmg-ec2 -f
```

### Restart runner
```bash
sudo systemctl restart actions.runner.Padma-Medical-Group-pmg-chatwoot.pmg-ec2
```

### Re-register runner (if token expires)
Runner registration tokens are single-use and expire after 1 hour. If the runner needs to be re-registered:

```bash
cd /opt/github-runner
# Get a new token from: GitHub → repo Settings → Actions → Runners → New self-hosted runner
sudo -u chatwoot ./config.sh remove --token OLD_TOKEN
sudo -u chatwoot ./config.sh \
  --url https://github.com/Padma-Medical-Group/pmg-chatwoot \
  --token NEW_TOKEN \
  --name pmg-ec2 \
  --labels pmg-ec2 \
  --work /opt/github-runner/_work \
  --unattended
sudo ./svc.sh start
```

---

## 2.4 Secrets

| Secret | Scope | Used by |
|--------|-------|---------|
| `ANTHROPIC_API_KEY` | Padma Medical Group org | `pr-review.yml` — Claude Haiku review |

Deploy jobs run on the self-hosted runner and use the EC2 IAM role for all AWS access (SSM, S3, CloudWatch) — no AWS credentials stored in GitHub.

---

## 2.5 Upstream Workflows

These upstream Chatwoot workflows remain active (they run on PRs and are harmless):

| Workflow | What it does |
|----------|-------------|
| `run_foss_spec.yml` | Full upstream RSpec suite — runs on `develop`/`master` pushes and PRs |
| `frontend-fe.yml` | Frontend lint + Jest — runs on `develop` PRs |
| `run_mfa_spec.yml` | MFA-specific specs |
| `size-limit.yml` | JS bundle size check |
| `lint_pr.yml` | PR title lint |
| `auto-assign-pr.yml` | Auto-assigns PR reviewers |
| `stale.yml` | Marks stale issues/PRs |
| `test_docker_build.yml` | Verifies Dockerfile builds |

These run on GitHub-hosted runners and consume free minutes. They should not be disabled — they catch upstream regressions.
