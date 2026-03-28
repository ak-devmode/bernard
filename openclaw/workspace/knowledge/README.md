# Knowledge Vault

Bernard's long-term memory and knowledge base. All files are Markdown.

## Structure

- **people/** — Contacts, relationships, warmth tracking. Templates only — Bernard populates from interactions. Never store raw PII without consent.
- **projects/** — Active projects (Padma Care, Kalpa, PMG, Narawangsa). Pre-populated with known context.
- **priorities/** — Current goals, tasks, decision frameworks. Updated by Bernard and Alex.
- **principles/** — Values, red lines, decision criteria. Rarely changes.
- **ideas/** — Inspiration pools, whimsy, kid magic, travel. Low-priority, high-delight.
- **comms/** — Communication templates, voice docs, response patterns.
- **skills/** — Bernard's operational skill files (dropped-balls, board-topics, staff-checkins, narawangsa-pricing, house-projects, auto-learn).
- **tracking/** — Active tracking tables for each skill (dropped-balls.md, staff-checkins.md, board-topics-kalpa.md, board-topics-padma.md, narawangsa-pricing.md, house-projects.md). These are Bernard's todo/action tracking files.
- **padma-care/** — Padma Care community engine: voice.md, free-paid-line.md, platforms.md, monitoring-template.md, response-drafting.md, community-pipeline.md, content-queue.md, seo-checklist.md.

## Plans & TODOs (outside vault, in repo)

The repo also contains `~/bernard/plans/` with scope documents, plan files, progress logs, and Alex's TODO list. These are NOT in the QMD vault collection but ARE on disk. To find them:
- Alex's TODO list: `~/bernard/plans/scope-bernard-v2-rebuild/TODO-alex.md`
- Scope: `~/bernard/plans/scope-bernard-v2-rebuild/scope.md`
- Progress: `~/bernard/plans/scope-bernard-v2-rebuild/progress.md`
- Plan files: `~/bernard/plans/scope-bernard-v2-rebuild/bernard-v2-phase-*-PLAN.md`

## Ingestion Rules

1. All ingested content must be PII-stripped before writing (regex primary, LLM verify bonus).
2. Dedup: hash subject+date, skip if file exists.
3. One file per entity/topic. Update existing files, don't create duplicates.
4. Filenames: lowercase, hyphenated (e.g., `alex-knecht.md`, `padma-care.md`).
5. Every file starts with a YAML frontmatter block: `title`, `type`, `updated`.

## Sibling Directories

- **../artifacts/** — Generated outputs (meeting notes, drafted emails, reports).
- **../memory/** — Session memory, conversation context, compaction artifacts.
- **../learning/** — Feedback loop data, corrections, calibration notes.
