# Production Migration Runbook — 16 March 2026

> Full migration from Chatwoot Cloud (app.chatwoot.com) to Production self-hosted
> (chat.pbmcgroup.com). Executed on 16 March 2026 — cutover immediately after migration completes.
> **Go-live: 17 March 2026.**

---

## Target Environment

| | Cloud (source) | Production (target) |
|---|---|---|
| URL | app.chatwoot.com | chat.pbmcgroup.com |
| Account ID | 152163 | 1 |
| Token | rzHUgBP9pJgBVS8RwWmFU5De | xyu8g4yHcfapYAJjcrTQGzVi |
| Docker container | — | chatwoot-web-production (port 3002) |
| Database | — | chatwoot_production |

## Differences from Staging Migration

- **Separate state file**: `state_production.json` (do not use `state.json` from the migration/ folder)
- **Target URL**: `chat.pbmcgroup.com` not `staging-chat.pbmcgroup.com`
- **Full migration**: all ~2,200+ conversations (not a delta)
- **Contacts**: production already has 28k contacts — script will reuse by phone number, will not overwrite

---

## Preparation

```bash
cd "D:/2 - Padma/7 - Chatwoot/migration_production"

# Verify state is clean (must be empty for first full migration)
cat state_production.json
# Expected: {"conversation_map": {}, "contact_map": {}, "agent_map": {}, "done": {"conversations": []}}

# Remove old checkpoints if any exist from previous tests
rm -f export_incoming_checkpoint.json
rm -f fetch_outgoing_ckpt_prod.json
rm -f all_conv_ids.json
rm -f missing_incoming.json
rm -f outgoing_timestamp_updates.json
```

---

## Step 1 — Migrate all conversations

```bash
python3 migrate_full.py
```

- Reads `state_production.json` (initially empty)
- Fetches all conversations from cloud, skips those already in state
- For each conversation: search contact by phone → reuse if found, create new if not
- Migrates outgoing messages via API
- Updates `state_production.json` and creates `all_conv_ids.json`
- **Resume-capable**: if interrupted, re-run — already-done conversations will be skipped
- Estimated time: ~60 minutes

---

## Step 2 — Export incoming messages (customer)

```bash
python3 export_incoming.py
```

- Reads `all_conv_ids.json`
- Exports incoming messages from cloud with original timestamps
- Resume-capable via `export_incoming_checkpoint.json`
- Output: `missing_incoming.json`
- Estimated time: ~30 minutes

---

## Step 3 — Insert incoming messages on server

```bash
scp -i "../16_chatwoot_services.pem" missing_incoming.json ubuntu@10.10.3.112:/tmp/
scp -i "../16_chatwoot_services.pem" insert_incoming_messages.rb ubuntu@10.10.3.112:/tmp/

ssh -i "../16_chatwoot_services.pem" ubuntu@10.10.3.112 \
  "sudo docker exec chatwoot-web-production sh -c \
  'cd /app && RAILS_ENV=production bundle exec rails runner /tmp/insert_incoming_messages.rb' 2>&1"
```

Expected output:
```
DONE
  Conversations processed : XXXX
  Messages inserted       : XXXX
  Errors                  : 0
```

---

## Step 4 — Fix outgoing message timestamps

### Step 4a — Fetch timestamps from cloud

```bash
python3 fetch_outgoing_timestamps.py
# Output: outgoing_timestamp_updates.json
# Resume-capable via fetch_outgoing_ckpt_prod.json
# Estimated time: ~1.5-2 hours
```

### Step 4b — Apply to server

```bash
scp -i "../16_chatwoot_services.pem" outgoing_timestamp_updates.json ubuntu@10.10.3.112:/tmp/
scp -i "../16_chatwoot_services.pem" apply_outgoing_timestamps.rb ubuntu@10.10.3.112:/tmp/

ssh -i "../16_chatwoot_services.pem" ubuntu@10.10.3.112 \
  "sudo docker exec chatwoot-web-production sh -c \
  'cd /app && RAILS_ENV=production bundle exec rails runner /tmp/apply_outgoing_timestamps.rb' 2>&1"
```

Expected output:
```
DONE
  Updated : XXXX
  Skipped : 0
  Errors  : 0
```

---

## Step 5 — Validate

```bash
scp -i "../16_chatwoot_services.pem" validate_messages.rb ubuntu@10.10.3.112:/tmp/

ssh -i "../16_chatwoot_services.pem" ubuntu@10.10.3.112 \
  "sudo docker exec chatwoot-web-production sh -c \
  'cd /app && RAILS_ENV=production bundle exec rails runner /tmp/validate_messages.rb' 2>&1"
```

Expected output:
```
RESULTS
  OK (all messages visible) : XXXX
  Conversations with hidden : 0
  Empty conversations       : 0
```

If hidden messages > 0 → investigate before proceeding.

---

## Step 6 — Final delta before cutover (16 March evening)

Conversations received since Step 1 started need to be imported again.
Re-run Steps 1–5 — scripts skip already-migrated, only import new conversations.

Estimated time: ~20–30 minutes (new conversations only).

---

## Step 7 — Router cutover (16 March evening — coordinate with Alex)

Run immediately after Step 6 completes and validation passes.
Alex updates router at 10.10.3.7 — switch target from:
```
app.chatwoot.com → chat.pbmcgroup.com
```

**Target: 17 March 2026 — chat.pbmcgroup.com live for all users.**

---

## Go-Live Checklist

- [ ] `migrate_full.py` complete — all conversations imported
- [ ] `export_incoming.py` complete
- [ ] `insert_incoming_messages.rb` on server — 0 errors
- [ ] `fetch_outgoing_timestamps.py` complete
- [ ] `apply_outgoing_timestamps.rb` on server — 0 errors
- [ ] `validate_messages.rb` — 0 hidden messages
- [ ] Sample check: open 5 conversations, message order correct
- [ ] Final delta (Step 6) complete — 16 March evening
- [ ] Router cutover to chat.pbmcgroup.com — 16 March evening (Alex)
- [ ] Notify CS team — active on chat.pbmcgroup.com from 17 March

---

## Important Notes

**Do not run from the `migration/` folder** — that folder is for staging.
Always run from `migration_production/`.

**State file**: `state_production.json` is the cloud_id → production_id map.
Do not delete while migration is in progress.

**Docker exec command for production**:
```bash
sudo docker exec chatwoot-web-production sh -c \
  'cd /app && RAILS_ENV=production bundle exec rails runner /tmp/SCRIPT.rb'
```

**Redis**: staging uses DB 1, production uses DB 0 — already separated, no cross-interference.
