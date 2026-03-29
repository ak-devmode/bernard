---
title: Reference — Tier 2 Long-Term Memory
type: config
updated: 2026-03-29
---

# Reference (Tier 2)

Long-term memory layer. QMD-indexed but ranked lower than `knowledge/` (Tier 1).
Bernard knows this material exists but doesn't reason about it unprompted.

## Structure

- `archive/` — Historical documents stored verbatim
- `index/` — Pointers to external docs (Dropbox paths, file locations, etc.)
  - `by-domain/` — Domain-specific indexes (business, financial, legal, etc.)
- `extracts/` — Curated insights extracted from archive material
  - `business/` — Business lessons, strategies, decisions
  - `relationships/` — Historical relationship context for active contacts
  - `technical/` — Architecture decisions, technical references

## When to Use

- Search reference/ when a question involves historical context ("what did Alex decide about X?")
- Cite the source path so Alex can find the original document
- Never copy financial or legal content into extracts — pointers only
