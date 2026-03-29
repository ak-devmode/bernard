# SSM Secret Management Plan — WellMed

**Version:** 1.1
**Date:** 04 March 2026
**Previous Version:** 1.0 (04 March 2026) — initial plan
**Maintained by:** Alex

### Key Changes v1.0 → v1.1
- Added ECS transition context throughout — this plan is explicitly a transitional step, not the end state
- Added Section 7: Documentation, Testing, and ECS Handoff — final stage of implementation with items to revisit during ECS migration

---

# 1. Decision Summary

1.1 **This plan is a transitional step.** The current state is naked secrets in `.env` files on VMs. The end state is ECS with IAM task roles, no VM-based deployments, and no static credentials anywhere. This plan moves the team from current state to a safe intermediate state — secrets in SSM, services pulling at startup — that is fully compatible with ECS and requires minimal rework during that migration. Items to revisit during ECS migration are explicitly flagged throughout and consolidated in Section 7.

1.2 All secrets (database passwords, JWT secrets, API keys, service-to-service keys) are stored in AWS SSM Parameter Store as `SecureString`. No secrets live in `.env` files on VMs or in Docker images at any environment.

1.2 Non-secret config (ports, log levels, feature flags, region, SSM path prefix) continues to be managed via `.env` files or environment variables in ECS task definitions. These contain no credentials.

1.3 Each Go service pulls its own secrets from SSM at startup using the AWS SDK, scoped to its own SSM prefix plus the shared prefix. No service reads another service's parameters.

1.4 SSM Parameter Store is chosen over AWS Secrets Manager. Secrets Manager costs ~$0.40/secret/month and is designed for automated rotation workflows not yet needed. SSM SecureString is effectively free at current scale and sufficient for the rotation model described in Section 4.

1.5 The ADR for this decision is tracked in Section 6. Claude Code writes it in sequence after existing queued ADRs (ADR-001, ADR-002, ADR-003).

---

# 2. SSM Path Hierarchy

2.1 The established path convention is `/wellmed/{env}/{service}/{KEY}` for service-specific parameters and `/wellmed/{env}/shared/{KEY}` for parameters shared across services.

2.2 Valid values for `{env}` are `staging` and `production`. Dev environment uses local `.env` files only — no SSM dependency for local development.

2.3 Valid values for `{service}` are the service names as they appear in the WellMed service registry (gateway, backbone, emr, cashier, etc.). New services follow the same pattern — no exceptions.

2.4 The shared prefix currently holds `BACKBONE_SERVICE_KEY` only. As new shared secrets are identified (e.g., a common RabbitMQ credential, ElasticSearch auth), they are added to shared rather than duplicated per service.

```
/wellmed/
  staging/
    shared/
      BACKBONE_SERVICE_KEY
    gateway/
      DB_HOST, DB_PASSWORD, JWT_SESSION_TOKEN_SECRET, ...
    backbone/
      DB_HOST, DB_PASSWORD, JWT_SECRET_KEY, ...
    emr/
      ...
  production/
    shared/
      BACKBONE_SERVICE_KEY
    gateway/
      ...
    backbone/
      ...
```

---

# 3. Implementation Tasks

## 3.1 Audit Existing SSM Pull Pattern in Gateway

3.1.1 Objective: Confirm the existing `BACKBONE_SERVICE_KEY` SSM pull in the gateway service is using the correct pattern before replicating it across all secrets.

```
  [ ] 3.1.1 Locate the existing SSM pull code in wellmed-gateway-go — @Alex
  [ ] 3.1.2 Verify it uses GetParametersByPath (batch pull by prefix), not individual GetParameter calls — @Alex
  [ ] 3.1.3 Verify it pulls at startup (main.go or application init), not per-request — @Alex
  [ ] 3.1.4 Verify it uses WithDecryption: true for SecureString params — @Alex
  [ ] 3.1.5 If any of the above are wrong, correct the pattern before proceeding to 3.2 — @Alex
```

Acceptance criteria: a single startup call pulls all secrets for the service prefix + shared prefix in one SDK call. No per-request SSM calls. No plaintext SecureString values in logs.

## 3.2 Extend Gateway to Pull All Secrets from SSM

3.2.1 Objective: Replace all remaining secrets currently read from environment variables in the gateway with SSM-sourced values at startup.

```
  [ ] 3.2.1 Map every secret in parameters/gateway.json to its current env var name in the gateway codebase — @Alex
  [ ] 3.2.2 Identify which gateway secrets are currently in naked .env files on VMs — @Alex
  [ ] 3.2.3 Update gateway startup to pull full service prefix + shared prefix via GetParametersByPath — @Alex (depends on 3.1)
  [ ] 3.2.4 Remove secret env vars from gateway .env file, leaving only non-secret config — @Alex
  [ ] 3.2.5 Test on staging: confirm gateway starts, authenticates, and routes correctly with no .env secrets — @Alex
  [ ] 3.2.6 Deploy to production — @Alex (depends on 3.2.5)
```

Acceptance criteria: gateway `.env` contains zero secrets. All SecureString params are loaded from SSM. Service starts cleanly in staging and production.

## 3.3 Extend Backbone to Pull All Secrets from SSM

3.3.1 Objective: Same as 3.2 but for the backbone service. Backbone has additional complexity — RabbitMQ URL and exchange name have PENDING items (confirm with Hamzah before values are set).

```
  [ ] 3.3.1 Confirm RABBITMQ_URL format and RABBITMQ_EXCHANGE name with Hamzah — @Alex (blocks 3.3.3)
  [ ] 3.3.2 Confirm RABBITMQ_EXCHANGE is read from env in application.go (currently may be hardcoded — see backbone.json note) — @Alex
  [ ] 3.3.3 Map every secret in parameters/backbone.json to its current env var name in backbone codebase — @Alex
  [ ] 3.3.4 Update backbone startup to pull full service prefix + shared prefix — @Alex (depends on 3.1, 3.3.1, 3.3.2)
  [ ] 3.3.5 Remove secret env vars from backbone .env file — @Alex
  [ ] 3.3.6 For now, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in SSM as SecureString — @Alex / @Hamzah (revisit during ECS migration: task role replaces these entirely, see Section 7)
  [ ] 3.3.7 Test on staging, then deploy to production — @Alex
```

Acceptance criteria: backbone `.env` contains zero secrets. RABBITMQ_EXCHANGE is env-driven, not hardcoded. IAM task role decision documented.

## 3.4 Establish Pattern for Remaining Services (EMR, Cashier, etc.)

3.4.1 Objective: Document the standard pattern so future services implement SSM pull correctly from day one, without needing Alex to review each one.

```
  [ ] 3.4.1 Write a shared Go package (e.g., /pkg/config or /pkg/ssm) that wraps GetParametersByPath and returns a map[string]string — @Alex (depends on 3.1)
  [ ] 3.4.2 Add the package to kalpa-docs development/conventions.md as the mandated pattern for all services — @Alex
  [ ] 3.4.3 Create parameters/{service}.json manifest stubs for emr, cashier, and any other active services — @TBD
  [ ] 3.4.4 Add SSM pull bootstrap to each new service as it is created, using the shared package — @TBD
```

Acceptance criteria: any new service can implement SSM pull by importing the shared package and passing its service prefix. No copy-paste of SDK boilerplate between services.

## 3.5 Populate Staging SSM Values

3.5.1 Objective: Ensure all REPLACE_ME values in staging are set before 3.2 and 3.3 tests run.

```
  [ ] 3.5.1 Run sync.sh --env staging --service gateway --dry-run and review output — @Alex
  [ ] 3.5.2 Set all REPLACE_ME values for staging gateway manually via AWS console or aws ssm put-parameter — @Alex / @Hamzah
  [ ] 3.5.3 Run sync.sh --env staging --service backbone --dry-run and review output — @Alex
  [ ] 3.5.4 Set all REPLACE_ME values for staging backbone — @Alex / @Hamzah
  [ ] 3.5.5 Run pull.sh --env staging --service gateway and verify output is complete with no blank values — @Alex
  [ ] 3.5.6 Run pull.sh --env staging --service backbone and verify — @Alex
```

Acceptance criteria: pull.sh for both services returns a complete, non-blank .env file with no REPLACE_ME values remaining.

## 3.6 Verify IAM Permissions

3.6.1 Objective: Confirm that the IAM roles attached to staging and production VMs / ECS tasks have the minimum required SSM permissions.

```
  [ ] 3.6.1 Confirm IAM policy includes ssm:GetParametersByPath on arn:aws:ssm:ap-southeast-1:*:parameter/wellmed/* — @Alex / @Hamzah
  [ ] 3.6.2 Confirm IAM policy includes ssm:GetParameters and kms:Decrypt for SecureString decryption — @Alex / @Hamzah
  [ ] 3.6.3 Verify no service has broader SSM access than its own prefix + shared (principle of least privilege) — @Hamzah
  [ ] 3.6.4 Document the IAM policy in wellmed-infrastructure repo — @Hamzah
```

Acceptance criteria: services can pull their own parameters. No service can read another service's SecureString values. Policy is documented in infra repo.

---

# 4. Key Rotation Procedure

4.1 Because each service pulls secrets at startup, rotation requires: (1) update the SSM parameter, (2) restart only the affected service. No other services are touched unless the rotated secret is in `/shared/`.

4.2 For shared secrets (currently `BACKBONE_SERVICE_KEY`): both gateway and backbone must be restarted after rotation, coordinated to avoid a window where one service has the new key and the other has the old. Restart backbone first (it validates the key), then gateway (it sends the key).

4.3 For database passwords: update SSM, then restart the service that owns that DB connection. Other services are unaffected.

4.4 There is no automated rotation configured at this time. All rotation is manual via AWS console or `aws ssm put-parameter --overwrite`. This is acceptable at current scale.

---

# 5. Local Development

5.1 Developers do not pull from SSM for local dev. The pull.sh script generates `.env.{env}.{service}` files that are copied to the service root as `.env` for local use.

5.2 These generated files are gitignored and treated as ephemeral. They are not committed, not deployed, and not the source of truth — SSM is.

5.3 A local dev `.env` may contain placeholder values for secrets that are not needed to run the service locally (e.g., production S3 bucket). Document acceptable local placeholder values in development/setup.md.

5.5 **ECS revisit:** Once ECS is running, non-secret config (ports, log level, APP_ENV, SSM_PATH_PREFIX) moves from VM `.env` files into ECS task definitions as plain environment variables. The `.env` files on VMs become irrelevant. pull.sh remains useful for local dev only. See Section 7.

---

# 6. ADR

6.1 This decision requires an ADR. Claude Code writes it as ADR-004 (next in sequence after ADR-003 in kalpa-docs/adrs/).

6.2 ADR title: **ADR-004 — Secret Management via AWS SSM Parameter Store**

6.3 ADR content scope:
- Decision: SSM Parameter Store (SecureString) for all secrets, not env files and not Secrets Manager
- Context: naked secrets on VMs, team concern about per-service env file complexity, multi-service growth to 18+
- Alternatives considered: (1) per-service .env files — rejected due to rotation complexity and mismatch risk; (2) single master .env per VM — rejected due to forced full-restart on any rotation and false coupling of unrelated services; (3) AWS Secrets Manager — rejected as overkill at current scale (~$0.40/secret/month, rotation automation not needed)
- Consequences: services require IAM role with SSM read access; local dev uses pull.sh-generated files; startup time increases slightly for SSM SDK call (acceptable); all secrets auditable in one place per environment

```
  [ ] 6.3.1 Claude Code writes ADR-004 using ADR-000-template.md as base — @Alex (CC)
  [ ] 6.3.2 Alex reviews and approves — @Alex
  [ ] 6.3.3 Merge to kalpa-docs main — @Alex
```

---

# 7. Documentation, Testing, and ECS Handoff

## 7.1 Documentation

7.1.1 Objective: Record what was built, why, and what needs revisiting — so the ECS migration doesn't rediscover these decisions from scratch.

```
  [ ] 7.1.1 Update development/setup.md with local dev workflow — how to use pull.sh, acceptable placeholder values for secrets not needed locally — @Alex
  [ ] 7.1.2 Update operations/incident-response.md with key rotation runbook — SSM update procedure, restart order for shared secrets (backbone first, then gateway) — @Alex
  [ ] 7.1.3 Add SSM path hierarchy and parameter manifest convention to development/conventions.md — @Alex
  [ ] 7.1.4 Merge ADR-004 to kalpa-docs (depends on Section 6 tasks) — @Alex
```

## 7.2 Testing

7.2.1 Objective: Confirm the full SSM pull flow works end-to-end in staging before production cutover.

```
  [ ] 7.2.1 Start gateway cold in staging with no .env secrets — confirm clean startup and SSM pull in logs — @Alex
  [ ] 7.2.2 Start backbone cold in staging with no .env secrets — confirm clean startup — @Alex
  [ ] 7.2.3 Run an authenticated request end-to-end (login → JWT → gRPC to backbone) to confirm BACKBONE_SERVICE_KEY shared secret is working — @Alex
  [ ] 7.2.4 Deliberately set a wrong SSM value and confirm the service fails loudly at startup, not silently at runtime — @Alex
  [ ] 7.2.5 Confirm no SSM values appear in CloudWatch logs (check for accidental secret logging in startup output) — @Alex
```

Acceptance criteria: both services start cleanly from SSM alone in staging. Errors surface at startup, not mid-request. No secrets visible in logs.

## 7.3 ECS Handoff — Items to Revisit

7.3.1 This section is a parking lot. These items are deliberately deferred — they are not blockers for this plan but must not be forgotten when ECS migration begins.

7.3.2 **Drop static AWS credentials.** `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set in SSM as a transitional measure (see 3.3.6). When ECS is running with an IAM task role that has S3 and SSM permissions, these two parameters are deleted from SSM and removed from the parameter manifests entirely. This is the correct end state.

7.3.3 **Move non-secret config to ECS task definitions.** Non-secret environment variables (ports, log level, APP_ENV, SSM_PATH_PREFIX, region) currently live in VM `.env` files. In ECS these move to the task definition as plain `environment` entries. VM `.env` files are retired.

7.3.4 **Verify IAM task role scope per service.** Each ECS service should run under its own task role scoped to only its SSM prefix plus shared. The current IAM setup (see 3.6) covers VM-based access — confirm task role policies replicate the same least-privilege boundaries during ECS setup.

7.3.5 **Review sync.sh and pull.sh relevance.** pull.sh remains useful for local dev indefinitely. sync.sh (which pushes manifest values to SSM) remains the right tool for populating parameters regardless of runtime environment. No changes expected, but confirm both scripts work from a developer Mac against the ECS-era SSM structure.

---

# Edit Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 04 Mar 2026 | Alex + Claude | Initial plan. Covers decision rationale, SSM path hierarchy, implementation tasks for gateway and backbone, shared package pattern, rotation procedure, local dev model, and ADR stub. |
| 1.1 | 04 Mar 2026 | Alex + Claude | Added ECS transition framing to Section 1 and throughout. Added Section 7: Documentation, Testing, and ECS Handoff with explicit parking lot of items to revisit during ECS migration. |
