#!/usr/bin/env python3
"""Tests for the WA Follow-Up Tracker watcher."""

import sys
from pathlib import Path

# Ensure tools/ is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.wa_followup import detect_request, build_entry, process, _extract_contact, _extract_project


# --- Detection tests ---

def test_detects_request_patterns():
    """Request patterns should be detected."""
    requests = [
        "Can you send me the monthly report by Friday?",
        "Please send the updated budget to the team.",
        "Let me know when the lab results are ready.",
        "Following up on the IT infrastructure proposal.",
        "Could you check the Chatwoot integration status?",
        "When will the new clinic licenses be ready?",
        "I need you to prepare the board deck for Thursday.",
        "Please handle the Palm Emas reconciliation this week.",
        "Take care of the insurance renewal before end of month.",
        "Send me the guest feedback summary.",
        "Get me the updated construction timeline by Monday.",
        "Make sure the payroll is processed by Friday.",
    ]
    for msg in requests:
        assert detect_request(msg), f"Should detect request: {msg}"


def test_skips_social_messages():
    """Social/greeting messages should not trigger."""
    social = [
        "Hi Kezia, hope you're doing well!",
        "Thanks for the update!",
        "Happy birthday!",
        "Congratulations on the new role!",
        "Ok great, noted.",
        "Yes",
        "No worries at all.",
        "Got it",
        "FYI the meeting was moved to 3pm.",
        "Just letting you know I'll be late.",
    ]
    for msg in social:
        assert not detect_request(msg), f"Should skip social: {msg}"


def test_skips_fyi_messages():
    """FYI/informational messages should not trigger."""
    fyi = [
        "FYI the server migration is complete.",
        "Just so you know, the audit team will visit next week.",
        "For your information, the new policy starts Monday.",
    ]
    for msg in fyi:
        assert not detect_request(msg), f"Should skip FYI: {msg}"


def test_short_acknowledgments():
    """Short acknowledgments should not trigger."""
    acks = ["Ok", "Sure", "Agreed", "Noted", "Received", "Got it"]
    for msg in acks:
        assert not detect_request(msg), f"Should skip ack: {msg}"


# --- Contact extraction tests ---

def test_extract_contact():
    assert _extract_contact("Asked Kezia to send the report") == "Kezia"
    assert _extract_contact("Told Fitri to handle the reconciliation") == "Fitri"
    assert _extract_contact("Can you send me the report?") == "unknown"
    assert _extract_contact("to David Fu about the loan") == "David Fu"


# --- Project extraction tests ---

def test_extract_project():
    assert _extract_project("PMG board deck review") == "pmg"
    assert _extract_project("Padma Care lead follow-up") == "padma-care"
    assert _extract_project("Narawangsa guest complaint") == "narawangsa"
    assert _extract_project("Random unrelated task") == "general"
    assert _extract_project("Kalpa deployment schedule") == "kalpa"


# --- Entry building tests ---

def test_build_entry_has_frontmatter():
    entry = build_entry("Asked Kezia to send the monthly PMG report")
    assert "---" in entry
    assert 'type: followup' in entry
    assert 'status: waiting' in entry
    assert 'contact: "Kezia"' in entry
    assert 'related_project: "pmg"' in entry


def test_build_entry_has_trail():
    entry = build_entry("Please send the budget update")
    assert "## Trail" in entry
    assert "Initial request sent via WA" in entry


# --- Process function tests ---

def test_process_matches_request():
    result = process("Can you send me the monthly report?", dry_run=True)
    assert result["matched"] is True
    assert result["entry"] is not None
    assert result["output_path"] is None  # dry run


def test_process_skips_social():
    result = process("Thanks for the update!", dry_run=True)
    assert result["matched"] is False
    assert result["entry"] is None


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
