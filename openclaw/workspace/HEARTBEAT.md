# Heartbeat Instructions

On each scheduled check:
1. Scan for flagged messages or urgent items in connected channels
2. Check if any tasks in workspace/tasks/ are overdue
3. Reference `knowledge/priorities/current.md` — only escalate items that touch active priorities
4. Note anything time-sensitive in the next 24 hours
5. If nothing urgent: respond with "All clear [time]" — no noise
6. Only message Alex proactively if something genuinely needs attention

## Stream Watcher Checks
On each heartbeat, also scan watcher outputs:
- `knowledge/followups/`: flag entries approaching or past `expected_by` date. Include overdue items in the next digest with a gentle flag.
- `knowledge/todos/`: flag proposed items sitting 7+ days unreviewed.
- `knowledge/padma-care/leads/`: flag leads with `hubspot: pending` for 7+ days.
If nothing is overdue or stale, don't mention watchers.

## Signal vs. Noise
- Urgent = something that will cost Alex time, money, or a relationship if not addressed today
- Not urgent = everything else
- Default to silence when in doubt
- Weight against `knowledge/priorities/current.md` — if it's not on the list, it's not urgent

## Tone on Proactive Messages
- One line summary + what action (if any) is needed from Alex
- No preamble, no "just checking in"

## End-of-Day Curation (after 20:00 WITA)
- Run the daily vault curation loop defined in `CURATION.md`
- Output the curation report to Alex as a single Telegram message
- Wait for approval before making any vault changes
- If Alex ignores curation reports for 3 consecutive days, reduce to weekly cadence

## Digest-Diff Tracking
- After each digest, note which items Alex acted on vs. ignored
- Use this signal to calibrate future digest relevance — promote topics Alex engages with, demote topics Alex skips
- Store calibration notes in `learning/` directory
