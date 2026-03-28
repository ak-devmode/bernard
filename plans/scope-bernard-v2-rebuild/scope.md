# Bernard v2 Rebuild — Functional Revival

**Project:** Bernard (ak-devmode/bernard)  **Branch:** main  **Date:** 2026-03-28
**Scope folder:** plans/scope-bernard-v2-rebuild/
**Source repo(s):** /Users/alexknecht/Projects/bernard
**Server:** 54.254.76.94 (SSH as ubuntu, bernard user, OpenClaw at /home/bernard/.openclaw/)

## Context

Bernard v1 (Feb 2026) failed due to no feedback loop, wrong model tier, voice added too early, and no vault. Server hardening and OpenClaw installation are complete. This scope covers the functional rebuild: identity, vault, learning loop, digest quality, ingestion pipeline, CC dispatch, and Padma Care community intelligence engine. PRD: `bernard-master-plan-v2`.

## Phases

### Phase 1 — Foundation & Config
Upgrade OpenClaw to latest stable, run doctor, disable voice (ElevenLabs + Whisper), set budget cap, verify heartbeat at 3hr, update openclaw.json with model routing tiers (Sonnet primary, Haiku for heartbeat/ack), initialize vault directory structure on server.
**Done when:** openclaw.json reflects v2 config, voice disabled, vault dirs exist, OC on latest stable.

### Phase 2 — Identity & Learning Loop
Rewrite SOUL.md v2 (wise uncle + Telegram code formatting rules), seed FEEDBACK.md with v1 failure modes, create MEMORY.md, update AGENTS.md with security spine from PRD §3, codify authority classes and red lines.
**Done when:** All workspace identity files reflect v2 PRD. FEEDBACK.md has ≥5 seeded corrections.

### Phase 3 — Vault & QMD
Build full vault architecture (knowledge/people, projects, priorities, principles, ideas, comms, artifacts). Configure QMD backend (research if built-in or separate install). Write daily curation loop template. Update USER.md and HEARTBEAT.md to reference vault. Pre-populate project files, Padma Care voice docs. Templates for sensitive (people, contacts).
**Done when:** Vault structure on server, QMD configured and indexing, curation loop template ready.

### Phase 4 — Digest & Phase 2 Skills
Build daily digest template (top 3 priorities, dropped balls, 1 relationship nudge, 1 whimsy item — terse prose, voice-ready, no bullets). Create skill templates for: dropped ball tracking, board meeting topic accumulator, staff check-in accountability, Narawangsa pricing heuristic, house project ledger.
**Done when:** Digest template in workspace, 5 skill files created with instructions Bernard can follow.

### Phase 5 — Ingestion Pipeline
Define email + WA criteria lists in USER.md. Build summarization + PII strip pipeline for email and WA/Chatwoot. Implement ContextEngine afterTurn hook for automatic FEEDBACK.md writes. First vault ingestion test.
**Done when:** Pipeline scripts in tools/, afterTurn hook configured, test ingestion produces clean vault entry.

### Phase 6 — CC Dispatch (ACP Bridge)
Install Claude Code on server. Install acpx. Wire ACP dispatch into Bernard. Test with summarization task. Test PR creation end-to-end. Configure approval gate for destructive operations. Set up JSONL logging.
**Done when:** `acpx openclaw exec` works, approval gate tested, logging active.

### Phase 7 — Padma Care Community Engine
Codify Padma Care voice in vault (voice.md). Document free/paid line (free-paid-line.md). Set up community monitoring template and platform list. Create response drafting templates (4 response types). Build pipeline tracking (community-pipeline.md) and content flywheel (content-queue.md). SEO basics checklist for padmacare.pbmcgroup.com.
**Done when:** All Padma Care knowledge files in vault, monitoring template ready, SEO checklist complete.

## Architecture

```
Local repo (this machine)          Server (54.254.76.94)
├── openclaw/                      /home/bernard/.openclaw/
│   ├── workspace/  ──rsync──►     ├── workspace/
│   │   ├── SOUL.md                │   ├── SOUL.md
│   │   ├── FEEDBACK.md            │   ├── FEEDBACK.md
│   │   ├── MEMORY.md              │   ├── MEMORY.md
│   │   ├── knowledge/             │   ├── knowledge/  ◄── QMD indexes this
│   │   └── ...                    │   └── ...
│   └── openclaw.json              ├── openclaw.json
├── tools/                         ├── tools/ (ingestion pipelines)
├── infra/                         └── .env (secrets)
└── plans/
    └── scope-bernard-v2-rebuild/
```

## What Already Exists

- `openclaw/workspace/SOUL.md` — v1 soul, needs rewrite (terse British PA persona)
- `openclaw/workspace/IDENTITY.md` — basic identity, good foundation to build on
- `openclaw/workspace/USER.md` — stub with roles and tools
- `openclaw/workspace/HEARTBEAT.md` — basic heartbeat instructions
- `openclaw/workspace/AGENTS.md` — basic operating rules
- `openclaw/openclaw.json` — working config with OpenRouter, Telegram, ElevenLabs TTS, Whisper
- `infra/setup.sh` — bootstrap script (creates bernard user, installs Node, OpenClaw, Whisper)
- `infra/update.sh` — version-pinned update script
- `infra/env.example` — env var template

## NOT in Scope

- **Phase 5 Voice** (PRD §9) — blocked by voice readiness gate (2 weeks useful digests)
- **Gateway/Control UI evaluation** (PRD §8) — manual testing, not scriptable
- **Dedicated Padma Care agent spin-out** (PRD §10.9) — future milestone
- **Phase 4+ aspirational skills** (PRD §11) — Sentry triage, CI/CD reports, competitive intel, etc.
- **Server hardening** — already complete from v1 setup plan
- **WhatsApp channel** — commented out in PRD, revisit if Telegram becomes a barrier

## Skill Sequence

| # | Skill | Apply? | When | Notes |
|---|-------|--------|------|-------|
| 1 | /plan-ceo-review | [ ] **ALWAYS** | 1st | Challenge: is the 7-phase sequence right? Should Padma Care start earlier? |
| 2 | /plan-eng-review | [ ] YES | 2nd | Architecture: vault structure, QMD config, ingestion pipeline, ACP bridge |
| 3 | /plan-design-review | [N/A] | — | No UI component — all workspace files and server config |
| 4 | /review | [ ] YES | After each plan | Review workspace file quality before deploying to server |
| 5 | /ship | [ ] YES | After Plans 1-3 | Commit foundation changes to repo |
| 6 | /qa | [N/A] | — | No browser UI to test |
| 7 | /qa-only | [N/A] | — | No test suite — validation is behavioral (Bernard's output quality) |
| 8 | /browse | [N/A] | — | No web UI except Plan 7 SEO (manual) |
| 9 | /design-consultation | [N/A] | — | No UI design needed |
| 10 | /design-review | [N/A] | — | No UI to audit |
| 11 | /qa-design-review | [N/A] | — | No UI |
| 12 | /setup-browser-cookies | [N/A] | — | No authenticated browser sessions |
| 13 | /document-release | [ ] YES | After Plan 3 | Update CLAUDE.md to reflect v2 architecture |
| 14 | /retro | [ ] OPTIONAL | After Plans 1-3 | Evaluate if foundation is solid before proceeding to Phase 2 skills |

## Key Decisions Captured

- CC can SSH directly into server — plans include live SSH commands, user approves as they come
- OpenClaw version unknown — Plan 1 includes version check + conditional upgrade
- Padma Care site live at padmacare.pbmcgroup.com — SEO tasks are real, not stubs
- Claude Code not on server — Plan 6 includes CC installation as prerequisite
- Vault seeding: mix approach — templates for sensitive (people, contacts), pre-populate for projects, principles, Padma Care voice docs
- QMD: unknown if built-in or separate — Plan 3 researches and handles either case
- All 7 plans generated upfront, user runs /plan at their own pace
- Voice (ElevenLabs/Whisper) stays disabled until voice readiness gate passed (2 weeks useful digests)
