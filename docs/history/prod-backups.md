# Production backups

Append-only. One entry per snapshot, newest at the BOTTOM (chronological, so a
`git log` on this file reads as the deploy history). Written by
`mvp-backend/tools/backup-prod.sh` — do not hand-edit past entries.

The parquet files themselves live outside the repo (`~/Desktop/mvp-prod-snapshot-<date>/`)
because they are real families' data and must never be committed. What lives
here is the RECORD: when, what, how many bytes, and the md5 — enough to prove a
later copy is byte-identical, and enough to know what was never captured.

## How to take one

```bash
cd mvp-backend
export MVP_ADMIN_TOKEN=<the server's ADMIN_TOKEN, from mvp-backend/.env>
BACKUP_REASON="pre-deploy: migration v24" ./tools/backup-prod.sh
```

Default scope is narrow on purpose — only tables whose **schema** the pending
migration alters or drops. Read that strictly: "a table the new code writes to at
runtime" is NOT at risk, and treating it as such is how a backup scope quietly
grows to include every family's PII. The first draft of `backup-prod.sh` listed
`household_members` on exactly that basis and was blocked — correctly, since
migration v23 doesn't touch its schema.

PII-bearing tables (`household_members`, `auth_identities`, `kid_credentials`,
`consent_records`, `circle_messages`, …) require a reason **this deploy**, named
explicitly on the command line. `--all` is for a volume-rebuild drill only.

**Never use `GET /data/export`.** It is the bulk-PII route CLAUDE.md forbids, and
on 2026-08-08 the operator's own runbook wrongly told them to call it (the
permission layer blocked it). The script uses `GET /cms/stats` for counts and
`GET /data/download/{table}.parquet` per file.

## How to read one back

The files are plain parquet — no server needed:

```bash
python3 -c "import duckdb; print(duckdb.sql(\"SELECT * FROM 'dm_messages.parquet' LIMIT 5\"))"
```

To restore, write the rows back through the ordinary API (or `INSERT` into the
live DuckDB from the parquet). Do NOT drop a restored parquet into `mvp-backend/data/`
and redeploy — `railway up` uploads the working tree and would bake user state
into the image. `.dockerignore` blocks it, and `tests/test_dockerignore_guard.py`
locks that.

---

## 2026-08-08T09:52:00Z

- **Reason:** pre-deploy snapshot — sprint-2 migration **v21** DROPped the public
  board and 1:1 DMs. Taken by hand, before `backup-prod.sh` existed; this entry is
  a retroactive record so the snapshot is tracked like every later one.
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `~/Desktop/mvp-prod-snapshot-2026-08-08/`
- **Captured:** `community_posts.parquet` `dm_conversations.parquet`
  `dm_messages.parquet` `dm_reactions.parquet` `post_replies.parquet`
- **Contents that mattered:** **73 real DM messages across 4 conversations**
  (Miguel ↔ a beta parent, 65 msgs Jul 19–23, plus Heather and Lindsey). Board
  posts were all seeded — 0 had a `user_id`. Verified byte-identical (md5) to the
  frozen leftover still on the prod volume.
- **Still owed:** Heather and Lindsey were never told their threads are gone.
  Nothing was deleted from this snapshot; re-adding each other restores nothing
  automatically, so the messages only exist here.
- **md5:**
    - (not recorded at the time — regenerate with `md5 -r ~/Desktop/mvp-prod-snapshot-2026-08-08/*.parquet`
      if a comparison is ever needed; the files are unmodified since capture)

## 2026-08-08T16:35:31Z

- **Reason:** pre-deploy: sprint-1/2 completion, migration v23 (ALTERs articles: +kicker +age_range; adds empty circle_requests)
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `/Users/miguelalvarado/Desktop/mvp-prod-snapshot-2026-08-08`
- **Captured:** `articles.parquet` `categories.parquet`
- **Pre-deploy counts:** 45 articles / 110 categories (`pre-deploy-cms-stats.json`)
- **Scope note:** deliberately content-only. v23 ALTERs `articles`; `circle_requests`
  is new and therefore empty; **no PII table was pulled**, because none is at
  schema risk in this deploy.
- **md5:**
    - `1119755f93689fdba974b46f4f40e88c articles.parquet`
    - `99e73584ea36c5ecbba6ea4264fb8da3 categories.parquet`
    - (the five `dm_*`/board files in the same folder are from the 09:52Z entry
      above, not this run — the script's manifest glob was hashing them too and
      has been fixed to list only what each run captured)


## 2026-08-10T01:38:02Z

- **Reason:** pre-deploy: migration v23 (circle_requests table + article eyebrow columns) + round-2 iOS fidelity pass
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `/Users/miguelalvarado/Desktop/mvp-prod-snapshot-2026-08-10`
- **Captured:** articles.parquet categories.parquet
- **md5:**
    - `8ee35ebdcc23b41758cdc5c3542ee5f1 articles.parquet`
    - `99e73584ea36c5ecbba6ea4264fb8da3 categories.parquet`


## 2026-08-11T00:32:42Z

- **Reason:** pre-deploy: migration v24 UPDATE-backfills tracked_activities.details_json from activity_candidates (v24 is the only schema-adjacent change; user_data also snapshotted because the post-deploy step deletes two orphaned rows from it)
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `/Users/miguelalvarado/Desktop/mvp-prod-snapshot-2026-08-11`
- **Captured:** tracked_activities.parquet activity_candidates.parquet
- **Not on the volume (expected for a new table):** user_data.parquet
- **md5:**
    - `1b07e44db46c63ef80f2124092fdc6ba tracked_activities.parquet`
    - `5cce16087f16b579124fa2386fd541fa activity_candidates.parquet`


## 2026-08-22T05:19:20Z

- **Reason:** pre-deploy: heisman sprint-01 (additive — anon extraction endpoints, seed keys, admin reset; no new migration beyond live v24)
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `/Users/miguelalvarado/Desktop/mvp-prod-snapshot-2026-08-22`
- **Captured:** articles.parquet categories.parquet
- **md5:**
    - `8ee35ebdcc23b41758cdc5c3542ee5f1 articles.parquet`
    - `99e73584ea36c5ecbba6ea4264fb8da3 categories.parquet`


## 2026-10-11T15:44:32Z

- **Reason:** PR #1 deployment, merged revision 68df0ce; documentation and contract tests only, no migrations; narrow content rollback baseline
- **Remote:** `https://mvp-backend-production-8678.up.railway.app`
- **Location:** `/Users/miguelalvarado/Desktop/mvp-prod-snapshot-2026-10-11`
- **Captured:** articles.parquet categories.parquet
- **md5:**
    - `8ee35ebdcc23b41758cdc5c3542ee5f1 articles.parquet`
    - `99e73584ea36c5ecbba6ea4264fb8da3 categories.parquet`

