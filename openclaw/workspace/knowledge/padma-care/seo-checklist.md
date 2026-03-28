# Padma Care — SEO Basics Checklist

**Site:** padmacare.pbmcgroup.com

The goal is technical soundness so content can rank and be cited by AI assistants (ChatGPT, Perplexity, Google AI Overviews). Not chasing authority scores.

---

## One-Time Tasks

### Technical Foundation
- [ ] **Meta titles and descriptions** on all key pages — unique per page, include "Bali" and service keywords
- [ ] **Structured data markup**: Schema.org `LocalBusiness` + `MedicalOrganization` — name, address, phone, services, geo coordinates
- [ ] **Page speed audit** (Lighthouse) — fix obvious issues (image compression, render-blocking scripts, lazy loading)
- [ ] **Google Search Console** configured and verified
- [ ] **Sitemap.xml** generated and submitted to Search Console
- [ ] **Mobile responsiveness** verified — test on iPhone SE (smallest common viewport) and standard Android
- [ ] **HTTPS** confirmed across all pages (no mixed content)
- [ ] **Canonical URLs** set to prevent duplicate content issues

### Content & Structure
- [ ] **Content answers specific questions clearly** — each service page should answer "what is this, who needs it, what does it cost, how do I start"
- [ ] **GEO / AI citation optimization** — structure answers so AI assistants can extract and cite them (clear headings, direct answers in first paragraph, FAQ sections)
- [ ] **Internal linking** between service pages and FAQ/content pages — every page should link to at least 2 related pages
- [ ] **FAQ section** on key service pages — use `FAQPage` schema markup so Google can feature them
- [ ] **Contact info** visible on every page (phone, WhatsApp link, email) — not buried in footer only

### Local SEO
- [ ] **Google Business Profile** claimed and complete (if not already)
- [ ] **NAP consistency** (Name, Address, Phone) — same across website, Google Business, and any directories
- [ ] **Service area** defined in Google Business Profile (Bali-wide or specific areas)

---

## Weekly Monitoring (Bernard Does This)

Bernard checks these weekly and surfaces anything notable in the daily digest:

- **Search Console: new queries** — surface as content opportunities (add to content-queue.md)
- **Ranking changes** on target terms (BPJS, healthcare Bali, hospital Bali, medical emergency Bali)
- **New backlinks** — note any organic links from community posts or content
- **Indexing errors** — flag any pages dropped from index

---

## Target Keywords (Seed List)

Based on community monitoring and content queue — Alex to confirm:

| Keyword | Intent | Priority | Content Exists? |
|---------|--------|----------|----------------|
| BPJS for foreigners Bali | Informational | High | [ ] No — content-queue #1 |
| healthcare Bali expats | Informational | High | [ ] No — content-queue #2 |
| best hospital Bali | Informational/Local | High | [ ] No — content-queue #3 |
| medical emergency Bali | Urgent/Informational | High | [ ] No — content-queue #5 |
| healthcare advocacy Bali | Commercial | Medium | [ ] Service page? |
| health concierge Bali | Commercial | Medium | [ ] Service page? |
| travel insurance Indonesia hospital | Informational | Medium | [ ] No — content-queue #4 |

---

## Notes

- SEO is a byproduct of being genuinely useful, not a goal in itself
- Content queue items (content-queue.md) double as SEO targets — write for humans, structure for machines
- Community responses that link back to site content are the most natural backlink strategy
- AI citation optimization (GEO) matters as much as traditional SEO — Perplexity and ChatGPT increasingly answer health questions with citations
