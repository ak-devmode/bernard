---
title: Intent-Aligned Todo Capture
type: readme
---

# Intent-Aligned Todos

Incoming asks directed at Alex, scored against current priorities.

## How It Works

1. **Capture**: Stream watcher detects actionable asks in email/WhatsApp
2. **Score**: Each ask is compared against `priorities/current.md` for alignment
3. **Propose**: Entry created with status `proposed` — Alex must promote to `accepted`
4. **Surface**: Daily digest groups todos by alignment: aligned → adjacent → unrelated

## Status Lifecycle

- `proposed` — captured, awaiting Alex review
- `accepted` — Alex promoted to active
- `deferred` — not now, resurface on specified date
- `dismissed` — Alex explicitly declined
- `done` — completed

## File Naming

`{topic-slug}-{date}.md` — e.g., `board-deck-review-2026-03-29.md`
