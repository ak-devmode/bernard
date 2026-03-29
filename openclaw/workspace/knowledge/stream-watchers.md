---
title: Stream Watcher Registry
type: config
updated: 2026-03-29
---

# Stream Watchers

Bernard checks this file on each heartbeat to know which watchers are active
and where to route incoming summaries.

## Active Watchers

| Name | Source | Output | Gate | Status |
|------|--------|--------|------|--------|
| wa-followup-tracker | whatsapp-outbound | knowledge/followups/ | daily-digest | active |
| lead-capture | bali-year-group | knowledge/padma-care/leads/ | daily-digest | active |
| todo-capture | email, whatsapp | knowledge/todos/ | daily-digest | active |

## Adding a New Watcher

1. Define source, trigger criteria, action, and gate
2. Add row to the table above
3. Create output directory in knowledge/
4. Add output section to daily digest template (DIGEST.md)
5. Bernard starts watching on next heartbeat
