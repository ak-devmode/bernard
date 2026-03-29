# Phase 9 Resume Context

Read this file at the start of a Phase 9 session. It contains all directory traversal
knowledge from Phase 8 that Phase 9 needs.

## What Phase 8 Did

- Scanned ~/Projects/ (156 .md files), ~/Desktop/, ~/Downloads/, ~/Dropbox/ (32K+ files)
- Copied 82 .md files into `openclaw/workspace/reference/` (Tier 2)
- Tasks 8.6 (extracts) and 8.7 (index pointers) were deferred to Phase 9
- Inventories live at:
  - `openclaw/workspace/reference/index/inventory-projects.md` — ~/Projects/ scan
  - `openclaw/workspace/reference/index/inventory-desktop-downloads.md` — Desktop/Downloads/Dropbox scan

## Key Paths

| Location | Path | What's There |
|---|---|---|
| Dropbox | `/Users/alexknecht/Library/CloudStorage/Dropbox` | 220GB, ~32K files |
| Dropbox/PMG | `.../Dropbox/Padma Medical Group/` | Active business — highest value |
| Dropbox/FEI | `.../Dropbox/Fin Engine/` | Narawangsa ops, PBMC investment, company docs |
| Dropbox/AWK | `.../Dropbox/AWK/` | Personal — taxes, insurance, shelved startups |
| Dropbox/NAI | `.../Dropbox/North Atlantic/` | Defunct seafood biz (~18K files) — SKIP |
| Dropbox/Stone | `.../Dropbox/Stone Foundation/` | Old nonprofit board work — SKIP |
| Desktop | `~/Desktop/` | Active projects, PDFs, Padma Care briefs |
| Downloads | `~/Downloads/` | Duplicates mostly — already handled |
| Projects | `~/Projects/` | Code repos — .md files already copied |

## Dropbox Folder Structure (PMG — the important one)

```
Padma Medical Group/
  0 - PMG Group/          # Board, Vector Meeting, inventory, audit (196 files)
  1 - PMG - Bali/         # Bali clinic ops, licensing (183 files)
  2 - PMG - Surabaya/     # Surabaya ops, 2025 recap (84 files)
  3 - PMG - Jakarta/      # Minimal (5 files)
  4 - Managed Care/       # Padma Care marketing, Crew Care pricing (416 files)
  IT_Infra/               # Chatwoot/WA PRDs, Napier HIS, network (597 files)
  Kalpa Health/           # Business formation, AWS, PACS, payroll (96 files)
  HR/                     # Employee records, recruiting (217 files) — SKIP
  Sales/                  # Pipeline data (67 files)
  Marketing/              # Brand assets (91 files)
  Operating Plans/        # OP 2022-2026 financial models (42 files)
  Data Analysis Projects/ # Historical financial analysis (38 files)
  Medical Division/       # Equipment comparison (20 files)
  Personal Items/         # Expense reports (475 files) — SKIP
  Medical Impressions/    # Medical records (20 files) — SKIP
```

## Dropbox Folder Structure (Fin Engine)

```
Fin Engine/
  2. Narawangsa Villas/     # Operations (~1,200 files): accounting, payroll, HR, guest services, marketing, construction
  5. Organization Documents/ # Company registration, NPWP, Akta (~30 files) — LEGAL, index only
  6. PBMC Investment/       # Investment deal docs, due diligence (~60 files) — LEGAL, index only
  7-8. Bank/Financial/      # Bank + financial statements (~200 files) — SKIP
  10. Taxes/                # Tax filings, PPH (~100 files) — SKIP
  Fin Engine Holdings LLC/  # US entity docs (~73 files) — index only
```

## Dropbox Folder Structure (AWK — Personal)

```
AWK/
  Taxes Knecht Family/    # 302 files, 2019-2025 — INDEX ONLY, never content
  Job Searches/           # 295 files — SKIP
  Shelved Startups/       # 5,081 files (Anchor Energy ~4,925, AWK Wealth ~147) — extract if lessons apply
  Personal/               # 76 files — SKIP
  Insurance/              # 40 files — INDEX only
  BSV/                    # 69 files — SKIP
  Frisbee/                # 159 files — SKIP
  2006-2012/              # 91 files — SKIP
  2013-2014/              # 202 files (IMD era) — extract if MBA lessons relevant
  2015-2016/              # 2,292 files (mostly Bolt CMS vendor files) — SKIP
```

## What Phase 9 Needs to Do

1. **Deep scan non-.md files** in Dropbox PMG and Fin Engine folders — .docx, .xlsx, .pdf
2. **Relevance score** each file on 4 dimensions (decision-relevant, relationships, reusable insight, reference data)
3. **Alex reviews** scored inventory domain-by-domain
4. **Extract** high-score docs into reference/extracts/ as .md summaries
5. **Index** medium/low-score docs as pointers in reference/index/by-domain/
6. Also handle the ~74 deferred .md extracts from Phase 8 (large files 40K-80K that need summarization)

## Key Rules

- Financial/legal docs → pointer only, NEVER content
- HR/personnel records → SKIP
- Medical records → SKIP
- Personal media → SKIP
- North Atlantic (defunct seafood biz) → SKIP entirely
- Stone Foundation (old nonprofit) → SKIP entirely
- AWK/Shelved Startups — extract only if lessons apply to current ventures
- PII must be stripped from all extracts (regex + review)

## File Types in Dropbox (approximate counts)

| Type | Count | Notes |
|---|---|---|
| .pdf | 14,971 | Mostly receipts, invoices, scans, legal docs |
| .xlsx | 7,036 | Financial data, operational spreadsheets |
| .docx | 4,562 | Agreements, reports, correspondence |
| .xls | 1,719 | Legacy spreadsheets |
| .doc | 1,573 | Legacy Word docs |
| .pptx | 1,365 | Presentations |
| .csv | 295 | Data exports |
| .md | ~35 relevant | Already handled in Phase 8 |

## Alex's Direction (from Phase 8 review)

- reference/ is the permanent landing zone — Bernard searches it at lower QMD weight
- Non-.md files are the hard problem — Alex only started using .md format since Jan 2026
- Phase 9 can run incrementally, one domain per session
- Suggested order: Business → Relationships → Technical → Financial/Legal (pointers) → Personal
