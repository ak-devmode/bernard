#!/usr/bin/env python3
"""Tests for the Lead Capture watcher."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from watchers.lead_capture import (
    detect_lead, build_entry, process,
    _extract_name, _determine_product_fit, _determine_urgency,
)


# --- Detection tests ---

def test_detects_health_inquiries():
    """Health-related inquiries should be detected as leads."""
    leads = [
        "Does anyone know a good doctor in Canggu? My friend Sarah has been having back pain.",
        "Looking for a specialist for my husband, he needs a cardiologist.",
        "Can anyone recommend a good dentist in Sanur?",
        "We need help navigating the hospital system here, my mother is visiting and fell ill.",
        "Anyone know about medical advocacy services in Bali?",
        "My friend needs a medical check-up, preferably English speaking.",
        "Emergency — does anyone know an urgent care near Seminyak?",
        "Interested in Padma Care services for expat health coordination.",
    ]
    for msg in leads:
        assert detect_lead(msg), f"Should detect lead: {msg}"


def test_detects_bahasa_health_inquiries():
    """Bahasa health inquiries should also be detected."""
    leads = [
        "Cari dokter spesialis jantung di Denpasar",
        "Teman saya sakit, butuh rekomendasi rumah sakit",
        "Ada yang bisa bantu soal BPJS? Bagaimana caranya?",
        "Butuh dokter anak yang bisa bahasa Inggris",
        "Keluarga saya perlu medical check-up",
    ]
    for msg in leads:
        assert detect_lead(msg), f"Should detect Bahasa lead: {msg}"


def test_skips_general_discussion():
    """General health discussion and news should not trigger."""
    non_leads = [
        "Just sharing this article about healthcare in Indonesia.",
        "FYI there's a new study about tropical diseases.",
        "Covid vaccination update for Bali residents.",
        "Good morning everyone! How are you all doing?",
        "Anyone else dealing with the heat this week?",
        "Great restaurant recommendation in Ubud.",
    ]
    for msg in non_leads:
        assert not detect_lead(msg), f"Should skip non-lead: {msg}"


def test_skips_bahasa_news():
    """Bahasa news/article sharing should not trigger."""
    non_leads = [
        "Berita tentang rumah sakit baru di Denpasar.",
        "Artikel menarik soal kesehatan di Indonesia.",
    ]
    for msg in non_leads:
        assert not detect_lead(msg), f"Should skip Bahasa non-lead: {msg}"


# --- Name extraction ---

def test_extract_name():
    assert _extract_name("My friend Sarah needs a doctor") == "Sarah"
    assert _extract_name("John Smith is looking for a specialist") == "John Smith"
    assert _extract_name("Namanya Lisa, dia butuh dokter") == "Lisa"
    assert _extract_name("Can anyone help with healthcare?") == "Unknown"


# --- Product fit ---

def test_product_fit_advocacy():
    assert _determine_product_fit("need help navigating the hospital system") == "Advocacy"
    assert _determine_product_fit("help with BPJS insurance claim") == "Advocacy"
    assert _determine_product_fit("bantu koordinasi dengan rumah sakit") == "Advocacy"


def test_product_fit_concierge():
    assert _determine_product_fit("looking for a premium health screening") == "Concierge"
    assert _determine_product_fit("want an executive annual checkup") == "Concierge"
    assert _determine_product_fit("interested in home visit doctor service") == "Concierge"


def test_product_fit_unclear():
    assert _determine_product_fit("need a good doctor in Canggu") == "Unclear"


# --- Urgency ---

def test_urgency_detection():
    assert _determine_urgency("Emergency — need a doctor now!") == "high"
    assert _determine_urgency("Need a specialist this week") == "medium"
    assert _determine_urgency("Thinking about getting a check-up sometime") == "low"
    assert _determine_urgency("Darurat, tolong bantu!") == "high"
    assert _determine_urgency("Butuh dokter segera") == "high"


# --- Entry building ---

def test_build_entry_has_hubspot_fields():
    entry = build_entry("My friend Sarah needs a doctor in Canggu for back pain")
    assert "HubSpot Draft Fields" in entry
    assert "Contact name: Sarah" in entry
    assert "Pipeline: Padma Care" in entry
    assert "Stage: New Lead" in entry


def test_build_entry_has_actions():
    entry = build_entry("Looking for medical advocacy in Bali")
    assert "Enter in HubSpot" in entry
    assert "Assign drip sequence" in entry
    assert "Initial follow-up by" in entry


# --- Process function ---

def test_process_matches_lead():
    result = process("My friend Sarah needs a good doctor in Bali", dry_run=True)
    assert result["matched"] is True
    assert result["entry"] is not None
    assert "Sarah" in result["entry"]


def test_process_skips_non_lead():
    result = process("Great weather today in Canggu!", dry_run=True)
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
