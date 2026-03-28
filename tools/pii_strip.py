#!/usr/bin/env python3
"""
PII stripping utility for Bernard's ingestion pipeline.

Strips personally identifiable information from text using regex patterns,
replacing matches with category tags ([EMAIL], [PHONE], etc.).
Optional LLM verification pass via OpenRouter/Haiku.

Usage:
    from pii_strip import strip_pii
    cleaned, count = strip_pii(raw_text)

    # With LLM verification (requires OPENROUTER_API_KEY):
    cleaned, count = strip_pii(raw_text, llm_verify=True)

    # CLI:
    python3 pii_strip.py < input.txt
    python3 pii_strip.py --llm-verify < input.txt
"""

import re
import sys
import json
import os
from dataclasses import dataclass, field

# --- Regex patterns for PII detection ---

PATTERNS: list[tuple[str, re.Pattern]] = [
    # Email addresses
    ("EMAIL", re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    )),

    # Indonesian NIK in context ("NIK: 1234567890123456") — must be before generic digit patterns
    ("ID_NUMBER", re.compile(
        r'(?:NIK|KTP|BPJS|No\.?\s*ID)[\s:]*\d{10,16}',
        re.IGNORECASE
    )),

    # Indonesian KTP numbers (16 digits, structured)
    ("ID_NUMBER", re.compile(
        r'\b\d{2}(?:0[1-9]|[1-7]\d)\d{2}(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[012])\d{2}\d{4}\b'
    )),

    # Indonesian BPJS numbers (13 digits starting with 000)
    ("ID_NUMBER", re.compile(
        r'\b000\d{10}\b'
    )),

    # Passport numbers (1-2 letters + 6-9 digits)
    ("ID_NUMBER", re.compile(
        r'\b[A-Z]{1,2}\d{6,9}\b'
    )),

    # Phone numbers — Indonesian formats (+62xxx, 08xxx)
    ("PHONE", re.compile(
        r'(?:\+62|62|0)[\s-]?(?:\d[\s-]?){8,12}\b'
    )),

    # Phone numbers — international with + prefix
    ("PHONE", re.compile(
        r'\+\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b'
    )),

    # Monetary amounts with currency (Rp, IDR, $, USD, EUR)
    ("FINANCIAL", re.compile(
        r'(?:Rp\.?|IDR|USD|\$|EUR|€)\s*[\d.,]+(?:\s*(?:juta|ribu|rb|jt|million|k|m)\b)?',
        re.IGNORECASE
    )),

    # Credit card numbers (exactly 13-19 digits with separators, no letters adjacent)
    ("FINANCIAL", re.compile(
        r'(?<![A-Za-z])\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{1,7}\b'
    )),
]


@dataclass
class StripResult:
    """Result of PII stripping."""
    cleaned_text: str
    strip_count: int = 0
    categories: dict[str, int] = field(default_factory=dict)

    def log_line(self) -> str:
        if self.strip_count == 0:
            return "PII strip: 0 items found"
        cats = ", ".join(f"{k}={v}" for k, v in sorted(self.categories.items()))
        return f"PII strip: {self.strip_count} items replaced ({cats})"


def strip_pii(text: str, llm_verify: bool = False) -> StripResult:
    """
    Strip PII from text using regex patterns.

    Args:
        text: Raw input text
        llm_verify: If True, run an LLM pass to catch remaining PII

    Returns:
        StripResult with cleaned text, count, and categories
    """
    result = StripResult(cleaned_text=text)

    for tag, pattern in PATTERNS:
        def replacer(match, _tag=tag):
            result.strip_count += 1
            result.categories[_tag] = result.categories.get(_tag, 0) + 1
            return f"[{_tag}]"

        result.cleaned_text = pattern.sub(replacer, result.cleaned_text)

    if llm_verify and result.cleaned_text:
        result = _llm_verify_pass(result)

    return result


def _llm_verify_pass(result: StripResult) -> StripResult:
    """
    Send stripped text to Haiku for verification that no PII remains.
    If PII is found, replace it with tags.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        # Can't verify without API key — return as-is
        return result

    try:
        import urllib.request

        prompt = (
            "Review this text for any remaining personally identifiable information "
            "(names, emails, phone numbers, addresses, ID numbers, financial details). "
            "If you find PII, respond with a JSON array of objects: "
            '[{"text": "the PII found", "category": "EMAIL|PHONE|ID_NUMBER|FINANCIAL|NAME|ADDRESS"}]. '
            "If no PII remains, respond with an empty array: []\n\n"
            f"Text to review:\n{result.cleaned_text}"
        )

        payload = json.dumps({
            "model": "anthropic/claude-haiku-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
        }).encode()

        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read())
            content = body["choices"][0]["message"]["content"]

            # Try to parse JSON from response
            # Handle markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            findings = json.loads(content.strip())
            if isinstance(findings, list):
                for item in findings:
                    pii_text = item.get("text", "")
                    category = item.get("category", "PII")
                    if pii_text and pii_text in result.cleaned_text:
                        result.cleaned_text = result.cleaned_text.replace(
                            pii_text, f"[{category}]"
                        )
                        result.strip_count += 1
                        result.categories[category] = (
                            result.categories.get(category, 0) + 1
                        )

    except Exception:
        # LLM verification is best-effort — don't fail the pipeline
        pass

    return result


def main():
    """CLI entry point: reads stdin, strips PII, writes to stdout."""
    import argparse

    parser = argparse.ArgumentParser(description="Strip PII from text")
    parser.add_argument(
        "--llm-verify", action="store_true",
        help="Run LLM verification pass (requires OPENROUTER_API_KEY)"
    )
    args = parser.parse_args()

    text = sys.stdin.read()
    result = strip_pii(text, llm_verify=args.llm_verify)

    print(result.cleaned_text)
    print(f"\n---\n{result.log_line()}", file=sys.stderr)


if __name__ == "__main__":
    main()
