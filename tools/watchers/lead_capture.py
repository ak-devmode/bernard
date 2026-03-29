#!/usr/bin/env python3
"""
Lead Capture Watcher — detects potential Padma Care leads from community
group messages (Bali expat groups, referrals, etc.).

Trigger criteria:
- Name + health concern or healthcare inquiry
- Name + request for medical services, advocacy, or concierge
- Referral patterns: "my friend needs...", "can you help someone with..."

Excludes:
- General health discussion, news sharing, non-actionable conversation
"""

import re
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
LEADS_DIR = REPO_ROOT / "openclaw" / "workspace" / "knowledge" / "padma-care" / "leads"

# Lead signal patterns — health inquiry + actionable intent
LEAD_PATTERNS_EN = [
    r"\b(looking for|need|needs)\s+.{0,20}(doctor|dentist|specialist|clinic|hospital|medical|healthcare)\b",
    r"\b(recommend|recommendation|suggest)\s+.{0,20}(doctor|dentist|specialist|clinic|hospital)\b",
    r"\b(can (you|anyone)|does anyone)\s+(help|recommend|know)\b.+\b(doctor|dentist|medical|health|clinic)\b",
    r"\bmy (friend|wife|husband|partner|mother|father|child|family)\s+(needs|is looking for|has)\b",
    r"\b(health\s+insurance|medical\s+advocacy|patient\s+advocacy|medical\s+concierge)\b",
    r"\b(emergency|urgent)\s+(medical|health|doctor|care)\b",
    r"\bemergency\b.+\b(doctor|hospital|clinic|care|help)\b",
    r"\b(sick|ill|injured|pain|symptoms?)\b.+\b(where|who|help|doctor|hospital)\b",
    r"\b(referral|refer me|refer someone)\b",
    r"\b(medical\s+check[\s-]?up|annual\s+check[\s-]?up|health\s+screening)\b",
    r"\b(expat\s+health|international\s+patient|foreign\s+patient)\b",
    r"\bpadma\s+care\b",
    r"\b(navigat|help).+\b(hospital|healthcare system|medical system|bpjs)\b",
]

LEAD_PATTERNS_ID = [
    r"\b(cari|butuh|perlu)\s+(dokter|klinik|rumah\s+sakit|spesialis)\b",
    r"\b(rekomendasi|rekomen)\s+(dokter|klinik|rumah\s+sakit)\b",
    r"\b(teman|istri|suami|anak|keluarga)\s+(saya\s+)?(sakit|butuh|perlu)\b",
    r"\b(sakit|nyeri|gejala|demam|luka)\b.+\b(dimana|siapa|tolong|dokter|rs)\b",
    r"\b(asuransi\s+kesehatan|advokasi\s+medis|medical\s+check[\s-]?up)\b",
    r"\b(darurat|gawat\s+darurat|ugd)\b.+\b(dimana|ke\s+mana|rekomendasi)\b",
    r"\b(bpjs|jkn)\b.+\b(bagaimana|cara|bantu|help)\b",
]

LEAD_PATTERNS = LEAD_PATTERNS_EN + LEAD_PATTERNS_ID

# Exclusion patterns — general health discussion, not a lead
EXCLUDE_PATTERNS = [
    r"\b(article|study|research|news|headline|report says)\b",
    r"\b(covid|vaccine|vaccination)\s+(update|news|stats|statistics)\b",
    r"\b(general\s+question|just\s+curious|anyone\s+else)\b",
    r"\b(berita|artikel|studi|penelitian)\b",
    # Sharing info, not seeking help
    r"\b(fyi|for your information|just sharing)\b",
    r"^(hi|hey|hello|good morning)\s+(everyone|all|guys|folks)\b",
]

# Product fit keywords
ADVOCACY_KEYWORDS = [
    "advocacy", "advocate", "navigate", "navigating", "help with hospital",
    "coordinate", "interpret", "translation", "bpjs", "insurance claim",
    "advokasi", "bantu", "koordinasi",
]

CONCIERGE_KEYWORDS = [
    "concierge", "vip", "premium", "private", "home visit", "executive",
    "check-up", "checkup", "screening", "annual", "comprehensive",
    "medical tourism", "health retreat",
]

# Urgency keywords
HIGH_URGENCY = ["emergency", "urgent", "asap", "immediately", "darurat", "gawat", "segera"]
MEDIUM_URGENCY = ["soon", "this week", "need", "help", "butuh", "perlu", "segera"]


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:max_len].rstrip('-')


def _extract_name(text: str) -> str:
    """Try to extract the lead's name from the message."""
    # "my friend {Name}", "{Name} is looking for", "{Name} needs"
    name_re = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    patterns = [
        rf"\bfriend\s+{name_re}\b",
        rf"{name_re}\s+(?:is\s+looking|needs|has\s+been|was)\b",
        rf"\b[Nn]ama(?:nya)?\s+{name_re}\b",  # Bahasa: "namanya Sarah"
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            name = match.group(1)
            skip = {"the", "this", "my", "our", "someone", "anybody", "anyone",
                    "dia", "saya", "kami", "teman", "istri", "suami"}
            if name.lower() not in skip:
                return name
    return "Unknown"


def _extract_inquiry(text: str) -> str:
    """Extract what the lead is asking about."""
    first_sentence = re.split(r'[.\n]', text)[0].strip()
    if len(first_sentence) > 80:
        first_sentence = first_sentence[:77] + "..."
    return first_sentence or "Healthcare inquiry"


def _determine_product_fit(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ADVOCACY_KEYWORDS):
        return "Advocacy"
    if any(kw in text_lower for kw in CONCIERGE_KEYWORDS):
        return "Concierge"
    return "Unclear"


def _determine_urgency(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in HIGH_URGENCY):
        return "high"
    if any(kw in text_lower for kw in MEDIUM_URGENCY):
        return "medium"
    return "low"


def _followup_date(urgency: str) -> str:
    """Calculate follow-up date based on urgency."""
    today = date.today()
    if urgency == "high":
        return (today + timedelta(days=1)).isoformat()
    if urgency == "medium":
        return (today + timedelta(days=3)).isoformat()
    return (today + timedelta(days=7)).isoformat()


def detect_lead(text: str) -> bool:
    """Returns True if the text contains a lead signal and is not excluded."""
    text_lower = text.lower().strip()

    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False

    for pattern in LEAD_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def build_entry(text: str, source: str = "bali-year-group") -> str:
    """Build the lead capture markdown entry."""
    name = _extract_name(text)
    inquiry = _extract_inquiry(text)
    product_fit = _determine_product_fit(text)
    urgency = _determine_urgency(text)
    followup_by = _followup_date(urgency)
    today = date.today().isoformat()

    return f"""---
title: "Lead: {name}"
type: lead
status: new
source: {source}
captured: {today}
hubspot: pending
drip: unassigned
product_fit: {product_fit}
---

## Lead Info
- **Name**: {name}
- **Contact**: {source} (channel)
- **Inquiry**: {inquiry}
- **Product fit**: {product_fit}
- **Urgency**: {urgency}

## Recommended Actions
- [ ] Enter in HubSpot
- [ ] Assign drip sequence: {product_fit.lower() if product_fit != "Unclear" else "tbd"}
- [ ] Initial follow-up by: {followup_by}

## HubSpot Draft Fields
- Contact name: {name}
- Source: {source}
- Pipeline: Padma Care
- Stage: New Lead
- Product interest: {product_fit}
- Notes: {inquiry}

## Trail
- {today}: Lead captured from {source}
"""


def process(text: str, dry_run: bool = False) -> dict:
    """
    Process a message for lead signals. Called by stream-watcher.py.
    """
    if not detect_lead(text):
        return {"matched": False, "output_path": None, "entry": None}

    entry = build_entry(text)

    if dry_run:
        return {"matched": True, "output_path": None, "entry": entry}

    name = _extract_name(text)
    today = date.today().isoformat()
    filename = f"{_slugify(name)}-{today}.md"
    output_path = LEADS_DIR / filename
    LEADS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(entry)

    return {"matched": True, "output_path": str(output_path), "entry": entry}
