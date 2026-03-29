#!/usr/bin/env python3
"""
Intent-Aligned Todo Capture — detects actionable asks directed at Alex
in email/WhatsApp summaries and scores them against current priorities.

Trigger criteria:
- Direct request to Alex with an actionable ask
- Contains patterns: "can you...", "please...", "we need...", "deadline is..."

Excludes:
- Newsletters, automated notifications, social, group noise
- CC'd/FYI messages, mass emails
"""

import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
TODOS_DIR = REPO_ROOT / "openclaw" / "workspace" / "knowledge" / "todos"
PRIORITIES_PATH = REPO_ROOT / "openclaw" / "workspace" / "knowledge" / "priorities" / "current.md"

# Actionable ask patterns — someone wants Alex to do something
ASK_PATTERNS_EN = [
    r"\b(can you|could you|would you)\b",
    r"\b(please|pls)\s+\w+",
    r"\bwe need (you to|your)\b",
    r"\bdeadline\s+(is|:)\b",
    r"\b(action\s+required|action\s+needed|your\s+input\s+(needed|required))\b",
    r"\b(approve|approval\s+needed|sign\s+off)\b",
    r"\b(review|feedback)\s+(needed|required|requested|by)\b",
    r"\b(urgent|asap|immediately|time[\s-]sensitive)\b",
    r"\b(decision\s+needed|your\s+call|your\s+decision)\b",
    r"\b(submit|send|provide|prepare|complete)\s+(by|before)\b",
    r"\bassign(ed)?\s+to\s+you\b",
    r"\b(follow[\s-]?up|circle back|check in)\s+(with|on|about)\b",
]

ASK_PATTERNS_ID = [
    r"\btolong\b",
    r"\bmohon\b",
    r"\b(bisa|boleh)\s+(tolong\s+)?",
    r"\bperlu\s+(anda|kamu|bapak)\b",
    r"\b(approve|persetujuan|tanda\s+tangan)\b",
    r"\b(segera|secepatnya|penting)\b",
    r"\b(keputusan|input|masukan)\s+(dari\s+)?(anda|bapak)\b",
    r"\bdeadline\b",
    r"\bsebelum\s+\w+",
]

ASK_PATTERNS = ASK_PATTERNS_EN + ASK_PATTERNS_ID

# Exclusion patterns — automated/mass/social content
EXCLUDE_PATTERNS = [
    r"\b(unsubscribe|opt[\s-]?out|manage\s+preferences|email\s+preferences)\b",
    r"\b(newsletter|digest|weekly\s+update|monthly\s+report|automated)\b",
    r"\b(no[\s-]?reply|noreply|do[\s-]?not[\s-]?reply)\b",
    r"\b(cc|bcc|fyi|for your (information|reference))\b",
    r"\b(all[\s-]?staff|dear\s+team|dear\s+all|hi\s+everyone|hi\s+all)\b",
    # Bahasa
    r"\b(berhenti\s+berlangganan|kepada\s+seluruh)\b",
]


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:max_len].rstrip('-')


def _load_priorities() -> list[str]:
    """Load current top-5 priorities from the vault. Returns list of priority strings."""
    if not PRIORITIES_PATH.exists():
        return []

    text = PRIORITIES_PATH.read_text()
    priorities = []

    # Parse numbered items under "## Top 5"
    in_top5 = False
    for line in text.splitlines():
        if "## Top 5" in line:
            in_top5 = True
            continue
        if in_top5 and line.startswith("##"):
            break
        if in_top5 and re.match(r'\d+\.', line.strip()):
            # Strip the number prefix and any HTML comments
            content = re.sub(r'^\d+\.\s*', '', line.strip())
            content = re.sub(r'<!--.*?-->', '', content).strip()
            if content:
                priorities.append(content)

    return priorities


def _score_alignment(text: str, priorities: list[str]) -> tuple[str, str]:
    """
    Score alignment of an ask against current priorities.
    Returns (alignment, priority_match).
    """
    if not priorities:
        return "unrelated", ""

    text_lower = text.lower()

    # Direct match — the ask contains words from a priority
    for p in priorities:
        p_words = set(re.findall(r'\b\w{4,}\b', p.lower()))  # words 4+ chars
        if not p_words:
            continue
        matches = sum(1 for w in p_words if w in text_lower)
        if matches >= 2 or (matches >= 1 and len(p_words) <= 2):
            return "aligned", p

    # Adjacent — shares a project/domain keyword but not directly
    project_domains = {
        "pmg": ["pmg", "padma medical", "clinic", "klinik"],
        "padma care": ["padma care", "advocacy", "lead", "concierge"],
        "kalpa": ["kalpa", "wellmed", "satu sehat", "his", "fhir"],
        "narawangsa": ["narawangsa", "villa", "guest", "tamu"],
        "fin engine": ["fin engine", "fei", "feh", "pbmc", "loan"],
    }
    ask_domains = set()
    priority_domains = set()
    for domain, keywords in project_domains.items():
        if any(kw in text_lower for kw in keywords):
            ask_domains.add(domain)
        for p in priorities:
            if any(kw in p.lower() for kw in keywords):
                priority_domains.add(domain)

    overlap = ask_domains & priority_domains
    if overlap:
        return "adjacent", f"related to {', '.join(overlap)}"

    return "unrelated", ""


def _extract_asker(text: str) -> str:
    """Try to extract who is asking."""
    patterns = [
        r"\b[Ff]rom:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?):",
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:asked|wants|needs|requesting)\b",
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            name = match.group(1)
            skip = {"the", "this", "dear", "from", "please", "action"}
            if name.lower() not in skip:
                return name
    return "Unknown"


def _extract_ask(text: str) -> str:
    """Extract the core ask from the message."""
    first_sentence = re.split(r'[.\n]', text)[0].strip()
    if len(first_sentence) > 80:
        first_sentence = first_sentence[:77] + "..."
    return first_sentence or "Action requested"


def detect_ask(text: str) -> bool:
    """Returns True if the text contains an actionable ask directed at Alex."""
    text_lower = text.lower().strip()

    if not text_lower:
        return False

    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False

    for pattern in ASK_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def build_entry(text: str) -> str:
    """Build the todo capture markdown entry."""
    asker = _extract_asker(text)
    ask = _extract_ask(text)
    priorities = _load_priorities()
    alignment, priority_match = _score_alignment(text, priorities)
    today = date.today().isoformat()

    # Bernard's read on alignment
    if alignment == "aligned":
        intent_read = f"This aligns with current priority: {priority_match}. Likely a 'yes'."
    elif alignment == "adjacent":
        intent_read = f"Adjacent to current focus ({priority_match}). Worth considering but not urgent."
    else:
        intent_read = "Does not match current priorities. Consider deferring or declining."

    return f"""---
title: "Todo: {ask}"
type: todo
status: proposed
source: email
from: "{asker}"
captured: {today}
alignment: {alignment}
priority_match: "{priority_match}"
---

## The Ask
{ask}

## Alex's Likely Intent
{intent_read}

## If Accepted
- [ ] Respond to {asker}
- [ ] Complete the requested action
"""


def process(text: str, dry_run: bool = False) -> dict:
    """
    Process a message for actionable asks. Called by stream-watcher.py.
    """
    if not detect_ask(text):
        return {"matched": False, "output_path": None, "entry": None}

    entry = build_entry(text)

    if dry_run:
        return {"matched": True, "output_path": None, "entry": entry}

    ask = _extract_ask(text)
    today = date.today().isoformat()
    filename = f"{_slugify(ask)}-{today}.md"
    output_path = TODOS_DIR / filename
    TODOS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(entry)

    return {"matched": True, "output_path": str(output_path), "entry": entry}
