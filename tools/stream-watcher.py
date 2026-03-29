#!/usr/bin/env python3
"""
Stream watcher processing engine for Bernard's vault.

Reads a summarized message and checks it against active watcher trigger criteria.
For each match, generates the appropriate vault entry (followup, lead, todo).

Usage:
    python3 tools/stream-watcher.py --source whatsapp < summary.txt
    python3 tools/stream-watcher.py --source whatsapp --dry-run < summary.txt
    python3 tools/stream-watcher.py --watcher wa-followup-tracker < summary.txt
    python3 tools/stream-watcher.py --source email --dry-run < summary.txt
"""

import argparse
import importlib
import re
import sys
from pathlib import Path

# Repo root — stream-watcher.py lives in tools/
REPO_ROOT = Path(__file__).parent.parent
WORKSPACE = REPO_ROOT / "openclaw" / "workspace"
REGISTRY_PATH = WORKSPACE / "knowledge" / "stream-watchers.md"
KNOWLEDGE_ROOT = WORKSPACE / "knowledge"

# Watcher module mapping — name → module path under tools/watchers/
WATCHER_MODULES = {
    "wa-followup-tracker": "watchers.wa_followup",
    "lead-capture": "watchers.lead_capture",
    "todo-capture": "watchers.todo_capture",
}


def parse_registry(registry_path: Path = REGISTRY_PATH) -> list[dict]:
    """
    Parse the stream-watchers.md registry file.
    Returns a list of watcher dicts with keys: name, source, output, gate, status.
    """
    if not registry_path.exists():
        print(f"Warning: registry not found at {registry_path}", file=sys.stderr)
        return []

    text = registry_path.read_text()
    watchers = []

    # Parse the markdown table under "## Active Watchers"
    in_table = False
    header_seen = False
    for line in text.splitlines():
        if "## Active Watchers" in line:
            in_table = True
            continue
        if in_table and line.startswith("##"):
            break
        if not in_table:
            continue

        # Skip header row and separator
        stripped = line.strip()
        if not stripped or not stripped.startswith("|"):
            continue
        if "---" in stripped:
            header_seen = True
            continue
        if not header_seen:
            # This is the header row
            header_seen = False  # will be set on separator
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) >= 5:
            watchers.append({
                "name": cells[0],
                "source": cells[1],
                "output": cells[2],
                "gate": cells[3],
                "status": cells[4],
            })

    return watchers


def get_active_watchers(
    source: str | None = None,
    watcher_name: str | None = None,
) -> list[dict]:
    """
    Get active watchers, optionally filtered by source or name.
    """
    all_watchers = parse_registry()
    active = [w for w in all_watchers if w["status"] == "active"]

    if watcher_name:
        active = [w for w in active if w["name"] == watcher_name]
    elif source:
        # Match watchers whose source contains this source type
        active = [w for w in active if source in w["source"]]

    return active


def load_watcher_module(watcher_name: str):
    """
    Dynamically load a watcher module by name.
    Returns the module, which must have a process(text, dry_run) function.
    """
    module_path = WATCHER_MODULES.get(watcher_name)
    if not module_path:
        raise ValueError(f"No module mapping for watcher: {watcher_name}")

    # Add tools/ to path so watchers package is importable
    tools_dir = str(Path(__file__).parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    return importlib.import_module(module_path)


def process_message(
    text: str,
    source: str | None = None,
    watcher_name: str | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """
    Process a summarized message through matching watchers.

    Returns a list of results, each with:
        - watcher: name of the watcher that matched
        - matched: bool
        - output_path: path to created file (None if dry_run or no match)
        - entry: the generated markdown (if matched)
    """
    watchers = get_active_watchers(source=source, watcher_name=watcher_name)
    results = []

    for w in watchers:
        name = w["name"]
        try:
            module = load_watcher_module(name)
            result = module.process(text, dry_run=dry_run)
            results.append({
                "watcher": name,
                **result,
            })
        except Exception as e:
            print(f"Error in watcher {name}: {e}", file=sys.stderr)
            results.append({
                "watcher": name,
                "matched": False,
                "output_path": None,
                "entry": None,
                "error": str(e),
            })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Bernard's stream watcher — process summaries through active watchers"
    )
    parser.add_argument(
        "--source", default=None,
        help="Source type (whatsapp, email, etc.) — filters to matching watchers"
    )
    parser.add_argument(
        "--watcher", default=None,
        help="Run only the named watcher (e.g., wa-followup-tracker)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be created without writing to disk"
    )
    args = parser.parse_args()

    if not args.source and not args.watcher:
        print("Error: provide --source or --watcher", file=sys.stderr)
        sys.exit(1)

    text = sys.stdin.read()
    if not text.strip():
        print("No input provided (pipe text via stdin)", file=sys.stderr)
        sys.exit(0)

    results = process_message(
        text=text,
        source=args.source,
        watcher_name=args.watcher,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("--- DRY RUN ---\n")

    matched_any = False
    for r in results:
        if r.get("matched"):
            matched_any = True
            print(f"✓ {r['watcher']}: match")
            if r.get("entry"):
                print(r["entry"])
                print()
            if r.get("output_path") and not args.dry_run:
                print(f"  Written to: {r['output_path']}", file=sys.stderr)
        elif r.get("error"):
            print(f"✗ {r['watcher']}: error — {r['error']}", file=sys.stderr)
        else:
            print(f"· {r['watcher']}: no match")

    if not matched_any and not any(r.get("error") for r in results):
        print("No watchers matched this input.")


if __name__ == "__main__":
    main()
