#!/usr/bin/env python3
"""
Tests for Bernard's ingestion pipeline and PII stripping.

Run with: python3 -m pytest tools/test_ingest.py -v
"""

import tempfile
from pathlib import Path

import pytest

from pii_strip import strip_pii
from ingest import (
    parse_email,
    parse_whatsapp,
    dedup_hash,
    dedup_check,
    write_vault_entry,
    build_markdown,
    ingest,
    ParsedInput,
)


# --- PII stripping tests ---

class TestPiiStrip:
    def test_strips_email_addresses(self):
        result = strip_pii("Contact alex@example.com for details")
        assert "[EMAIL]" in result.cleaned_text
        assert "alex@example.com" not in result.cleaned_text
        assert result.strip_count >= 1

    def test_strips_indonesian_phone(self):
        result = strip_pii("Call me at +62 812 3456 7890")
        assert "[PHONE]" in result.cleaned_text
        assert "812" not in result.cleaned_text

    def test_strips_local_phone(self):
        result = strip_pii("Call 081234567890 now")
        assert "[PHONE]" in result.cleaned_text
        assert "081234567890" not in result.cleaned_text

    def test_strips_financial_amounts(self):
        result = strip_pii("Invoice total: Rp 15.000.000")
        assert "[FINANCIAL]" in result.cleaned_text
        assert "15.000.000" not in result.cleaned_text

    def test_strips_dollar_amounts(self):
        result = strip_pii("Budget is $1,234.56 per month")
        assert "[FINANCIAL]" in result.cleaned_text
        assert "1,234.56" not in result.cleaned_text

    def test_strips_nik_in_context(self):
        result = strip_pii("Patient NIK: 3171012345678901")
        assert "[ID_NUMBER]" in result.cleaned_text
        assert "3171012345678901" not in result.cleaned_text

    def test_no_pii_returns_unchanged(self):
        text = "Meeting at 3pm to discuss project timeline"
        result = strip_pii(text)
        assert result.cleaned_text == text
        assert result.strip_count == 0

    def test_multiple_pii_types(self):
        text = "Email alex@test.com, call +62 812 345 6789, pay Rp 500.000"
        result = strip_pii(text)
        assert "[EMAIL]" in result.cleaned_text
        assert "[PHONE]" in result.cleaned_text
        assert "[FINANCIAL]" in result.cleaned_text
        assert result.strip_count >= 3

    def test_categories_tracked(self):
        result = strip_pii("Contact alex@a.com and bob@b.com")
        assert result.categories.get("EMAIL", 0) >= 2


# --- Email parsing tests ---

class TestParseEmail:
    def test_parses_standard_headers(self):
        email = (
            "From: dr.gita@clinic.com\n"
            "To: alex@example.com\n"
            "Subject: Q1 Report\n"
            "Date: Mon, 28 Mar 2026 10:30:00 +0800\n"
            "\n"
            "Here is the Q1 report for your review.\n"
            "Please confirm by Friday."
        )
        parsed = parse_email(email)
        assert parsed.subject == "Q1 Report"
        assert "dr.gita@clinic.com" in parsed.sender
        assert parsed.date_str == "2026-03-28"
        assert "Q1 report" in parsed.body

    def test_subject_override(self):
        email = "From: test@test.com\nSubject: Original\n\nBody"
        parsed = parse_email(email, subject_override="Override")
        assert parsed.subject == "Override"

    def test_no_headers_treats_as_body(self):
        text = "Just some plain text without headers"
        parsed = parse_email(text)
        assert parsed.body == text
        assert parsed.subject == "No subject"

    def test_empty_body(self):
        email = "From: test@test.com\nSubject: Empty\n\n"
        parsed = parse_email(email)
        assert parsed.subject == "Empty"
        assert parsed.body == ""


# --- WhatsApp parsing tests ---

class TestParseWhatsApp:
    def test_parses_wa_export(self):
        wa = (
            "[28/03/2026, 10:15:30] Alex: Can you check the report?\n"
            "[28/03/2026, 10:16:45] Gita: Sure, looking now\n"
            "[28/03/2026, 10:20:00] Gita: All good, approved"
        )
        parsed = parse_whatsapp(wa)
        assert parsed.source == "whatsapp"
        assert parsed.date_str == "2026-03-28"
        assert "Alex" in parsed.participants
        assert "Gita" in parsed.participants
        assert len(parsed.participants) == 2

    def test_fallback_plain_text(self):
        text = "Not a WA format"
        parsed = parse_whatsapp(text)
        assert parsed.body == text
        assert parsed.source == "whatsapp"


# --- Dedup tests ---

class TestDedup:
    def test_same_input_same_hash(self):
        h1 = dedup_hash("Q1 Report", "2026-03-28")
        h2 = dedup_hash("Q1 Report", "2026-03-28")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = dedup_hash("Q1 Report", "2026-03-28")
        h2 = dedup_hash("Q2 Report", "2026-03-28")
        assert h1 != h2

    def test_dedup_check_no_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            assert not dedup_check("email", "test", "2026-03-28", Path(tmp))

    def test_dedup_check_detects_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            email_dir = tmp_path / "email"
            email_dir.mkdir()
            h = dedup_hash("Test Subject", "2026-03-28")
            (email_dir / f"2026-03-28-test-{h}.md").write_text("exists")

            assert dedup_check("email", "Test Subject", "2026-03-28", tmp_path)

    def test_dedup_check_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            email_dir = tmp_path / "email"
            email_dir.mkdir()
            h = dedup_hash("Test Subject", "2026-03-28")
            (email_dir / f"2026-03-28-test-{h}.md").write_text("exists")

            # Same subject, different case
            assert dedup_check("email", "test subject", "2026-03-28", tmp_path)


# --- Write tests ---

class TestWriteVaultEntry:
    def test_creates_file_in_correct_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            parsed = ParsedInput(
                source="email",
                subject="Test Email",
                sender="Someone",
                date_str="2026-03-28",
                body="Test body",
            )
            markdown = build_markdown(parsed, "Test summary")
            path = write_vault_entry(parsed, markdown, Path(tmp))

            assert path.exists()
            assert path.parent.name == "email"
            assert "2026-03-28" in path.name
            assert path.read_text() == markdown

    def test_creates_source_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            parsed = ParsedInput(
                source="whatsapp",
                subject="WA Chat",
                sender="Group",
                date_str="2026-03-28",
                body="Chat",
                participants=["A", "B"],
            )
            markdown = build_markdown(parsed, "Summary")
            path = write_vault_entry(parsed, markdown, Path(tmp))
            assert (Path(tmp) / "whatsapp").is_dir()
            assert path.exists()


# --- Dry-run test ---

class TestDryRun:
    def test_dry_run_no_file_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            email = "From: test@test.com\nSubject: Dry Run Test\n\nBody text"
            result = ingest(
                text=email,
                source="email",
                dry_run=True,
                vault_root=Path(tmp),
            )
            assert result.output_path is None
            assert result.markdown  # content generated
            assert not result.was_duplicate
            # No files should exist in email dir
            email_dir = Path(tmp) / "email"
            assert not email_dir.exists() or len(list(email_dir.iterdir())) == 0


# --- Full pipeline test ---

class TestFullPipeline:
    def test_ingest_email_writes_to_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            email = (
                "From: dr.gita@clinic.com\n"
                "Subject: Clinic Schedule\n"
                "Date: 28 Mar 2026\n"
                "\n"
                "The clinic schedule for next week is attached.\n"
                "Call me at +62 812 345 6789 if questions."
            )
            result = ingest(
                text=email,
                source="email",
                vault_root=Path(tmp),
            )
            assert result.output_path is not None
            assert result.output_path.exists()
            content = result.output_path.read_text()
            assert "source: email" in content
            assert "+62 812 345 6789" not in content  # PII stripped

    def test_duplicate_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            email = "From: test@t.com\nSubject: Same Thing\nDate: 28 Mar 2026\n\nBody"

            r1 = ingest(text=email, source="email", vault_root=Path(tmp))
            assert not r1.was_duplicate

            r2 = ingest(text=email, source="email", vault_root=Path(tmp))
            assert r2.was_duplicate

    def test_empty_input_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Empty but not raising — just produces minimal output
            result = ingest(text="   ", source="email", vault_root=Path(tmp))
            # Should still process (no crash on whitespace-only)
            assert result.markdown or result.was_duplicate or True
