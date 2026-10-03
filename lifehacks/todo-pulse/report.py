#!/usr/bin/env python3
"""report.py — weekly TO-DO pulse email: slope, churn, and where new items come from.

Approach: everything is computed in SQL from collect.py's two tables. Counts carry
forward (a source's value on a date is its latest snapshot on or before it), because
backfilled history only has rows on days the file changed. Adds and removals come from
item lifetimes, so a flat net can still show heavy churn. An item first seen on its
source's very first snapshot is the seed, not an addition, and is never counted as one.

The body is aggregates plus section names only — no item text — and still goes through
grafana-remediate's SES sender, which runs its PHI gate before any egress.

Usage: report.py [--days 7] [--send]     (default prints the email; --send sends it)
"""

import argparse
import csv
import datetime
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import psql  # noqa: E402

SES_DIR = os.path.join(os.path.expanduser("~"), "Projects", "ai-skills",
                       "grafana-remediate", "workflow")


def rows(sql):
    return list(csv.DictReader(io.StringIO(psql(args=["--csv", "-c", sql]))))


def report(days, today):
    end = today.isoformat()
    per_source = rows(f"""
WITH asof AS (
  SELECT s.label,
    (SELECT open FROM snapshot WHERE source = s.label AND taken_on <= DATE '{end}'
       ORDER BY taken_on DESC LIMIT 1) AS now,
    (SELECT open FROM snapshot WHERE source = s.label
       AND taken_on <= DATE '{end}' - {days} ORDER BY taken_on DESC LIMIT 1) AS wk,
    (SELECT open FROM snapshot WHERE source = s.label
       AND taken_on <= DATE '{end}' - 28 ORDER BY taken_on DESC LIMIT 1) AS m4,
    (SELECT round((regr_slope(open, taken_on - DATE '2000-01-01') * 7)::numeric, 1)
       FROM snapshot WHERE source = s.label AND taken_on > DATE '{end}' - 28) AS slope,
    (SELECT never_verified FROM snapshot WHERE source = s.label
       ORDER BY taken_on DESC LIMIT 1) AS nv,
    (SELECT min(taken_on) FROM snapshot WHERE source = s.label) AS seeded
  FROM source s
)
SELECT a.label, a.now, a.now - a.wk AS d_wk, a.now - a.m4 AS d_m4, a.slope, a.nv,
  (SELECT count(*) FROM item i WHERE i.source = a.label AND i.first_seen > a.seeded
     AND i.first_seen > DATE '{end}' - {days}) AS added,
  (SELECT count(*) FROM item i WHERE i.source = a.label
     AND i.gone_on > DATE '{end}' - {days}) AS removed
FROM asof a WHERE a.now IS NOT NULL ORDER BY a.now DESC;""")

    by_kind = rows(f"""
SELECT i.origin_kind AS kind, count(*) AS n FROM item i
JOIN (SELECT source, min(taken_on) AS seeded FROM snapshot GROUP BY source) s
  ON s.source = i.source
WHERE i.first_seen > s.seeded AND i.first_seen > DATE '{end}' - {days}
GROUP BY 1 ORDER BY 2 DESC;""")

    by_section = rows(f"""
SELECT i.source, i.section, count(*) AS n FROM item i
JOIN (SELECT source, min(taken_on) AS seeded FROM snapshot GROUP BY source) s
  ON s.source = i.source
WHERE i.first_seen > s.seeded AND i.first_seen > DATE '{end}' - {days}
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10;""")

    # Total open at each of the last 8 week-ends, carried forward per source.
    weekly = rows(f"""
SELECT w::date AS week, sum((SELECT open FROM snapshot sn WHERE sn.source = s.label
  AND sn.taken_on <= w ORDER BY taken_on DESC LIMIT 1)) AS open
FROM generate_series(DATE '{end}' - 49, DATE '{end}', interval '7 days') w,
     source s GROUP BY 1 ORDER BY 1;""")

    # Headline slope: regression over the DAILY carried-forward total, not a sum of
    # per-source slopes — a source with four snapshots would otherwise dominate it.
    total_slope = rows(f"""
SELECT round((regr_slope(t.open, t.d - DATE '2000-01-01') * 7)::numeric, 1) AS slope
FROM (SELECT d::date AS d, sum((SELECT open FROM snapshot sn WHERE sn.source = s.label
        AND sn.taken_on <= d ORDER BY taken_on DESC LIMIT 1)) AS open
      FROM generate_series(DATE '{end}' - 27, DATE '{end}', interval '1 day') d,
           source s GROUP BY 1) t;""")[0]["slope"]

    def n(v):
        return int(v) if v not in (None, "") else None

    def signed(v):
        v = n(v)
        return "   —" if v is None else f"{v:+4d}"

    total = sum(n(r["now"]) for r in per_source)
    added = sum(n(r["added"]) for r in per_source)
    removed = sum(n(r["removed"]) for r in per_source)
    slope = float(total_slope or 0)

    lines = [
        f"{total} open TO-DOs across {len(per_source)} sources. This week "
        f"+{added} added, -{removed} removed (net {added - removed:+d}); "
        f"28-day slope {slope:+.0f}/week.",
        "",
        f"{'source':<15}{'open':>6}{'7d':>6}{'28d':>6}{'slope/wk':>10}"
        f"{'added':>7}{'removed':>9}{'unverified':>12}",
    ]
    for r in per_source:
        lines.append(
            f"{r['label']:<15}{n(r['now']):>6}{signed(r['d_wk']):>6}"
            f"{signed(r['d_m4']):>6}{(r['slope'] or '—'):>10}{r['added']:>7}"
            f"{r['removed']:>9}{r['nv']:>12}")

    lines += ["", "Trend (total open, weekly):"]
    peak = max((n(w["open"]) or 0) for w in weekly) or 1
    for w in weekly:
        v = n(w["open"]) or 0
        lines.append(f"  {w['week']}  {v:>5}  {'#' * round(40 * v / peak)}")

    if by_kind:
        lines += ["", "Where this week's additions came from:"]
        lines += [f"  {r['kind']:<20}{r['n']:>4}" for r in by_kind]
    if by_section:
        lines += ["", "Top sections adding this week:"]
        lines += [f"  {r['n']:>3}  {r['source']} · {(r['section'] or '<none>')[:90]}"
                  for r in by_section]

    subject = (f"[todo-pulse] {total} open ({added - removed:+d} wk, "
               f"slope {slope:+.0f}/wk)")
    return subject, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args()

    subject, body = report(args.days, datetime.date.today())
    if not args.send:
        print(subject, "\n", body, sep="\n")
        return 0
    sys.path.insert(0, SES_DIR)
    import email_ses  # grafana-remediate's sender: PHI gate + SES identity reuse
    result = email_ses.send(subject, body, dry_run=False)
    print(f"sent {result.get('message_id', '')} to {result['recipient']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
