---
title: Auto-Learn from Negative Signals
type: skill
updated: 2026-03-28
---

# Auto-Learn from Negative Signals

Bernard detects dissatisfaction and writes corrections to FEEDBACK.md without Alex having to explicitly ask.

## Detection Signals

Bernard watches for these patterns in conversation:

1. **Explicit pushback** — "no", "not that", "don't do X", "stop", "wrong"
2. **Significant edits** — Alex rewrites Bernard's draft substantially (>50% change)
3. **Ignored output** — Bernard delivers something and Alex doesn't acknowledge it (2+ times)
4. **Tone correction** — "too long", "be shorter", "I don't need that much detail"
5. **Repeated requests** — Alex asks for the same thing twice (Bernard didn't get it right the first time)

## Response

When Bernard detects a signal:
1. Distill the correction into a specific, actionable rule
2. Append it to FEEDBACK.md as a numbered entry
3. Acknowledge briefly: "Noted — added to FEEDBACK.md: [one-line summary]"
4. Apply the correction immediately in the current conversation

## Constraints

- Never write aspirational entries — only observed corrections
- Never argue with or rationalize the correction
- If unsure whether it's a correction, ask once: "Should I note that as a preference?"
- Re-read FEEDBACK.md after every compaction event (per existing rule #7)

## Future: System Hook

OpenClaw v2026.3.24 has a `hooks` subsystem but it requires the full gateway environment to configure. When CLI access improves or the gateway supports declarative hook config in openclaw.json, migrate this to a system-level afterTurn hook for automatic detection outside of conversation context.
