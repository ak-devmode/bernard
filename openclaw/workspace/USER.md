# Alex — Personal Context

*This file is living context. Update Current Priorities regularly.*

---

## Identity
- **Name:** Alex
- **Timezone:** Asia/Makassar (GMT+08:00)
- **Wife:** Fitri (Fie) — co-owner Narawangsa Villas
- **Daughter:** Safira (Fira), 3
- **Notes:** Expat executive, juggling multiple domains. Values concise, effective collaboration.

---

## Roles
- PMG Director of Growth
- Kalpa Health Board Chair + Acting CEO
- Narawangsa Villas Co-Founder
- Padma Care Founder

---

## Key People
- Dr. Gita, Dr. Pebri, Intan, Okto, Anis, Wahdi, Amanda (as per org chart in workspace)
- See `knowledge/people/` for detailed contact files

---

## Vault Reference

Bernard's knowledge base lives in `workspace/knowledge/`. Search it before reasoning from scratch. The vault contains:
- **projects/** — PMG, Kalpa, Narawangsa, Padma Care context files
- **people/** — Contact and relationship files (Alex populates)
- **priorities/** — Current top-5 priorities (check before every digest)
- **principles/** — Decision frameworks and values
- **ideas/** — Whimsy pool, business ideas, sabbatical list
- **comms/** — Summarized ingestion output (email, WhatsApp, Chatwoot)

When a question touches any of these domains, search the vault first.

---

## Current Priorities

See `knowledge/priorities/current.md` for the authoritative list. Bernard checks this file before every digest and heartbeat.

---

## Key Contacts

See `knowledge/people/` directory. Alex will populate with key contacts across PMG, Kalpa, Padma Care, and personal network.

---

## Ingestion Criteria

Rules for what gets ingested into the vault. Bernard follows these programmatically via `tools/ingest.py`.

### Email

**Include:**
- Emails from known contacts (see `knowledge/people/`)
- Emails mentioning PMG, Kalpa, WellMed, Narawangsa, or Padma Care
- Emails with action items, deadlines, or decisions
- Emails from domains Alex specifies (Alex to add: @kalpa.co, @padmacare.com, etc.)

**Exclude:**
- Newsletters and marketing emails
- Automated notifications (CI/CD, billing confirmations, shipping updates)
- Spam and bulk mail
- Personal family emails (unless Alex explicitly routes them)

**PII strip before writing:**
- Email addresses → `[EMAIL]`
- Phone numbers (Indonesian + international) → `[PHONE]`
- ID numbers (KTP, passport, BPJS) → `[ID_NUMBER]`
- Financial details beyond category → `[FINANCIAL]`

**Summary format:** sender (role, not name), topic, action items, deadline if any, sentiment.

### WhatsApp

**Include:**
- Business-related threads from approved contacts or groups
- Messages with action items or decisions
- Threads Alex explicitly forwards to Bernard

**Exclude:**
- Personal conversations and family groups
- Group noise (reactions, stickers, forwards without context)
- Memes and media-only messages

**PII strip:** same rules as email.

**Summary format:** participants (roles only, not names in vault), topic, outcome, follow-up needed.

### Chatwoot

**Include:**
- Conversations with negative sentiment or complaints
- Unresolved conversations older than 24 hours
- Medical-topic conversations (Padma Care)
- Conversations Alex is tagged in

**Exclude:**
- Resolved positive interactions
- Automated bot responses with no human follow-up

**Summary format:** topic, customer sentiment, resolution status, follow-up needed.
