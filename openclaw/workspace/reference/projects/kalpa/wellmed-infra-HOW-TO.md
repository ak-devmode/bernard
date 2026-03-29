# How-To: New Repo Bootstrap

**Version:** 1.0
**Date:** 02 March 2026
**Maintained by:** Alex

---

# 1. Overview

1.1.1 The `bootstrap-repo.sh` script brings a new Kalpa-health GitHub repo up to org standard in a single command: creates the three-branch structure (main / staging / develop), pushes the CI workflow templates, and applies branch protection rules that mirror `wellmed-gateway-go`.

1.1.2 All configuration is version-controlled in `infrastructure/templates/`. When the standard changes — new workflow, different approval counts, Go version bump — update the template and re-run the script against any repo that needs it. The script is idempotent: safe to run multiple times.

---

# 2. Prerequisites

## 2.1 Required Tools

2.1.1 `gh` CLI installed — https://cli.github.com

2.1.2 Authenticated to the Kalpa-health org:

```bash
gh auth login
gh auth status   # should show: Logged in to github.com account <your-username>
```

2.1.3 Admin or write access to the target repo. If you created the repo, you have this.

## 2.2 The Target Repo Must Exist

2.2.1 The script configures an existing repo — it does not create one. Create the repo on GitHub first (private, no template, default branch: main), then run the bootstrap.

---

# 3. Running the Bootstrap

## 3.1 Dry Run First

3.1.1 Always preview before executing. The `--dry-run` flag prints every action without making any changes:

```bash
cd ~/Projects/WellMed/infrastructure/scripts
./bootstrap-repo.sh Kalpa-health/<repo-name> --dry-run
```

## 3.2 Basic Usage

3.2.1 For a standard Go repo with a single `./cmd` entry point:

```bash
./bootstrap-repo.sh Kalpa-health/<repo-name>
```

3.2.2 The binary name defaults to the repo name with the `wellmed-` prefix stripped. For `wellmed-backbone`, the output binary becomes `bin/backbone`.

## 3.3 Options Reference

| Flag | Default | When to Override |
|------|---------|-----------------|
| `--go-version VERSION` | `1.25.6` | Repo uses a different Go version in go.mod |
| `--binary-name NAME` | repo name minus `wellmed-` | Binary name doesn't match the repo name convention |
| `--cmd-path PATH` | `./cmd` | Entry point is not at `./cmd` (e.g., `./cmd/server`) |
| `--reviewer USERNAME` | `hamzahnafalahkalpa` | Different required reviewer for this repo |
| `--dry-run` | off | Preview all actions without touching anything |

3.3.1 Example with custom options:

```bash
./bootstrap-repo.sh Kalpa-health/wellmed-new-service \
  --binary-name new-service \
  --cmd-path ./cmd/server
```

---

# 4. What the Script Does

4.1.1 The script runs three steps in sequence:

```
Step 1: Branches
  ├── Fetch SHA of main
  ├── Create develop (from main)
  └── Create staging (from main)

Step 2: Workflow files (pushed to main via GitHub Contents API)
  ├── .github/workflows/ci.yml
  ├── .github/workflows/main-approval-check.yml
  └── .github/workflows/pr-review.yml

Step 3: Branch protection
  ├── main    — 2 approvals required, enforce_admins: true
  ├── staging — 2 approvals required, enforce_admins: false
  └── develop — 1 approval required,  enforce_admins: false
```

4.1.2 All three branches require CI status checks (Lint, Unit Test, Build) to pass before merge. These correspond exactly to the job names in `ci.yml`.

---

# 5. Post-Bootstrap Steps

5.1.1 The script prints a "Next steps" summary when it finishes. Two actions are always required:

## 5.1 Update the Architecture Context

5.1.1 The Claude PR review workflow ships with a placeholder architecture section marked `TODO:ARCH`. The AI review is only useful if this section accurately describes the repo — data flow, module structure, auth approach.

5.1.2 Edit `.github/workflows/pr-review.yml` in the newly bootstrapped repo, search for `TODO:ARCH`, and replace the placeholder with the repo's actual architecture. See `wellmed-gateway-go/.github/workflows/pr-review.yml` for a complete example.

## 5.2 Anthropic API Key Secret

5.2.1 The Claude review workflow requires `ANTHROPIC_API_KEY`. This is now managed as an **org-level secret** with `--visibility all`, so it is automatically available to every Kalpa-health repo — including newly bootstrapped ones. No per-repo action is needed.

5.2.2 If you ever need to rotate the key, update it once at the org level:

```bash
gh secret set ANTHROPIC_API_KEY --org Kalpa-health --visibility all
# gh will prompt: Paste your secret — key is never echoed to the terminal
```

5.2.3 To store the key locally for reference (e.g. for local scripts or Claude CLI), use macOS Keychain — never a plaintext file:

```bash
# Store (prompts for key without echoing it)
read -rs ANTHROPIC_KEY && security add-generic-password \
  -s "anthropic-api-key" -a "kalpa-health" -w "$ANTHROPIC_KEY" && unset ANTHROPIC_KEY

# Retrieve (e.g. in a local script)
security find-generic-password -s "anthropic-api-key" -a "kalpa-health" -w
```

---

# 6. Updating the Org Standard

6.1.1 The templates in `infrastructure/templates/workflows/` are the source of truth for what every Kalpa-health repo looks like. When the standard changes, update the template — not the downstream repos directly.

6.1.2 To re-apply the updated standard to an existing repo, run the script again. Existing branches are skipped, workflow files are updated in-place, and branch protection rules are overwritten to the current standard.

6.1.3 The approval counts and `enforce_admins` flags are hardcoded in `bootstrap-repo.sh` inside the `apply_protection` calls — not in a template file. When those change, update the script directly.

---

# 7. Future: Infrastructure as Its Own Repo

7.1.1 The `infrastructure/` folder currently lives as a local directory rather than a standalone GitHub repo. As the org grows past ~5 services and adds Terraform or environment configuration, it should become its own repo: `Kalpa-health/wellmed-infrastructure`. The bootstrap script should be the first thing run against it — proof the tooling works on itself.

7.1.2 Pending actions:

- [ ] 7.1.2.1 Create `Kalpa-health/wellmed-infrastructure` on GitHub — @Alex
- [ ] 7.1.2.2 Run `./bootstrap-repo.sh Kalpa-health/wellmed-infrastructure` to apply org standards — @Alex
- [ ] 7.1.2.3 Update cross-references in `kalpa-docs` from local path to `wellmed-infrastructure` repo — @Alex

---

# Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 02 Mar 2026 | Alex + Claude | Initial version. Covers prerequisites, usage, options, post-bootstrap steps, and the infrastructure-as-own-repo recommendation. |
