# Daily Vault Curation

Run this loop at end of day (triggered by HEARTBEAT.md). Output goes to Alex for review — never auto-commit vault changes.

---

## 1. Shape Summary

Who communicated with Alex today, by topic category only. No names in the summary unless Alex has explicitly added them to the people vault. Format as terse prose, 3-5 sentences max.

Example: "Three inbound on Padma Care operations, two Kalpa dev threads (auth migration and deploy pipeline), one personal. Nothing from PMG today."

---

## 2. Top 10 Additions

List the 10 highest-value pieces of information from today's interactions that would improve vault context if captured. Rank by long-term usefulness, not urgency.

For each: one line describing what to add and which vault file it belongs in. If the file doesn't exist yet, note that.

---

## 3. Pruning Candidates

Flag vault entries that are now stale, irrelevant, or out of scope. For each: the file path, why it's a candidate, and whether to update or remove.

Only flag — never auto-delete.

---

## 4. Vault Health Score

One paragraph assessing whether the vault is growing in a useful direction. Is it balanced across projects? Are people files being populated? Are priorities current? Is there drift toward noise?

End with a single rating: HEALTHY, GROWING, STALE, or DRIFTING.

---

## Instructions to Bernard

- Run this at end-of-day heartbeat (after 20:00 WITA).
- Output the curation report to Alex via Telegram as a single message.
- Wait for Alex's approval before making any vault changes.
- If Alex ignores the curation report for 3 consecutive days, reduce to weekly.
- Format as terse prose per FEEDBACK.md. No bullet lists, no markdown tables.
