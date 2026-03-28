---
title: Dropped Ball Tracking
type: skill
updated: 2026-03-28
---

# Dropped Ball Tracking

Tracks commitments Alex made and flags when follow-up hasn't happened.

## What It Does

Bernard listens for commitments in conversations, email summaries, and digest responses. When Alex says "I'll send that," "let me follow up," or "I'll get back to them" — Bernard captures it.

## Data Source

- Daily conversations via Telegram
- Email summaries (when Phase 5 ingestion is live)
- Calendar events with follow-up implications

## Storage

`knowledge/tracking/dropped-balls.md` — running list.

## Trigger

Checked at each daily digest (section 2). Items >48hrs without follow-up get flagged.

## Tone

"This is still open" — never "you forgot this." Bernard is a memory aid, not a taskmaster. If Alex explicitly says "drop it" or "not doing that anymore," remove the item without judgment.

## How to Capture

When Alex makes a commitment in conversation:
1. Note the item, who it was promised to, and the date
2. Add to tracking file with a reasonable follow-up deadline (default: 48hrs unless context suggests otherwise)
3. Do NOT ask Alex to confirm every capture — just track it. Alex will correct if wrong.
