-- todo-pulse schema. Applied idempotently by collect.py on every run.
--
-- Two grains: `snapshot` is one row per source per day (the trend line), `item` is one
-- row per TO-DO item ever seen, with its lifetime (first_seen .. gone_on). Adds and
-- removals come from item lifetimes, not from count deltas, so "+4 net" can be read as
-- "+30 added, -26 removed" — the churn a count hides.

CREATE TABLE IF NOT EXISTS source (
  label      text PRIMARY KEY,           -- kalpa, pmg, iris, ai-skills, ...
  repo       text NOT NULL,              -- absolute repo root
  todo_path  text NOT NULL,              -- repo-relative path to TO-DO.md
  ref        text NOT NULL               -- git ref read, e.g. origin/main
);

CREATE TABLE IF NOT EXISTS snapshot (
  source          text NOT NULL REFERENCES source(label),
  taken_on        date NOT NULL,
  commit_sha      text,
  open            int  NOT NULL,
  p1plus          int  NOT NULL,
  never_verified  int  NOT NULL,
  stale           int  NOT NULL,
  closed_in_place int  NOT NULL,
  sections        int  NOT NULL,
  PRIMARY KEY (source, taken_on)
);

CREATE TABLE IF NOT EXISTS item (
  id          text PRIMARY KEY,          -- hash of source + normalised first line
  source      text NOT NULL REFERENCES source(label),
  section     text,                      -- current ## heading
  origin_kind text,                      -- review-deferral | closeout-residual | operational | surfaced | manual | other
  origin_ref  text,                      -- "Plan 149.2", "Scope 116", ...
  title       text NOT NULL,
  priority    smallint,
  verified_on date,
  first_seen  date NOT NULL,
  last_seen   date NOT NULL,
  gone_on     date                       -- first snapshot it was absent from; NULL while open
);

CREATE INDEX IF NOT EXISTS item_source_open ON item (source) WHERE gone_on IS NULL;
CREATE INDEX IF NOT EXISTS item_first_seen ON item (first_seen);
CREATE INDEX IF NOT EXISTS item_gone_on ON item (gone_on);
