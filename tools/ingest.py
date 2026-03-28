#!/usr/bin/env python3
"""
Unified ingestion pipeline for Bernard's knowledge vault.

Ingests email, WhatsApp, or Chatwoot content into structured markdown
summaries in knowledge/comms/. Strips PII, deduplicates, and optionally
summarizes via LLM.

Usage:
    python3 tools/ingest.py --source email < raw_email.txt
    python3 tools/ingest.py --source whatsapp < wa_export.txt
    python3 tools/ingest.py --source email --dry-run < raw_email.txt
    echo "raw text" | python3 tools/ingest.py --source email --subject "Test"
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from pii_strip import strip_pii, StripResult

# Default vault path — relative to repo root
VAULT_ROOT = Path(__file__).parent.parent / "openclaw" / "workspace" / "knowledge" / "comms"


@dataclass
class ParsedInput:
    """Structured representation of parsed input."""
    source: str
    subject: str
    sender: str  # role/relationship, not name
    date_str: str  # YYYY-MM-DD
    body: str
    participants: list[str] | None = None  # for WA/Chatwoot


@dataclass
class IngestResult:
    """Result of the ingestion pipeline."""
    output_path: Path | None
    markdown: str
    was_duplicate: bool = False
    pii_result: StripResult | None = None


def parse_email(text: str, subject_override: str | None = None) -> ParsedInput:
    """
    Parse raw email text into structured fields.

    Handles common email formats:
    - From: / To: / Subject: / Date: headers
    - Plain text body after headers
    """
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_body = False

    for line in text.splitlines():
        if in_body:
            body_lines.append(line)
        elif line.strip() == "":
            in_body = True
        elif ":" in line and not in_body:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
        else:
            # No clear header/body separation — treat as body
            in_body = True
            body_lines.append(line)

    subject = subject_override or headers.get("subject", "No subject")
    sender = headers.get("from", "Unknown sender")
    date_str = _extract_date(headers.get("date", ""))

    return ParsedInput(
        source="email",
        subject=subject,
        sender=sender,
        date_str=date_str,
        body="\n".join(body_lines).strip(),
    )


def parse_whatsapp(text: str, subject_override: str | None = None) -> ParsedInput:
    """
    Parse WhatsApp export text.

    Common WA export format:
    [DD/MM/YYYY, HH:MM:SS] Sender: Message
    """
    messages: list[str] = []
    participants: set[str] = set()
    first_date = ""

    # WA export line pattern
    wa_pattern = re.compile(
        r'\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s*\d{1,2}:\d{2}(?::\d{2})?\]?\s*-?\s*([^:]+):\s*(.*)'
    )

    for line in text.splitlines():
        match = wa_pattern.match(line)
        if match:
            date_part, sender, message = match.groups()
            participants.add(sender.strip())
            messages.append(f"{sender.strip()}: {message.strip()}")
            if not first_date:
                first_date = _normalize_date(date_part)
        elif messages:
            # Continuation of previous message
            messages[-1] += f" {line.strip()}"

    if not messages:
        # Fallback: treat as plain text
        return ParsedInput(
            source="whatsapp",
            subject=subject_override or "WhatsApp conversation",
            sender="Unknown",
            date_str=date.today().isoformat(),
            body=text.strip(),
            participants=[],
        )

    return ParsedInput(
        source="whatsapp",
        subject=subject_override or "WhatsApp conversation",
        sender=", ".join(sorted(participants)),
        date_str=first_date or date.today().isoformat(),
        body="\n".join(messages),
        participants=sorted(participants),
    )


def parse_chatwoot(text: str, subject_override: str | None = None) -> ParsedInput:
    """
    Parse Chatwoot conversation export.

    Expects a simple format — adapt as needed when Chatwoot integration is wired.
    """
    return ParsedInput(
        source="chatwoot",
        subject=subject_override or "Chatwoot conversation",
        sender="Support thread",
        date_str=date.today().isoformat(),
        body=text.strip(),
        participants=[],
    )


PARSERS = {
    "email": parse_email,
    "whatsapp": parse_whatsapp,
    "chatwoot": parse_chatwoot,
}


def _extract_date(date_header: str) -> str:
    """Extract YYYY-MM-DD from various date formats. Falls back to today."""
    if not date_header:
        return date.today().isoformat()

    # Try ISO format
    iso_match = re.search(r'\d{4}-\d{2}-\d{2}', date_header)
    if iso_match:
        return iso_match.group()

    # Try common email date format: "Mon, 28 Mar 2026 10:30:00 +0800"
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }
    rfc_match = re.search(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_header)
    if rfc_match:
        day, month, year = rfc_match.groups()
        mm = month_map.get(month.lower(), "01")
        return f"{year}-{mm}-{int(day):02d}"

    return date.today().isoformat()


def _normalize_date(date_str: str) -> str:
    """Convert DD/MM/YYYY to YYYY-MM-DD."""
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', date_str)
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{int(month):02d}-{int(day):02d}"
    return date.today().isoformat()


def _slugify(text: str, max_len: int = 50) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug[:max_len].rstrip('-')


def dedup_hash(subject: str, date_str: str) -> str:
    """Generate a dedup hash from subject + date."""
    key = f"{subject.lower().strip()}|{date_str}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def dedup_check(source: str, subject: str, date_str: str, vault_root: Path) -> bool:
    """Check if a file with this hash already exists. Returns True if duplicate."""
    h = dedup_hash(subject, date_str)
    source_dir = vault_root / source
    if not source_dir.exists():
        return False
    for f in source_dir.iterdir():
        if h in f.name:
            return True
    return False


def summarize_llm(parsed: ParsedInput) -> str:
    """
    Summarize the parsed input using Haiku via OpenRouter.
    Falls back to truncated body if LLM is unavailable.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        # No API key — return truncated body as summary
        body = parsed.body[:500]
        return f"{body}\n\n**Action items:** (manual review needed)\n**Follow-up by:** (manual review needed)"

    source_type = parsed.source
    prompt = (
        f"Summarize this {source_type} in 2-3 sentences. Then list action items "
        f"(or 'none') and any follow-up deadline (or 'none').\n\n"
        f"Subject: {parsed.subject}\n"
        f"From: {parsed.sender}\n\n"
        f"{parsed.body[:2000]}"
    )

    try:
        payload = json.dumps({
            "model": "anthropic/claude-haiku-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            return body["choices"][0]["message"]["content"]

    except Exception as e:
        # LLM failed — fall back to truncated body
        print(f"LLM summarization failed: {e}", file=sys.stderr)
        body = parsed.body[:500]
        return f"{body}\n\n**Action items:** (LLM unavailable — manual review)\n**Follow-up by:** (LLM unavailable — manual review)"


def build_markdown(parsed: ParsedInput, summary: str) -> str:
    """Build the output markdown with YAML frontmatter."""
    frontmatter = [
        "---",
        f"date: {parsed.date_str}",
        f"from: {parsed.sender}",
        f"topic: {parsed.subject}",
        f"source: {parsed.source}",
    ]

    if parsed.participants:
        frontmatter.append(f"participants: {', '.join(parsed.participants)}")

    frontmatter.append("---")
    frontmatter.append("")
    frontmatter.append(summary)

    return "\n".join(frontmatter) + "\n"


def write_vault_entry(
    parsed: ParsedInput,
    markdown: str,
    vault_root: Path,
) -> Path:
    """Write the markdown entry to the vault. Returns the output path."""
    source_dir = vault_root / parsed.source
    source_dir.mkdir(parents=True, exist_ok=True)

    h = dedup_hash(parsed.subject, parsed.date_str)
    slug = _slugify(parsed.subject)
    filename = f"{parsed.date_str}-{slug}-{h}.md"
    output_path = source_dir / filename

    output_path.write_text(markdown)
    return output_path


def ingest(
    text: str,
    source: str,
    subject: str | None = None,
    dry_run: bool = False,
    llm_verify_pii: bool = False,
    vault_root: Path = VAULT_ROOT,
) -> IngestResult:
    """
    Full ingestion pipeline: parse → PII strip → dedup → summarize → write.

    Args:
        text: Raw input text
        source: "email", "whatsapp", or "chatwoot"
        subject: Optional subject override
        dry_run: If True, don't write to disk
        llm_verify_pii: If True, run LLM PII verification
        vault_root: Root path for vault output

    Returns:
        IngestResult with output path, markdown content, and metadata
    """
    # 1. Parse input
    parser = PARSERS.get(source)
    if not parser:
        raise ValueError(f"Unknown source: {source}. Expected: {', '.join(PARSERS)}")
    parsed = parser(text, subject)

    # 2. PII strip
    pii_result = strip_pii(parsed.body, llm_verify=llm_verify_pii)
    parsed.body = pii_result.cleaned_text
    parsed.sender = strip_pii(parsed.sender).cleaned_text

    # 3. Dedup check
    if dedup_check(source, parsed.subject, parsed.date_str, vault_root):
        return IngestResult(
            output_path=None,
            markdown="",
            was_duplicate=True,
            pii_result=pii_result,
        )

    # 4. Summarize
    summary = summarize_llm(parsed)

    # 5. Build markdown
    markdown = build_markdown(parsed, summary)

    # 6. Write (unless dry-run)
    output_path = None
    if not dry_run:
        output_path = write_vault_entry(parsed, markdown, vault_root)

    return IngestResult(
        output_path=output_path,
        markdown=markdown,
        pii_result=pii_result,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Bernard's ingestion pipeline — ingest comms into the vault"
    )
    parser.add_argument(
        "--source", required=True, choices=["email", "whatsapp", "chatwoot"],
        help="Source type"
    )
    parser.add_argument(
        "--subject", default=None,
        help="Override subject/topic"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show output without writing to vault"
    )
    parser.add_argument(
        "--llm-verify-pii", action="store_true",
        help="Run LLM verification on PII stripping"
    )
    parser.add_argument(
        "--vault-root", default=None,
        help="Override vault root path"
    )
    args = parser.parse_args()

    vault_root = Path(args.vault_root) if args.vault_root else VAULT_ROOT

    text = sys.stdin.read()
    if not text.strip():
        print("Error: no input provided (pipe text via stdin)", file=sys.stderr)
        sys.exit(1)

    result = ingest(
        text=text,
        source=args.source,
        subject=args.subject,
        dry_run=args.dry_run,
        llm_verify_pii=args.llm_verify_pii,
        vault_root=vault_root,
    )

    if result.was_duplicate:
        print("Skipped: duplicate entry (subject+date hash match)", file=sys.stderr)
        sys.exit(0)

    if args.dry_run:
        print("--- DRY RUN (not written to disk) ---\n")

    print(result.markdown)

    if result.pii_result:
        print(result.pii_result.log_line(), file=sys.stderr)

    if result.output_path:
        print(f"Written to: {result.output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
