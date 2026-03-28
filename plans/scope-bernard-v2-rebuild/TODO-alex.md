# Alex TODOs — Bernard v2

Action items that only Alex can do. Check off as you go.

---

## From Phase 3

- [ ] Fill in `openclaw/workspace/knowledge/priorities/current.md` — top 5 priorities. Bernard can't prioritize without this.
- [ ] Fill in `openclaw/workspace/knowledge/principles/decision-frameworks.md` — risk tolerance, delegation philosophy, comms preferences sections.
- [ ] Populate 5-10 people files in `openclaw/workspace/knowledge/people/` — copy TEMPLATE.md, start with key contacts across PMG, Kalpa, Padma Care, and personal.

## From Phase 4

- [ ] Populate `openclaw/workspace/knowledge/tracking/staff-checkins.md` — your team leads, cadence, last check-in dates.
- [ ] Set board meeting dates in `openclaw/workspace/knowledge/tracking/board-topics-kalpa.md` and `board-topics-padma.md`.
- [ ] List 3-5 competitor villas in `openclaw/workspace/knowledge/tracking/narawangsa-pricing.md`.

## From Phase 6

- [ ] Complete `claude login` on server (as bernard user) — sets up ANTHROPIC_API_KEY auth
- [ ] Add `ANTHROPIC_API_KEY` to Bernard's systemd service Environment= lines (if using API key instead of OAuth)
- [ ] Set up `~ubuntu/.claude/CLAUDE.md` on VM — copy from local, with your preferences and skills
- [ ] Set up shared skills directory on VM (`~/.claude/skills/` → symlink ai-skills + gstack)
- [ ] Test CC dispatch: `acpx claude exec "echo hello"` as bernard user

## From Phase 1-2 (still pending)

- [ ] Verify OpenRouter spend limit is set (openrouter.ai)
- [ ] Run Bernard for 2 weeks text-only to evaluate digest quality (gate for voice re-enablement)
