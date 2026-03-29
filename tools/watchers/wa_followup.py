#!/usr/bin/env python3
"""
WA Follow-Up Tracker — detects outbound requests in WhatsApp summaries
and creates follow-up tracking entries in knowledge/followups/.

Trigger criteria:
- Request patterns: "can you...", "please send...", "let me know when..."
- Delegation patterns: "I need you to...", "please handle..."
- Question patterns expecting a response about a deliverable

Excludes:
- Social messages, greetings, responses to others' requests, FYI messages
"""

import re
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
FOLLOWUPS_DIR = REPO_ROOT / "openclaw" / "workspace" / "knowledge" / "followups"

# Request patterns — phrases that signal Alex asked someone to do something
# English patterns
REQUEST_PATTERNS_EN = [
    r"\bcan you\b",
    r"\bcould you\b",
    r"\bwould you\b",
    r"\bplease send\b",
    r"\bplease share\b",
    r"\bplease prepare\b",
    r"\bplease update\b",
    r"\bplease check\b",
    r"\bplease confirm\b",
    r"\bplease review\b",
    r"\bplease handle\b",
    r"\bplease provide\b",
    r"\bplease arrange\b",
    r"\blet me know when\b",
    r"\blet me know if\b",
    r"\bfollowing up on\b",
    r"\bwhen will\b",
    r"\bwhen can\b",
    r"\bi need you to\b",
    r"\bi need .+ to\b",
    r"\btake care of\b",
    r"\bmake sure\b.+\b(is|are|gets)\b",
    r"\bsend me\b",
    r"\bget me\b",
    r"\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|end of (day|week|month))\b",
    r"\bdeadline\b",
]

# Bahasa Indonesia patterns
REQUEST_PATTERNS_ID = [
    r"\btolong\b",                          # please (request)
    r"\bmohon\b",                           # please (formal request)
    r"\bbisa\s+(tolong\s+)?",               # can (you)...
    r"\bkirim(kan|i)?\b",                   # send
    r"\bkirim ke\b",                        # send to
    r"\bsiap(kan)?\b",                      # prepare
    r"\bcek(kan)?\b",                       # check
    r"\bkonfirmasi\b",                      # confirm
    r"\bupdate\b",                          # update (loan word, common in WA)
    r"\bbagikan\b",                         # share
    r"\blaporkan\b",                        # report (verb)
    r"\burus(kan)?\b",                      # handle/take care of
    r"\bpastikan\b",                        # make sure
    r"\bsaya butuh\b",                      # I need
    r"\bsaya perlu\b",                      # I need
    r"\bsaya minta\b",                      # I'm asking for
    r"\bkabari\b",                          # let me know
    r"\binfo(kan|rmasi)?\b",               # inform
    r"\bkapan\b.+\b(selesai|bisa|jadi)\b", # when will it be done/ready
    r"\bfollow\s*up\b",                     # follow up (loan phrase)
    r"\bsebelum\s+(senin|selasa|rabu|kamis|jumat|sabtu|minggu|besok|akhir\s+(hari|minggu|bulan))\b",
    r"\bpaling\s+(lambat|telat)\b",         # at the latest
    r"\bdeadline\b",                        # deadline (loan word)
    r"\bjangan\s+lupa\b",                   # don't forget
    r"\bsegera\b",                          # immediately/ASAP
    r"\bsecepatnya\b",                      # as soon as possible
]

REQUEST_PATTERNS = REQUEST_PATTERNS_EN + REQUEST_PATTERNS_ID

# Exclusion patterns — social/FYI messages that shouldn't trigger
EXCLUDE_PATTERNS = [
    # English
    r"^(hi|hey|hello|good morning|good evening|thanks|thank you|ok|okay|great|sure|no worries|np)\b",
    r"\b(happy birthday|congrats|congratulations|merry christmas|happy new year)\b",
    r"\b(fyi|for your information|just letting you know|just so you know)\b",
    r"\b(haha|lol|😂|😄|👍|🙏)\b",
    r"^(yes|no|agreed|noted|received|got it)[\.\!\s]*$",
    # Bahasa Indonesia
    r"^(halo|hai|pagi|siang|sore|malam|makasih|terima\s+kasih|oke?|baik|siap)\b",
    r"\b(selamat\s+(ulang\s+tahun|tahun\s+baru|natal|hari\s+raya))\b",
    r"^(ya|tidak|sudah|iya|betul|benar|diterima)[\.\!\s]*$",
]


def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text to filesystem-safe slug."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:max_len].rstrip('-')


def _extract_contact(text: str) -> str:
    """
    Try to extract the contact name from the summary.
    Looks for patterns like "to Kezia", "asked Fitri", etc.
    Falls back to "unknown".
    """
    # "asked {Name}", "told {Name}", "to {Name}", "{Name}:" at start
    # Name must start with uppercase letter (not case-insensitive)
    name_re = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    patterns = [
        # English
        rf"\b[Aa]sked\s+{name_re}\b",
        rf"\b[Tt]old\s+{name_re}\b",
        rf"\b[Tt]o\s+{name_re}\b",
        # Bahasa — "minta Kezia", "bilang ke Fitri", "suruh Budi"
        rf"\b[Mm]inta\s+{name_re}\b",
        rf"\b[Bb]ilang\s+ke\s+{name_re}\b",
        rf"\b[Ss]uruh\s+{name_re}\b",
        rf"\b[Kk]e\s+{name_re}\b",
        # Generic — "{Name}:" at start of line
        rf"^{name_re}:",
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            name = match.group(1)
            # Skip common non-name words (EN + ID)
            skip = {"the", "this", "that", "my", "our", "your", "its",
                    "itu", "ini", "saya", "kami", "dia", "mereka"}
            if name.lower() not in skip:
                return name
    return "unknown"


def _extract_topic(text: str) -> str:
    """Extract a short topic from the summary text."""
    # Take the first sentence, truncated
    first_sentence = re.split(r'[.\n]', text)[0].strip()
    if len(first_sentence) > 60:
        first_sentence = first_sentence[:57] + "..."
    return first_sentence or "follow-up"


def _extract_project(text: str) -> str:
    """Try to identify which project this relates to."""
    project_keywords = {
        "pmg": ["pmg", "padma medical", "clinic"],
        "padma-care": ["padma care", "advocacy", "concierge", "lead"],
        "kalpa": ["kalpa", "wellmed", "satu sehat", "his"],
        "narawangsa": ["narawangsa", "villa", "guest"],
        "fin-engine": ["fin engine", "fei", "feh", "pbmc"],
    }
    text_lower = text.lower()
    for project, keywords in project_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return project
    return "general"


def _expected_by_date(text: str) -> str:
    """Infer expected_by date. Default: 5 business days from today."""
    today = date.today()

    # Check for explicit date-like references
    day_map = {
        "tomorrow": 1, "monday": None, "tuesday": None, "wednesday": None,
        "thursday": None, "friday": None, "saturday": None, "sunday": None,
    }

    text_lower = text.lower()

    # End of day — EN + ID
    if "end of day" in text_lower or "eod" in text_lower or "akhir hari" in text_lower:
        return today.isoformat()

    # End of week — EN + ID
    if "end of week" in text_lower or "eow" in text_lower or "akhir minggu" in text_lower:
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return (today + timedelta(days=days_until_friday)).isoformat()

    # End of month — EN + ID
    if "end of month" in text_lower or "eom" in text_lower or "akhir bulan" in text_lower:
        if today.month == 12:
            eom = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            eom = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return eom.isoformat()

    # Tomorrow — EN + ID
    if "tomorrow" in text_lower or "besok" in text_lower:
        return (today + timedelta(days=1)).isoformat()

    # Named days — EN + ID (sebelum senin, by Monday, etc.)
    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "senin": 0, "selasa": 1, "rabu": 2, "kamis": 3,
        "jumat": 4, "sabtu": 5, "minggu": 6,
    }
    for day_name, weekday_num in day_names.items():
        if day_name in text_lower:
            days_ahead = (weekday_num - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).isoformat()

    # "segera" / "secepatnya" → next business day
    if "segera" in text_lower or "secepatnya" in text_lower:
        result = today + timedelta(days=1)
        while result.weekday() >= 5:
            result += timedelta(days=1)
        return result.isoformat()

    # Default: 5 business days
    days_added = 0
    result = today
    while days_added < 5:
        result += timedelta(days=1)
        if result.weekday() < 5:  # Mon-Fri
            days_added += 1
    return result.isoformat()


def detect_request(text: str) -> bool:
    """
    Returns True if the text contains a request/delegation pattern
    and is NOT a social/FYI message.
    """
    text_lower = text.lower().strip()

    # Check exclusions first
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False

    # Check for request patterns
    for pattern in REQUEST_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def build_entry(text: str) -> str:
    """Build the followup markdown entry from the summary text."""
    contact = _extract_contact(text)
    topic = _extract_topic(text)
    project = _extract_project(text)
    expected_by = _expected_by_date(text)
    today = date.today().isoformat()

    return f"""---
title: "Follow-up: {topic}"
type: followup
status: waiting
contact: "{contact}"
channel: whatsapp
sent: {today}
expected_by: {expected_by}
escalation: none
related_project: "{project}"
---

## Request
{topic}

## Context
{project} — captured from WhatsApp outbound summary

## Trail
- {today}: Initial request sent via WA
"""


def process(text: str, dry_run: bool = False) -> dict:
    """
    Process a summarized WA message. Called by stream-watcher.py.

    Returns:
        dict with keys: matched (bool), output_path (Path|None), entry (str|None)
    """
    if not detect_request(text):
        return {"matched": False, "output_path": None, "entry": None}

    entry = build_entry(text)

    if dry_run:
        return {"matched": True, "output_path": None, "entry": entry}

    # Write the entry
    contact = _extract_contact(text)
    topic_slug = _slugify(_extract_topic(text))
    filename = f"{_slugify(contact)}-{topic_slug}.md"
    output_path = FOLLOWUPS_DIR / filename
    FOLLOWUPS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(entry)

    return {"matched": True, "output_path": str(output_path), "entry": entry}
