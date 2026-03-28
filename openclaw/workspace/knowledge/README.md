# Knowledge Vault

Bernard's long-term memory and knowledge base. All files are Markdown.

## Structure

- **people/** — Contacts, relationships, warmth tracking. Templates only — Bernard populates from interactions. Never store raw PII without consent.
- **projects/** — Active projects (Padma Care, Kalpa, PMG, Narawangsa). Pre-populated with known context.
- **priorities/** — Current goals, tasks, decision frameworks. Updated by Bernard and Alex.
- **principles/** — Values, red lines, decision criteria. Rarely changes.
- **ideas/** — Inspiration pools, whimsy, kid magic, travel. Low-priority, high-delight.
- **comms/** — Communication templates, voice docs, response patterns.

## Ingestion Rules

1. All ingested content must be PII-stripped before writing (regex primary, LLM verify bonus).
2. Dedup: hash subject+date, skip if file exists.
3. One file per entity/topic. Update existing files, don't create duplicates.
4. Filenames: lowercase, hyphenated (e.g., `alex-knecht.md`, `padma-care.md`).
5. Every file starts with a YAML frontmatter block: `title`, `type`, `updated`.

## Sibling Directories

- **../artifacts/** — Generated outputs (meeting notes, drafted emails, reports).
- **../memory/** — Session memory, conversation context, compaction artifacts.
- **../learning/** — Feedback loop data, corrections, calibration notes.
