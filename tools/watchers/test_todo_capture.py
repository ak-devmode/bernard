#!/usr/bin/env python3
"""Tests for the Intent-Aligned Todo Capture watcher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.todo_capture import (
    detect_ask, build_entry, process,
    _extract_asker, _score_alignment, _load_priorities,
)


# --- Detection tests ---

def test_detects_actionable_asks():
    """Actionable asks directed at Alex should be detected."""
    asks = [
        "Can you review the Q1 board deck by Thursday?",
        "Please approve the vendor contract before end of week.",
        "We need your input on the clinic expansion proposal.",
        "Action required: sign off on the new hiring budget.",
        "Deadline is Friday for the investor update presentation.",
        "Could you provide feedback on the marketing plan?",
        "Decision needed on the Surabaya clinic lease terms.",
        "Urgent: approve the emergency maintenance budget.",
        "Follow up with Palm Emas on the outstanding payment.",
    ]
    for msg in asks:
        assert detect_ask(msg), f"Should detect ask: {msg}"


def test_detects_bahasa_asks():
    """Bahasa actionable asks should be detected."""
    asks = [
        "Tolong review dokumen kontrak ini.",
        "Mohon persetujuan untuk budget marketing.",
        "Bisa tolong tandatangani surat ini?",
        "Perlu keputusan dari Bapak soal lease.",
        "Segera approve PO yang sudah pending.",
        "Deadline sebelum Jumat untuk laporan ini.",
    ]
    for msg in asks:
        assert detect_ask(msg), f"Should detect Bahasa ask: {msg}"


def test_skips_newsletters():
    """Newsletters and automated content should not trigger."""
    noise = [
        "Weekly newsletter: top stories in healthcare this week.",
        "Monthly report from the analytics dashboard — automated.",
        "Unsubscribe from this mailing list.",
        "No-reply: your receipt is attached.",
        "FYI the quarterly numbers are in — for your reference.",
    ]
    for msg in noise:
        assert not detect_ask(msg), f"Should skip newsletter: {msg}"


def test_skips_mass_messages():
    """Mass/group messages should not trigger."""
    mass = [
        "Dear all, please note the office will be closed Monday.",
        "Hi everyone, team lunch at 12pm tomorrow.",
        "All-staff: new parking policy effective next week.",
    ]
    for msg in mass:
        assert not detect_ask(msg), f"Should skip mass message: {msg}"


# --- Asker extraction ---

def test_extract_asker():
    assert _extract_asker("From: Kezia about the monthly report") == "Kezia"
    assert _extract_asker("David Fu asked for the loan documents") == "David Fu"
    assert _extract_asker("Sandy Stone: can you review this?") == "Sandy Stone"
    assert _extract_asker("Please send the report") == "Unknown"


# --- Alignment scoring ---

def test_alignment_with_no_priorities():
    """With no priorities set, everything scores unrelated."""
    alignment, match = _score_alignment("Can you review the board deck?", [])
    assert alignment == "unrelated"
    assert match == ""


def test_alignment_with_matching_priority():
    """Direct keyword match should score as aligned."""
    priorities = ["PMG clinic expansion", "Kalpa FHIR integration", "Narawangsa renovation"]
    alignment, match = _score_alignment(
        "Can you review the PMG clinic expansion proposal?",
        priorities
    )
    assert alignment == "aligned"
    assert "clinic expansion" in match.lower()


def test_alignment_adjacent():
    """Same domain but not direct match should score adjacent."""
    priorities = ["PMG clinic expansion", "Kalpa FHIR integration"]
    alignment, match = _score_alignment(
        "Review the PMG staff schedule for next month",
        priorities
    )
    # PMG domain overlaps but "staff schedule" != "clinic expansion"
    assert alignment in ("aligned", "adjacent")


def test_alignment_unrelated():
    """Unrelated ask should score unrelated."""
    priorities = ["PMG clinic expansion", "Kalpa FHIR integration"]
    alignment, _ = _score_alignment(
        "Can you pick up groceries on the way home?",
        priorities
    )
    assert alignment == "unrelated"


# --- Entry building ---

def test_build_entry_has_frontmatter():
    entry = build_entry("From: Kezia — can you approve the PMG budget?")
    assert "type: todo" in entry
    assert "status: proposed" in entry
    assert 'from: "Kezia"' in entry


def test_build_entry_has_intent():
    entry = build_entry("Can you review the vendor contract?")
    assert "## Alex's Likely Intent" in entry
    assert "## If Accepted" in entry


def test_proposed_status_not_auto_promoted():
    """Todos must always start as 'proposed', never 'accepted'."""
    entry = build_entry("Urgent: approve the emergency budget now!")
    assert "status: proposed" in entry
    assert "status: accepted" not in entry


# --- Process function ---

def test_process_matches_ask():
    result = process("Can you review the quarterly report?", dry_run=True)
    assert result["matched"] is True
    assert result["entry"] is not None


def test_process_skips_newsletter():
    result = process("Weekly newsletter: top stories in healthcare.", dry_run=True)
    assert result["matched"] is False


def test_process_empty_input():
    result = process("", dry_run=True)
    assert result["matched"] is False


# --- Run all tests ---

if __name__ == "__main__":
    test_funcs = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for fn in test_funcs:
        try:
            fn()
            passed += 1
            print(f"  ✓ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {fn.__name__}: {type(e).__name__}: {e}")

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
