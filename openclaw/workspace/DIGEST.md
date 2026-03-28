# Daily Digest

Bernard delivers a daily digest via Telegram. This file defines the structure, format, and learning loop.

---

## Structure

The digest has four numbered sections. Alex can reply "expand 2" or "skip 4" to steer.

1. **Today's priorities.** Pull from `knowledge/priorities/current.md`, cross-reference with calendar if available. Three items max. Frame as "what matters today" not "what's on the to-do list."

2. **Dropped balls.** Check `knowledge/tracking/dropped-balls.md` for items >48hrs without follow-up. Frame as "this is still open" — never "you forgot this." If nothing is overdue, say so in one line and move on.

3. **Relationship nudge.** Pick one person from `knowledge/people/` who is past their follow-up cadence. One sentence: who, why they matter, how long since last contact. If no people files exist yet, skip this section silently.

4. **Whimsy.** One item from `knowledge/ideas/` or a serendipitous connection Bernard noticed. Keep it light — this is the dessert, not the meal. If nothing fits, skip silently.

---

## Format Rules

- Terse prose paragraphs, never bullets or tables (per FEEDBACK.md).
- Voice-ready: write as if it will be spoken aloud.
- Max 200 words total unless Alex asks for detail.
- Numbered sections so Alex can reference them by number.
- No preamble. No "Good morning." Start with the content.

---

## Timing

- Default delivery: 07:30 WITA
- If Alex is in a different timezone (travel), adjust based on last known location
- Weekend digests: sections 1-2 only, skip 3-4 unless something is genuinely urgent

---

## Digest-Diff Tracking

After delivery, Bernard logs to `learning/digest-log.md`:
- Which sections Alex responded to or asked to expand
- Which sections Alex ignored
- Any explicit feedback ("too long", "more of this", "stop including X")

Over time, this data informs what belongs in the digest vs. noise. Promote topics Alex engages with. Demote topics Alex skips. Review the log weekly during the curation loop.
