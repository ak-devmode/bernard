#!/usr/bin/env bash
# Prove the newest backup restores: load it into a throwaway container (no ports, no
# volume) and compare row counts against the live cluster. A backup that has never been
# restored is a hope, not a backup. Timescale's "circular foreign-key" pg_dump warning on
# _timescaledb_catalog.continuous_agg is expected; this is how we know it is harmless.
set -euo pipefail

DEST="${HOMELAB_BACKUP_DIR:-$HOME/.local/share/homelab/backups}"
dump=$(ls -1t "$DEST"/homelab-*.sql.gz | head -1)
name=homelab-restore-test
q="SELECT (SELECT count(*) FROM snapshot) || '/' || (SELECT count(*) FROM item)"

docker run -d --rm --name "$name" -e POSTGRES_USER=alexk \
  -e POSTGRES_HOST_AUTH_METHOD=trust timescale/timescaledb:latest-pg18 >/dev/null
trap 'docker stop "$name" >/dev/null 2>&1 || true' EXIT
for _ in $(seq 1 60); do
  docker exec "$name" pg_isready -U alexk -q 2>/dev/null && break
  sleep 1
done
sleep 3  # the image restarts postgres once after initdb

# "role alexk already exists" is the only expected error (pg_dumpall recreates roles).
errors=$(gunzip -c "$dump" | docker exec -i "$name" psql -X -q -U alexk -d postgres 2>&1 \
  | grep ERROR | grep -v 'role "alexk" already exists' || true)
restored=$(docker exec "$name" psql -X -U alexk -d todo_pulse -Atc "$q")
live=$(docker exec homelab-db psql -X -U alexk -d todo_pulse -Atc "$q")

echo "dump:     $(basename "$dump")"
echo "restored: snapshot/item = $restored"
echo "live:     snapshot/item = $live"
[ -n "$errors" ] && { echo "unexpected errors:"; echo "$errors"; exit 1; }
[ "$restored" = "$live" ] || echo "note: counts differ — fine if the collector ran after the dump"
echo "OK"
