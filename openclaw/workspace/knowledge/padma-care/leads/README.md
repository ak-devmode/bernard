---
title: Lead Capture Pipeline
type: readme
---

# Padma Care Lead Capture

Leads detected from Bali community groups and referrals.

## How It Works

1. **Capture**: Stream watcher detects health inquiries / service requests in lead group messages
2. **Draft**: Entry created with HubSpot draft fields pre-filled
3. **Surface**: Daily digest shows new leads by urgency, with follow-up deadlines
4. **Enter**: Alex enters in HubSpot and assigns drip sequence

## Status Lifecycle

- `new` — just captured
- `hubspot-entered` — Alex confirmed HubSpot entry
- `drip-assigned` — drip sequence active
- `converted` — became a client
- `lost` — didn't convert, with reason

## File Naming

`{name-slug}-{date}.md` — e.g., `sarah-jones-2026-03-29.md`
