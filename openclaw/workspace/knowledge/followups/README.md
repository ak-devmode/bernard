---
title: Follow-Up Tracker
type: readme
---

# Follow-Up Tracker

Tracks requests Alex has sent to people, so nothing falls through the cracks.

## How It Works

1. **Capture**: When Alex sends a request via WhatsApp (or tells Bernard about one), an entry is created here
2. **Surface**: Daily digest shows waiting follow-ups, ordered by age, flagging overdue items
3. **Close**: Alex marks entries as closed when resolved, or Bernard detects a response via ingestion

## Status Lifecycle

- `waiting` — request sent, no response yet
- `responded` — contact replied (detected by ingestion pipeline)
- `closed` — task is done or Alex manually closed
- `stale` — 14+ days with no action; flagged once then dropped from digest

## File Naming

`{contact}-{topic-slug}.md` — e.g., `kezia-monthly-report.md`
