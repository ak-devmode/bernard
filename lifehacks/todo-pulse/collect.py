#!/usr/bin/env python3
"""collect.py — daily snapshot of every plans-dir TO-DO.md into the homelab Postgres.

Approach:
  - Discover sources by globbing ~/Projects for */plans/TO-DO.md (depth <= 3), skipping
    linked git worktrees so a herdr lane never double-counts its parent repo.
  - Read each file from git at origin's default branch after a fetch, NOT the working
    tree: kalpa-docs is multi-author, and a local checkout can lag by days. Reading the
    committed blob also makes a daily snapshot identical in kind to a backfilled one.
  - Parse with todo-stats.py's parse_items (imported, never forked), so the session-start
    counter and this history can't disagree about what an item is.
  - Each open item gets a stable id = hash(source, normalised first line). Section is
    deliberately left out of the id: items move between sections and headings get
    re-dated, and either would otherwise read as one removal plus one addition.
    Editing an item's first line still does — a known, accepted limit.
  - --backfill replays git history (latest commit per day) into an empty source, so
    the slope exists on day one instead of after a month of cron runs.

Writes go through `psql` (stdin script with inline COPY), keeping this stdlib-only.
Connection comes from the usual PG* env vars; defaults target the homelab cluster.

Usage: collect.py [--backfill] [--rebuild] [--dry-run] [--only LABEL ...]
"""

import argparse
import csv
import datetime
import glob
import hashlib
import importlib.util
import io
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, "Projects")
TODO_STATS = os.path.join(PROJECTS, "ai-skills", "scripts", "todo-stats.py")
SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

PG_DEFAULTS = {"PGHOST": "127.0.0.1", "PGPORT": "5432", "PGUSER": "alexk",
               "PGDATABASE": "todo_pulse"}

ORIGIN_REF = re.compile(r"\b(Scope|Plan)\s+(\d+(?:\.\d+)*)", re.I)
# Heuristic over free-form ## headings — a trend signal, not a taxonomy. Order matters:
# "Phase 2 review deferrals" is a review deferral even inside a closeout section.
ORIGIN_KINDS = [
    ("review-deferral", re.compile(r"\breview\b|\bdeferr", re.I)),
    ("operational", re.compile(r"\boperational\b", re.I)),
    ("closeout-residual", re.compile(
        r"closeout|closed out|residual|leftover|wrap|follow-?ups?|fallout", re.I)),
    ("surfaced", re.compile(r"surfaced|found (?:while|during|building)|smoke|demo", re.I)),
    ("manual", re.compile(r"\(Alex\b", re.I)),
]


def load_todo_stats():
    spec = importlib.util.spec_from_file_location("todo_stats", TODO_STATS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ts = load_todo_stats()


def git(repo, *args, check=True, timeout=60):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {repo}: {p.stderr.strip()[:200]}")
    return p.stdout


def discover():
    found = {}
    for depth in ("*", "*/*", "*/*/*"):
        for todo in sorted(glob.glob(os.path.join(PROJECTS, depth, "plans", "TO-DO.md"))):
            plans_dir = os.path.dirname(todo)
            try:
                repo = git(plans_dir, "rev-parse", "--show-toplevel").strip()
                git_dir = git(plans_dir, "rev-parse", "--absolute-git-dir").strip()
                common = os.path.abspath(os.path.join(
                    plans_dir, git(plans_dir, "rev-parse", "--git-common-dir").strip()))
            except (RuntimeError, subprocess.TimeoutExpired):
                continue
            if os.path.realpath(git_dir) != os.path.realpath(common):
                continue  # linked worktree — the parent repo is the source
            label = ts.label_for(plans_dir)
            if label in found:
                print(f"warn: duplicate label {label}: {todo} (keeping "
                      f"{found[label]['repo']})", file=sys.stderr)
                continue
            ref = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD",
                      check=False).strip() or "HEAD"
            found[label] = {"label": label, "repo": repo, "ref": ref,
                            "todo_path": os.path.relpath(todo, repo)}
    return list(found.values())


def normalise(line):
    s = re.sub(r"^- \[[ xX]\]\s*", "", line)
    s = re.sub(r"[*~`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def origin_of(section):
    section = section or ""
    kind = next((k for k, rx in ORIGIN_KINDS if rx.search(section)), "other")
    m = ORIGIN_REF.search(section)
    ref = f"{m.group(1).title()} {m.group(2)}" if m else None
    return kind, ref


def snapshot_of(label, text, asof):
    """Parse one TO-DO.md text into (stats, open_item_rows) as of a given date."""
    items = ts.parse_items(text)
    open_items = [i for i in items if i["open"]]
    cutoff = asof - datetime.timedelta(days=ts.STALE_AFTER_DAYS)
    stale = sum(1 for i in open_items
                if (d := i["stamped"] or i["section_date"] or i["raised"]) and d < cutoff)
    closed = [i for i in items if not i["open"]]
    stats = {
        "open": len(open_items),
        "p1plus": sum(1 for i in open_items
                      if i["priority"] is not None and i["priority"] <= 1),
        "never_verified": sum(1 for i in open_items if not i["stamped"]),
        "stale": stale,
        "closed_in_place": sum(1 for i in closed if not ts.TOMBSTONE.search(i["text"])),
        "sections": len({i["section"] for i in items if i["section"]}),
    }
    rows, seen = [], {}
    for it in open_items:
        first = it["body"][0]
        key = f"{label}|{normalise(first)}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            key += f"#{seen[key]}"  # identical first lines: keep both, in file order
        kind, ref = origin_of(it["section"])
        title = re.sub(r"^- \[[ xX]\]\s*", "", first).strip()[:300]
        rows.append([hashlib.sha1(key.encode()).hexdigest()[:16], it["section"], kind,
                     ref, title, it["priority"],
                     it["stamped"].isoformat() if it["stamped"] else None])
    return stats, rows


def q(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def snapshot_sql(src, asof, sha, stats, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for r in rows:
        w.writerow(["" if v is None else v for v in r])
    d, s = q(asof.isoformat()), q(src["label"])
    cols = "open, p1plus, never_verified, stale, closed_in_place, sections"
    vals = ", ".join(str(stats[c.strip()]) for c in cols.split(","))
    return f"""
TRUNCATE cur;
COPY cur FROM STDIN (FORMAT csv);
{buf.getvalue()}\\.
INSERT INTO snapshot (source, taken_on, commit_sha, {cols})
VALUES ({s}, {d}, {q(sha)}, {vals})
ON CONFLICT (source, taken_on) DO UPDATE SET commit_sha = EXCLUDED.commit_sha,
  open = EXCLUDED.open, p1plus = EXCLUDED.p1plus,
  never_verified = EXCLUDED.never_verified, stale = EXCLUDED.stale,
  closed_in_place = EXCLUDED.closed_in_place, sections = EXCLUDED.sections;
INSERT INTO item (id, source, section, origin_kind, origin_ref, title, priority,
                  verified_on, first_seen, last_seen)
SELECT id, {s}, section, origin_kind, origin_ref, title, priority, verified_on, {d}, {d}
FROM cur
ON CONFLICT (id) DO UPDATE SET section = EXCLUDED.section,
  origin_kind = EXCLUDED.origin_kind, origin_ref = EXCLUDED.origin_ref,
  title = EXCLUDED.title, priority = EXCLUDED.priority,
  verified_on = EXCLUDED.verified_on,
  last_seen = GREATEST(item.last_seen, EXCLUDED.last_seen), gone_on = NULL;
UPDATE item SET gone_on = {d}
WHERE source = {s} AND gone_on IS NULL AND id NOT IN (SELECT id FROM cur);
"""


def psql(script=None, file=None, args=()):
    env = {**PG_DEFAULTS, **os.environ}
    cmd = ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", *args]
    if file:
        cmd += ["-f", file]
    p = subprocess.run(cmd, input=script, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"psql failed: {p.stderr.strip()[:500]}")
    return p.stdout


def latest_snapshot(label):
    out = psql(args=["-At", "-c",
                     f"SELECT max(taken_on) FROM snapshot WHERE source = {q(label)}"])
    return datetime.date.fromisoformat(out.strip()) if out.strip() else None


def history(src):
    """Latest commit per day touching the TO-DO file on src's ref, oldest first."""
    log = git(src["repo"], "log", "--format=%H %cs", src["ref"], "--", src["todo_path"])
    per_day = {}
    for line in log.splitlines():
        sha, day = line.split()
        per_day.setdefault(day, sha)  # log is newest-first: first hit is the day's last
    return sorted((datetime.date.fromisoformat(d), sha) for d, sha in per_day.items())


def plan_for(src, args, today):
    """Return [(date, sha)] to apply for this source."""
    head = git(src["repo"], "rev-parse", src["ref"]).strip()
    if args.dry_run:
        return (history(src) if args.backfill else []) + [(today, head)]
    last = latest_snapshot(src["label"])
    if args.backfill or args.rebuild:
        if last and not args.rebuild:
            print(f"{src['label']}: has history to {last}; backfill needs --rebuild",
                  file=sys.stderr)
            return []
        return [x for x in history(src) if x[0] < today] + [(today, head)]
    if last and last > today:
        return []
    return [(today, head)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--rebuild", action="store_true",
                    help="delete a source's rows, then backfill it")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    today = datetime.date.today()

    sources = [s for s in discover() if not args.only or s["label"] in args.only]
    if not args.dry_run:
        psql(file=SCHEMA)

    failures = 0
    for src in sources:
        try:
            if not args.no_fetch:
                git(src["repo"], "fetch", "--quiet", "origin", check=False)
            steps = plan_for(src, args, today)
            parts = ["BEGIN;",
                     "CREATE TEMP TABLE cur (id text, section text, origin_kind text, "
                     "origin_ref text, title text, priority smallint, verified_on date) "
                     "ON COMMIT DROP;",
                     f"INSERT INTO source VALUES ({q(src['label'])}, {q(src['repo'])}, "
                     f"{q(src['todo_path'])}, {q(src['ref'])}) ON CONFLICT (label) DO "
                     "UPDATE SET repo = EXCLUDED.repo, todo_path = EXCLUDED.todo_path, "
                     "ref = EXCLUDED.ref;"]
            if args.rebuild:
                parts += [f"DELETE FROM item WHERE source = {q(src['label'])};",
                          f"DELETE FROM snapshot WHERE source = {q(src['label'])};"]
            last_stats = None
            for day, sha in steps:
                text = git(src["repo"], "show", f"{sha}:{src['todo_path']}", check=False)
                if not text:
                    continue  # file absent at that commit (moved/created later)
                last_stats, rows = snapshot_of(src["label"], text, day)
                parts.append(snapshot_sql(src, day, sha, last_stats, rows))
            parts.append("COMMIT;")
            if last_stats is None:
                continue
            if not args.dry_run:
                psql(script="\n".join(parts))
            print(f"{src['label']}: {len(steps)} snapshot(s) via {src['ref']}, "
                  f"{last_stats['open']} open today"
                  + (" [dry-run]" if args.dry_run else ""))
        except Exception as e:  # noqa: BLE001 — one bad source must not hide the rest
            failures += 1
            print(f"error: {src['label']}: {e}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
