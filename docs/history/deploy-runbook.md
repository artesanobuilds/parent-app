# Deploy runbook — closed beta

The order below is not preference. Each step exists because skipping it broke
something on a previous deploy.

**Prod deploys need explicit user authorization each time** (CLAUDE.md). This
runbook describes *how*, never *whether*.

Prod host: `https://mvp-backend-production-8678.up.railway.app`

---

## 0. Know what the deploy changes

Answer these three before touching anything:

| Question | Where to look | Why it matters |
|---|---|---|
| Does a migration **DROP** or **ALTER** anything? | `app/migrations.py` tail | Determines the backup scope in step 1 |
| Does it change a **request/response shape**? | the diff | The shipped iOS build is still calling the OLD shape |
| Does it change an **agent/voice** path? | `agent.py`, `server.py` streaming | Real-time surface; watch `[PERF][VOICE]` after |

A migration that only ADDs is still worth a backup — a bad `ALTER` is as
unrecoverable as a `DROP` if you can't diff against yesterday.

## 1. Back up prod state — BEFORE the deploy

```bash
cd mvp-backend
export MVP_ADMIN_TOKEN=<the server's ADMIN_TOKEN, from mvp-backend/.env>
BACKUP_REASON="pre-deploy: migration v23" ./tools/backup-prod.sh
```

The script forces a fresh parquet export first (otherwise the files are whatever
the last export wrote — and after a DROP they are **frozen leftovers that still
return 200**, verified 2026-08-08), records `/cms/stats` counts as the
post-deploy baseline, downloads **per file**, writes an md5 manifest, and appends
an entry to `docs/history/prod-backups.md`.

**Commit that ledger entry.** The Desktop folder is not a record; the ledger is.

- Default scope is narrow — only what the pending migration can destroy. Widen it
  with explicit table names when the migration touches more.
- **Never `GET /data/export`** — bulk PII, forbidden by CLAUDE.md. On 2026-08-08 the
  then-current runbook wrongly told the operator to call it and the permission
  layer blocked it. That is why this file exists.
- `--all` is for a volume-rebuild drill only. It puts every family's data on a laptop.

## 2. Ship iOS FIRST when the deploy removes anything

The **shipped** app calls the OLD API. If the deploy deletes routes or columns
the current TestFlight build still uses, ordering matters:

1. iOS to TestFlight, and let Miguel install it.
2. *Then* `railway up`.

On 2026-08-08 the shipped 1.75 app called `/dm/*` and `/content/community*`,
which the deploy deleted. It degraded (per-section catch → "Couldn't load…")
rather than crashing, but old-app users saw an empty Circle tab until they
updated. **Degrading gracefully is not the same as being fine.**

If the deploy is purely additive, either order works.

## 3. Green gates before deploying

```bash
cd mvp-backend && source .venv/bin/activate && python -m pytest -q   # 544 passed / 42 skipped
python3 tools/lint-design-tokens.py                                  # ✓ tokens clean
cd mvp-backend/parent-dashboard && npx tsc --noEmit && npm run build
xcodebuild -project mvp/MVP.xcodeproj -scheme MVP -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build      # BUILD SUCCEEDED
```

Also: **rehearse the migration against a prod-SHAPED volume**, not an empty one.
Copy the real content parquets into a scratch dir, stamp `schema_migrations` to
the current prod version, boot through the actual path, and confirm (a) the
migration applies, (b) content row counts survive, (c) a **reboot** doesn't
re-run it or resurrect a dropped table. `tests/test_migration_chain.py` is that
rehearsal in test form — extend it per migration rather than doing it by hand.

## 4. Deploy

```bash
cd mvp-backend && railway up --detach
```

`railway up` uploads the **working tree**. Before running it:

```bash
git status --short | grep -i parquet   # must be EMPTY
```

User-state parquets baked into an image is a known hazard
(`debugging_railway_parquet_deploy_hazard`), locked by
`tests/test_dockerignore_guard.py`. `export_parquet` writes relative to the CWD,
so running it from `mvp-backend/` drops ~44 user-state files one directory ABOVE
the ignored `data/` — that happened on 2026-08-08 and they were staged for commit.

New user-state files (e.g. `agent_checkpoints.sqlite` and its `-wal`/`-shm`) must
be in **both** `.gitignore` and `.dockerignore`.

The web dashboard + CMS build inside the Dockerfile and ship with every backend
deploy. iOS ships via TestFlight only.

## 5. Verify after — against the step-1 baseline

- **Migrations applied**, no traceback: check the Railway boot logs for each new
  version number.
- **Content survived exactly:** `GET /cms/stats` vs `pre-deploy-cms-stats.json`
  from the snapshot. (2026-08-08: 45 articles / 110 categories, matched.)
- **Retired routes 404; new routes live.**
- **One real end-to-end flow on a THROWAWAY user**, deleted afterwards via
  `DELETE /family/{user_id}`. Never delete a real user's data.
- **Read-only NL-harness flows** against prod.
- A single 502 during the container swap is normal and self-resolves.

## 6. Then, and only then

- Dated **release-notes entry** in `parent-dashboard/docs/release-notes.md`, written
  for beta parents: what changed + exactly how to reach it. iOS features are tagged
  *app update X.YY*; web features say *live now*. It rides the same deploy so it
  can never lag.
- Bump build **+1** / marketing **+0.01**.
- Tell affected users anything the deploy took away from them. Still owed from
  2026-08-08: Heather and Lindsey were never told their DM threads are gone.

---

## Rollback

There is no one-command rollback. In descending order of preference:

1. **Forward-fix.** Almost always right for a UI or handler bug.
2. **`railway up` a reverted tree.** The volume is untouched, so this recovers
   code, not data. A migration is **not** undone by this — `schema_migrations`
   still says applied, so an already-dropped table stays dropped.
3. **Restore data from the step-1 snapshot** — read the parquet with DuckDB and
   write rows back through the API. Do NOT drop a restored parquet into
   `mvp-backend/data/` and redeploy (see step 4).

Which is why step 1 is not optional: for anything destructive, the backup is the
only rollback that exists.
