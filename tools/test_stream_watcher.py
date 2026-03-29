#!/usr/bin/env python3
"""
Integration tests for the stream watcher framework.

Tests registry parsing, routing, dry-run mode, and end-to-end watcher
processing through the framework.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import importlib.util

# Load stream-watcher.py as a module (hyphen in name requires manual loading)
spec = importlib.util.spec_from_file_location(
    "stream_watcher",
    Path(__file__).parent / "stream-watcher.py"
)
sw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sw)


# --- Framework tests ---

def test_registry_parsing():
    """Registry should parse all three watchers from stream-watchers.md."""
    watchers = sw.parse_registry()
    assert len(watchers) == 3, f"Expected 3 watchers, got {len(watchers)}"
    names = {w["name"] for w in watchers}
    assert names == {"wa-followup-tracker", "lead-capture", "todo-capture"}


def test_registry_fields():
    """Each watcher should have all required fields."""
    watchers = sw.parse_registry()
    for w in watchers:
        assert "name" in w
        assert "source" in w
        assert "output" in w
        assert "gate" in w
        assert "status" in w
        assert w["status"] == "active"


def test_routing_whatsapp():
    """WhatsApp source should route to wa-followup and todo, not lead-capture."""
    watchers = sw.get_active_watchers(source="whatsapp")
    names = {w["name"] for w in watchers}
    assert "wa-followup-tracker" in names
    assert "todo-capture" in names
    assert "lead-capture" not in names


def test_routing_email():
    """Email source should route to todo-capture only."""
    watchers = sw.get_active_watchers(source="email")
    names = {w["name"] for w in watchers}
    assert "todo-capture" in names
    assert "wa-followup-tracker" not in names
    assert "lead-capture" not in names


def test_routing_lead_group():
    """Bali-year-group source should route to lead-capture only."""
    watchers = sw.get_active_watchers(source="bali-year-group")
    names = {w["name"] for w in watchers}
    assert "lead-capture" in names
    assert "wa-followup-tracker" not in names
    assert "todo-capture" not in names


def test_routing_by_name():
    """--watcher flag should return only the named watcher."""
    watchers = sw.get_active_watchers(watcher_name="wa-followup-tracker")
    assert len(watchers) == 1
    assert watchers[0]["name"] == "wa-followup-tracker"


def test_routing_unknown_source():
    """Unknown source should return no watchers."""
    watchers = sw.get_active_watchers(source="carrier-pigeon")
    assert len(watchers) == 0


# --- Dry-run tests ---

def test_dry_run_wa_followup():
    """Dry run: WA request should match but not write files."""
    results = sw.process_message(
        "Please send me the PMG report by Friday",
        source="whatsapp",
        dry_run=True,
    )
    followup_results = [r for r in results if r["watcher"] == "wa-followup-tracker"]
    assert len(followup_results) == 1
    assert followup_results[0]["matched"] is True
    assert followup_results[0]["output_path"] is None  # dry run


def test_dry_run_no_files_written():
    """Dry run should never write any files."""
    results = sw.process_message(
        "Can you review the board deck?",
        source="whatsapp",
        dry_run=True,
    )
    for r in results:
        assert r.get("output_path") is None


# --- End-to-end tests ---

def test_e2e_wa_followup_request():
    """WA outbound request → followup entry created."""
    results = sw.process_message(
        "Minta Kezia tolong kirimkan laporan keuangan PMG",
        watcher_name="wa-followup-tracker",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is True
    assert "Kezia" in results[0]["entry"]
    assert "pmg" in results[0]["entry"]


def test_e2e_wa_social_no_match():
    """Social WA message → no followup entry."""
    results = sw.process_message(
        "Thanks for the update!",
        watcher_name="wa-followup-tracker",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is False


def test_e2e_lead_capture_match():
    """Health inquiry → lead entry with HubSpot draft."""
    results = sw.process_message(
        "My friend Sarah needs a good doctor in Canggu for back pain",
        watcher_name="lead-capture",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is True
    assert "Sarah" in results[0]["entry"]
    assert "HubSpot" in results[0]["entry"]


def test_e2e_lead_general_chat_no_match():
    """General chat → no lead entry."""
    results = sw.process_message(
        "Great restaurant recommendation in Ubud!",
        watcher_name="lead-capture",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is False


def test_e2e_todo_direct_request():
    """Direct actionable request → todo with alignment score."""
    results = sw.process_message(
        "Can you approve the vendor contract by Thursday?",
        watcher_name="todo-capture",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is True
    assert "alignment:" in results[0]["entry"]
    assert "status: proposed" in results[0]["entry"]


def test_e2e_todo_newsletter_no_match():
    """Newsletter → no todo entry."""
    results = sw.process_message(
        "Weekly newsletter: top stories in healthcare this week.",
        watcher_name="todo-capture",
        dry_run=True,
    )
    assert len(results) == 1
    assert results[0]["matched"] is False


# --- Edge cases ---

def test_multiple_watchers_same_message():
    """A WA message can trigger both followup and todo watchers."""
    results = sw.process_message(
        "Can you please send me the updated PMG budget by Friday?",
        source="whatsapp",
        dry_run=True,
    )
    matched = [r for r in results if r.get("matched")]
    watcher_names = {r["watcher"] for r in matched}
    # This should match both wa-followup and todo-capture
    assert "wa-followup-tracker" in watcher_names
    assert "todo-capture" in watcher_names


def test_empty_input():
    """Empty input → no matches, no crashes."""
    results = sw.process_message(
        "",
        source="whatsapp",
        dry_run=True,
    )
    for r in results:
        assert r.get("matched") is False


def test_malformed_input():
    """Garbage input → no crash, no match."""
    results = sw.process_message(
        "asdlkfj 239847 !@#$%^&*()",
        source="whatsapp",
        dry_run=True,
    )
    for r in results:
        assert not r.get("error"), f"Should not error: {r.get('error')}"


# --- Run all tests ---

if __name__ == "__main__":
    test_funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
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
