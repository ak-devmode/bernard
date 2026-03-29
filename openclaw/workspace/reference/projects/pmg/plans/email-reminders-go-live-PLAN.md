# Email Reminders Go-Live Plan
**Project:** PMG / padma-integrations
**Branch:** develop
**Date:** 2026-03-22
**Source repo:** ~/Projects/pmg/padma-integrations

## 1. Context

The auth-retry cron and SES email system are **fully built** but not yet live.
Code exists for: auth-retry.js (12-72hr reminder schedule), ses.js (SES sender
with template interpolation), two HTML email templates, and SES initialization
in the connector manifest.

**What's blocking go-live:**
1. Possibly missing SSM params (`ses_from_address`, `xendit_callback_token`)
2. Templates live in the repo — need to decide if that's acceptable or if they
   should be externalized for non-deploy editing
3. PR #22 not yet merged to main (deploy branch)

**What the old Zoho version did:**
- Sent reminder emails every 12 hours for 72 hours when a member hadn't completed
  card authorization
- Recreated payment URLs when they expired (every 24hrs)
- Abandoned after 72hrs and alerted the team

The Node.js version replicates this exactly — it just needs to be unblocked.

## 2. Tasks

### 2.1 Verify SSM Parameters [ ] HUMAN
Re-authenticate AWS (`aws sso login` or equivalent), then verify these two params exist:
```bash
aws ssm get-parameter --name "/pmg/integrations/ses_from_address" --region ap-southeast-1
aws ssm get-parameter --name "/pmg/integrations/xendit_callback_token" --region ap-southeast-1
```
- If `ses_from_address` is missing: create it with the desired From: address
  (e.g., `noreply@pbmcgroup.com` or `padmacare@pbmcgroup.com`)
- If `xendit_callback_token` is missing: get from Xendit dashboard → Settings → Callbacks,
  then create the SSM param
- Both should be type `SecureString`

### 2.2 Decide Template Location [ ] CHECKPOINT
**Current state:** Templates are HTML files at `integrations/padmacare-signup/templates/`.
Loaded from disk at runtime via `ses.renderTemplate()`. Changes require commit + deploy.

**Options:**
- **A) Keep in repo (current)** — Version controlled, reviewed in PRs, deployed with code.
  To edit: change HTML, commit, push to main. Deploy is automatic (GH Actions → systemd).
  Best for: content that rarely changes, team that's comfortable with git.
- **B) Move to S3** — Upload templates to S3 bucket, load at startup or per-send.
  To edit: upload new HTML to S3, no deploy needed. Adds S3 dependency + IAM permissions.
  Best for: frequently changing content, non-technical editors.
- **C) SES Templates** — Use AWS SES template system. Edit via AWS console or CLI.
  Limited: max 500 templates, 500KB each, less flexible than raw HTML.
  Best for: simple templates managed by ops.

**Recommendation:** A (keep in repo). The deploy is automatic — push to main and it's
live in ~60 seconds. Template changes are rare (wording, not logic). Version control
is a feature, not a bug. If you need non-git editing later, S3 is an easy migration.

### 2.3 Review & Polish Email Templates [ ]
Read both templates and confirm:
- Branding/voice matches Padma Care tone
- Contact email (`padmacare@pbmcgroup.com`) is correct
- CTA buttons and wording are appropriate
- Subject lines are good: "Complete Your Padma Care Payment Authorization"
  and "New Payment Link — Padma Care Membership"
- Consider adding: Padma Care logo, unsubscribe note, footer with address

**Files:**
- `integrations/padmacare-signup/templates/reminder-email.html`
- `integrations/padmacare-signup/templates/new-url-email.html`

### 2.4 Test Email Delivery End-to-End [ ]
With SSM params in place, test the full flow:
1. SSH to pmg-chatwoot and check service health:
   ```bash
   curl -s http://localhost:3012/health
   sudo journalctl -u padma-integrations --since "10 min ago" | grep -i ses
   ```
2. Verify SES can send from the configured address:
   ```bash
   aws ses send-email --from "FROM_ADDRESS" --to "YOUR_EMAIL" \
     --subject "Test" --text "SES test from padma-integrations" \
     --region ap-southeast-1
   ```
3. If possible, trigger a test signup through Jotform with a test email,
   then wait 12hrs (or temporarily lower the threshold for testing)

### 2.5 Merge PR #22 [ ]
Once SSM params are confirmed and templates are approved:
```bash
gh pr merge 22 --squash
```
This deploys automatically via GitHub Actions → systemd restart.

### 2.6 Verify Auth-Retry Cron Running [ ]
After deploy, confirm the cron is executing:
```bash
ssh pmg-chatwoot "sudo journalctl -u padma-integrations --since '15 min ago' | grep 'Auth retry'"
```
Expected: `Auth retry: no active records found` (if no pending signups) or
`Auth retry: checking active records` (if there are pending ones).

### 2.7 Update TODOS.md [ ]
Mark the reminder email items as complete. Update the SSM param items.

## 3. Not in Scope
- Redis state persistence (deferred)
- Xendit payment webhook migration (separate task, medium priority)
- Make.com cutover (needs web dev for redirect)
- Template externalization to S3 (only if repo-based templates prove insufficient)

## 4. Success Criteria
- [ ] SES sends emails from the configured From: address
- [ ] Auth-retry cron runs every 10 min and processes stale records
- [ ] Reminder emails go out at 12hr, 36hr, 60hr thresholds
- [ ] New payment URLs generated at 24hr, 48hr thresholds
- [ ] Abandoned records get SNS alert at 72hr
- [ ] Templates are editable and the edit path is clear
