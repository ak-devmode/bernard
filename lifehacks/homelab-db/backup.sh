#!/usr/bin/env bash
# Nightly logical backup of the whole homelab cluster.
#
# Approach: pg_dumpall inside the container (no client/server version skew), gzip to a
# dated file, keep the newest $KEEP. Writes to the same disk as the volume, so it guards
# against bad migrations and fat-fingered DELETEs, not disk loss — off-box copy is a
# separate, later step. Read-back check: a dump that gunzips to nothing fails the unit
# rather than rotating a good backup out.
set -euo pipefail

DEST="${HOMELAB_BACKUP_DIR:-$HOME/.local/share/homelab/backups}"
KEEP="${HOMELAB_BACKUP_KEEP:-14}"
mkdir -p "$DEST"

out="$DEST/homelab-$(date +%F).sql.gz"
docker exec homelab-db sh -c 'pg_dumpall -U "$POSTGRES_USER"' | gzip > "$out.tmp"

if ! gunzip -c "$out.tmp" | grep -q "PostgreSQL database cluster dump complete"; then
  rm -f "$out.tmp"
  echo "backup incomplete — kept previous backups untouched" >&2
  exit 1
fi
mv "$out.tmp" "$out"

ls -1t "$DEST"/homelab-*.sql.gz | tail -n +"$((KEEP + 1))" | xargs -r rm -f
echo "wrote $out ($(du -h "$out" | cut -f1))"
