# lifehacks — personal cron jobs on the homelab box

## 1. What runs here

| Unit | When | What |
|---|---|---|
| `homelab-db` (docker, `restart: unless-stopped`) | always | TimescaleDB/PG18 on `127.0.0.1:5432`; one database per domain |
| `homelab-db-backup.timer` | daily 03:30 | `pg_dumpall` → `~/.local/share/homelab/backups/`, keeps 14 |
| `todo-pulse-collect.timer` | daily 06:00 | snapshot every `~/Projects/**/plans/TO-DO.md` |
| `todo-pulse-report.timer` | Mon 07:00 | weekly email via SES → alex@kalpahealth.com |

All timers use `Persistent=true`, so a run missed while the box was off fires at next boot.

```
 ~/Projects/*/plans/TO-DO.md          homelab-db (todo_pulse)
   (read from git origin/HEAD)  --->   snapshot  1 row / source / day
            collect.py                 item      1 row / item, first_seen..gone_on
                                              |
                                              v
                                  report.py --send  ---> SES (grafana-remediate sender)
```

## 2. Setup

2.1 **Secrets.** 1Password is the source of truth; local `600` files are caches, so
timers never depend on 1Password being reachable. The box's Service Account is
read-only by design — a human creates/rotates items, the box only reads.

| Secret | 1Password | Local cache | Written by |
|---|---|---|---|
| DB password | `op://Automation/homelab-db/password` | `homelab-db/.env`, `~/.pgpass` | `~/cc/homelab-db-up.sh` |
| AWS keys | `op://Automation/AWS {default,kalpa,padma}` | `~/.aws/credentials`, `~/.aws/config` | `~/cc/aws-hydrate.sh` |

2.2 **Bring-up** (idempotent; re-run after rotating the DB password in 1Password):
`bash ~/cc/homelab-db-up.sh`

2.3 **Email** uses the `kalpa` profile: Grafana's SES identity (kalpahealth.com,
production access) is in that account, `ap-southeast-1`. No separate SES-only key —
it would sit beside the full keys in the same file and protect nothing.

2.4 **docker group.** Only the backup touches docker. The systemd user manager and the
herdr server keep the groups they started with, so after adding `alexk` to `docker`
the box needs one reboot before the backup timer can reach the socket.

## 3. todo-pulse

3.1 **History comes from git.** `collect.py --backfill` replays the latest commit per day
of each TO-DO.md, so the trend starts at the file's first commit. `--rebuild` wipes a
source and replays it (needed after changing id or parsing rules).

3.2 **Item identity** = hash(source, normalised first line). Moving an item between
sections keeps its id; editing its first line reads as remove + add.

3.3 **Origin kind** (`review-deferral`, `closeout-residual`, `surfaced`, ...) is a regex
over the section heading — a trend signal, not a taxonomy. Value categories (real vs
slop) and approval for overnight agents are the next layer, not built yet.

3.4 Parsing is imported from `~/Projects/ai-skills/scripts/todo-stats.py`, the same parser
the session-start counter uses.

## 4. Databases

- `todo_pulse` — this.
- `home` — IoT (water, power, leak). Timescale extension already enabled; schema not yet built.

The WellMed test env does **not** belong here: it lives in the WellMed repos, on another port, disposable.
