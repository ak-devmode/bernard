---
title: Communications Vault
type: readme
updated: 2026-03-28
---

# Communications Vault

Summarized communication entries from ingestion pipelines. **Never raw input** — all content is summarized and PII-stripped before landing here.

## Structure

- **email/** — Summarized email entries (populated by Phase 5 ingestion pipeline)
- **whatsapp/** — Summarized WhatsApp entries
- **chatwoot/** — Flagged conversation summaries from Chatwoot

## Rules

1. **Summaries only.** Never store raw message content. Each file is a structured summary: sender context, topic, action items, urgency.
2. **PII stripped.** Phone numbers, email addresses, and personal identifiers are removed before writing. Regex primary, LLM verification as bonus layer.
3. **Dedup by hash.** Subject + date hash prevents duplicate entries.
4. **One file per conversation thread or topic.** Update existing files for ongoing threads.
5. **Ingestion criteria defined in USER.md.** What gets ingested vs. ignored is controlled by the criteria lists there.

## Populated By

These directories are empty until Phase 5 (Ingestion Pipeline) is deployed. The `tools/ingest.py` script handles the ingestion, summarization, and PII stripping.
