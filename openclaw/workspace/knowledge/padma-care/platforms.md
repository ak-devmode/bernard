# Padma Care — Community Platforms

Target platforms for community monitoring. Alex to confirm rankings, add specific groups, and mark which ones team is already in.

---

## Tier 1 — High Volume, Open Access

| Platform | Group/Channel | Est. Audience | Access | Healthcare Q Frequency | Status | Notes |
|----------|--------------|---------------|--------|----------------------|--------|-------|
| Facebook | Bali Expats | ~150k members | Open (join + approve) | High — daily health threads | [ ] Joined | Largest English-speaking expat group. High noise but high reach. |
| Facebook | Expat Living in Bali | ~80k members | Open (join + approve) | Medium-high | [ ] Joined | Slightly more settled/long-term expat audience. |
| Facebook | Retire in Bali | TBD | Open (join + approve) | Medium-high | [ ] Check membership | Retiree demographic — high concierge potential. Alex may already be a member. |
| Reddit | r/bali | ~120k members | Open | Medium — weekly health posts | [ ] Active | Skews younger, digital nomad demographic. Good for SEO backlinks. |
| TripAdvisor | Bali Forum | High (tourist traffic) | Open | Medium — travel health, emergency Q's | [ ] Active | Tourist-heavy. Good for "medical emergency in Bali" type queries. |

## Tier 2 — High Quality, Requires Presence

| Platform | Group/Channel | Est. Audience | Access | Healthcare Q Frequency | Status | Notes |
|----------|--------------|---------------|--------|----------------------|--------|-------|
| Facebook | Canggu Community | ~30-50k | Open (join + approve) | Medium | [ ] Joined | Area-specific. Higher trust, more personal threads. |
| Facebook | Ubud Community | ~20-40k | Open (join + approve) | Medium | [ ] Joined | Older demographic, more families. Higher concierge potential. |
| Facebook | Seminyak/Kuta Expats | ~15-30k | Open (join + approve) | Low-medium | [ ] Joined | Mixed tourist/expat. |
| InterNations | Bali chapter | ~5-10k | Membership required | Low but high-quality | [ ] Member | Professional expat network. Higher income demographic = concierge leads. |

## Tier 3 — Closed, Requires Team Member

| Platform | Group/Channel | Est. Audience | Access | Healthcare Q Frequency | Status | Notes |
|----------|--------------|---------------|--------|----------------------|--------|-------|
| WhatsApp | Expat community groups (HIGHEST SIGNAL) | Varies (50-300 per group) | Invite only | High — real-time, personal | [ ] In group | See WA Monitoring section below. Someone posted a public list of Bali community WA groups — dig up and evaluate. |
| Facebook | Neighborhood-specific groups (e.g., Berawa Neighbors) | 1-5k each | Closed, requires local address | Low but high trust | [ ] Joined | Hyper-local. When health Q's come up, conversion rate is highest. |
| Facebook | Bali parenting/family groups | ~10-20k | Closed | Medium — pediatric Q's | [ ] Joined | Family healthcare = high concierge potential. |

---

## Priority Order for Launch

1. **Bali Expats (FB)** — volume play, start here
2. **r/bali** — open, searchable, SEO value
3. **Canggu Community (FB)** — area Alex/team operates in
4. **Ubud Community (FB)** — family demographic
5. **TripAdvisor Bali Forum** — tourist emergency Q's

Start with top 3. Add others as cadence is established.

---

## WA Monitoring — Architecture Problem

WhatsApp groups are highest signal but hardest to monitor. Alex does NOT want manual summarization burden.

**Options (ranked by feasibility):**
1. **WA→Telegram bridge** — Forward select WA groups to a Telegram channel Bernard already monitors. One-time setup, then hands-off. Bernard's ingestion pipeline handles the rest.
2. **Delegate forwarding** — Team member forwards interesting health threads to Bernard's Telegram. Low-tech, works immediately.
3. **Chatwoot via WA Business API** — If WA Business is connected to Chatwoot, Bernard's Phase 5 ingestion already handles Chatwoot input. Requires WA Business account.
4. **WA Web automation** — Fragile, against TOS. Not recommended.

**Next step:** Find the public list of Bali community WA groups. Evaluate which are worth joining. Pick a monitoring method above.

---

## Alex TODO

- [ ] Confirm group names and sizes (estimates above from public data)
- [ ] Mark which groups team is already active in
- [ ] Find the public list of Bali community WA groups (someone posted online)
- [ ] Decide WA monitoring method (see WA Monitoring section)
- [ ] Check if already a member of Retire in Bali (FB)
- [ ] Identify specific closed groups worth joining
- [ ] Assign team member(s) for Tier 3 group access
