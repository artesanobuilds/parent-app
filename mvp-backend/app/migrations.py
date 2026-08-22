"""
Versioned schema migrations for the DuckDB backend.

Replaces the old inline `try: ALTER ...; except: pass` pattern, which silently
swallowed every error (disk-full, syntax, type mismatch) and left no record of
what ran. Here, a `schema_migrations` table tracks applied versions, migrations
run in order at startup, and any failure raises — a container that won't start
is better than one serving on a half-migrated schema.

Rules:
- NEVER edit or reorder an existing entry. Only append new ones.
- A migration is (version:int, description:str, body: str | callable | None).
  - str  -> executed as a single SQL statement.
  - callable(con) -> run arbitrary multi-step logic (con is the storage conn).
  - None -> a marker only (e.g. the baseline); records the version, runs nothing.
- No down-migrations. Recovery posture for the closed beta is "snapshot + roll
  forward" (a reversal is just a new forward migration).
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Callable, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

MigrationBody = Union[str, Callable[[object], None], None]

# (version, description, body)
MIGRATIONS: List[Tuple[int, str, MigrationBody]] = [
    (1, "baseline_schema", None),  # CREATE-IF-NOT-EXISTS schema is applied separately
    (2, "auth_tokens.add_expires_at",
     "ALTER TABLE auth_tokens ADD COLUMN expires_at TIMESTAMPTZ"),
    (3, "auth_tokens.add_last_used_at",
     "ALTER TABLE auth_tokens ADD COLUMN last_used_at TIMESTAMPTZ"),
    # Phase 0 taxonomy redesign: categories gain a soft self-reference for
    # 2-level hierarchy. parent_id is nullable; top-level rows have NULL.
    # DuckDB doesn't enforce FKs, so this is a soft reference to categories.id,
    # following the same convention as articles.category today.
    #
    # Callable instead of a bare ALTER because CONTENT_DDL was also updated to
    # include parent_id (so fresh DBs get it via CREATE-IF-NOT-EXISTS) — the
    # framework runs migrations after the DDL, and DuckDB would otherwise
    # raise "Column with name parent_id already exists". The column-presence
    # check makes the migration idempotent against both fresh and legacy DBs.
    (4, "categories.add_parent_id",
     lambda con: (
         None if "parent_id" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'categories'"
             ).fetchall()
         }
         else con.execute("ALTER TABLE categories ADD COLUMN parent_id TEXT")
     )),
    # Voice fragments persisted alongside the assistant message. The /voice/
    # synthesize/{reply_id}/{fragment_id} endpoint reads from this column;
    # generate_kid_stream populates it during streaming on sentence boundaries.
    (5, "kid_messages.add_fragments_json",
     lambda con: (
         None if "fragments_json" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'kid_messages'"
             ).fetchall()
         }
         else con.execute("ALTER TABLE kid_messages ADD COLUMN fragments_json JSON")
     )),
    # R3: Gmail message id on ingest_artifacts so the daily email-sync agent is
    # idempotent (skip already-ingested messages). New tables (email_sync_runs,
    # agent_config) come via CREATE-IF-NOT-EXISTS; only this column-add on an
    # existing table needs a migration. Column-presence guard = idempotent.
    (6, "ingest_artifacts.add_external_id",
     lambda con: (
         (None if "external_id" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'ingest_artifacts'"
             ).fetchall()
         } else con.execute("ALTER TABLE ingest_artifacts ADD COLUMN external_id TEXT")),
         # Index lives here (not the DDL) so it's created only after the column
         # exists — on fresh DBs the CREATE TABLE already added the column.
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_ingest_artifacts_ext "
             "ON ingest_artifacts (user_id, external_id)"
         ),
     )),
    # R4 part 2: two-way Google Calendar sync. calendar_entries gains the
    # provider event id (the mapping back to the Google event) + synced_at (last
    # reconcile, drives the dirty-check). New tables (calendar_sync_runs) come via
    # CREATE-IF-NOT-EXISTS; only these column-adds on an existing table need a
    # migration. Column-presence guards = idempotent against fresh + legacy DBs.
    # The (user_id, provider_event_id) index lives here, after the columns exist
    # (the DDL runs before migrations, so an index on a migration-added column
    # must be created in the migration — see debugging-duckdb-ddl-gotchas).
    (7, "calendar_entries.add_sync_columns",
     lambda con: (
         (None if "provider_event_id" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'calendar_entries'"
             ).fetchall()
         } else con.execute("ALTER TABLE calendar_entries ADD COLUMN provider_event_id TEXT")),
         (None if "synced_at" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'calendar_entries'"
             ).fetchall()
         } else con.execute("ALTER TABLE calendar_entries ADD COLUMN synced_at TIMESTAMPTZ")),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_calendar_entries_provider "
             "ON calendar_entries (user_id, provider_event_id)"
         ),
     )),
    # Discovery geo-grounding: activity_candidates gains a structured city + region
    # so results are filterable by town (the free-text location_text was unreliable).
    # New columns come via CREATE-IF-NOT-EXISTS on fresh DBs; existing DBs need this
    # guarded column-add. Column-presence guards = idempotent against fresh + legacy.
    (8, "activity_candidates.add_city_region",
     lambda con: (
         (None if "city" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'activity_candidates'"
             ).fetchall()
         } else con.execute("ALTER TABLE activity_candidates ADD COLUMN city TEXT")),
         (None if "region" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'activity_candidates'"
             ).fetchall()
         } else con.execute("ALTER TABLE activity_candidates ADD COLUMN region TEXT")),
     )),
    # Nearest sort: activity_candidates gains straight-line distance (miles) from
    # the parent's ZIP, computed at insert from the candidate's city. Guarded
    # column-add, idempotent against fresh (CREATE-IF-NOT-EXISTS) + legacy DBs.
    (9, "activity_candidates.add_distance_mi",
     lambda con: (
         None if "distance_mi" in {
             r[0] for r in con.execute(
                 "SELECT column_name FROM information_schema.columns "
                 "WHERE table_name = 'activity_candidates'"
             ).fetchall()
         } else con.execute("ALTER TABLE activity_candidates ADD COLUMN distance_mi DOUBLE")
     )),
    # Crisis-lock push notifications: APNs device tokens per parent. New table
    # comes via CREATE-IF-NOT-EXISTS on fresh DBs; legacy DBs need this create.
    (10, "push_device_tokens.create",
     lambda con: (
         con.execute(
             "CREATE TABLE IF NOT EXISTS push_device_tokens ("
             "token TEXT PRIMARY KEY, user_id TEXT NOT NULL, platform TEXT, "
             "created_at TIMESTAMPTZ DEFAULT now(), last_seen_at TIMESTAMPTZ DEFAULT now())"
         ),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_push_device_tokens_user "
             "ON push_device_tokens (user_id)"
         ),
     )),
    # Phase 3b: scoped read-only share links. New table via CREATE-IF-NOT-EXISTS
    # on fresh DBs; legacy DBs need this create.
    (11, "share_tokens.create",
     lambda con: (
         con.execute(
             "CREATE TABLE IF NOT EXISTS share_tokens ("
             "token TEXT PRIMARY KEY, user_id TEXT NOT NULL, scope TEXT NOT NULL, "
             "label TEXT, created_at TIMESTAMPTZ DEFAULT now(), "
             "expires_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ)"
         ),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_share_tokens_user ON share_tokens (user_id)"
         ),
     )),
    # ── Auth v1 (Phase 2). New tables via CREATE-IF-NOT-EXISTS on fresh DBs
    # (KID_DDL); these mirror them for legacy DBs. See the DDL for column docs.
    (12, "user_accounts.create",
     lambda con: con.execute(
         "CREATE TABLE IF NOT EXISTS user_accounts ("
         "user_id TEXT PRIMARY KEY, analytics_id TEXT UNIQUE, display_name TEXT, "
         "primary_email TEXT, created_at TIMESTAMPTZ DEFAULT now())"
     )),
    (13, "auth_identities.create",
     lambda con: (
         con.execute(
             "CREATE TABLE IF NOT EXISTS auth_identities ("
             "id TEXT PRIMARY KEY, user_id TEXT NOT NULL, provider TEXT NOT NULL, "
             "provider_sub TEXT NOT NULL, email TEXT, email_verified BOOLEAN DEFAULT false, "
             "created_at TIMESTAMPTZ DEFAULT now(), last_login_at TIMESTAMPTZ, "
             "UNIQUE (provider, provider_sub))"
         ),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_auth_identities_user ON auth_identities (user_id)"
         ),
     )),
    (14, "refresh_tokens.create",
     lambda con: (
         con.execute(
             "CREATE TABLE IF NOT EXISTS refresh_tokens ("
             "id TEXT PRIMARY KEY, family_id TEXT NOT NULL, user_id TEXT NOT NULL, "
             "token_hash TEXT UNIQUE NOT NULL, platform TEXT, device_name TEXT, "
             "created_at TIMESTAMPTZ DEFAULT now(), last_used_at TIMESTAMPTZ, "
             "expires_at TIMESTAMPTZ, rotated_at TIMESTAMPTZ, replaced_by TEXT, "
             "revoked_at TIMESTAMPTZ)"
         ),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id)"
         ),
         con.execute(
             "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens (family_id)"
         ),
     )),
    # Backfill a user_accounts row (with a fresh analytics_id) for every distinct
    # existing user across the profile + auth tables. Idempotent: INSERT OR IGNORE
    # keyed on user_id PK, so re-running only fills gaps.
    (15, "user_accounts.backfill_existing",
     lambda con: _backfill_user_accounts(con)),
    # Vertical expansion Phase 0: every tracked activity gets a canonical
    # activity_type (camp|extracurricular|outing|school_event|trip). Backfill
    # is ALL existing rows -> 'camp' — behaviorally true (camp behavior is the
    # only behavior these rows ever had); rows retype organically on next edit.
    # Idempotent (WHERE activity_type IS NULL) so it self-heals across the
    # rollback window. Index lives HERE, not in ACTIVITY_DDL — the DDL runs
    # before migrations on legacy DBs, where the column doesn't exist yet.
    (16, "tracked_activities.add_activity_type",
     lambda con: _add_tracked_activity_type(con)),
    # Vertical expansion Phase 2: the generalized date model, scoped to the two
    # live shapes — week_block (start/end dates; week_start stays the derived
    # anchor) and recurring_weekly (an RFC-5545 RRULE string is the SINGLE
    # SOURCE OF TRUTH; derived recurring_appointments rows get an activity_id
    # back-reference and are regenerated on change, never hand-edited).
    # Backfill start_date = week_start, end_date = week_start + 4 days —
    # end_date is FABRICATED (Mon–Fri assumption), not observed: Saturday
    # sessions and two-week camps exist, so treat backfilled end_dates as
    # display hints only. Idempotent (WHERE start_date IS NULL).
    (17, "tracked_activities.date_model",
     lambda con: _add_tracked_activity_dates(con)),
    # Vertical expansion Phase 4: registration-window watchlist. Both tables
    # are NEW (CREATE IF NOT EXISTS in ACTIVITY_DDL covers fresh and legacy
    # DBs alike), so this is a marker: it records WHEN the watchlist schema
    # arrived, and pins the tables' registration in BOOTSTRAP_TABLES + the
    # .dockerignore exclusions (a volume rebuild must never silently delete
    # the watchlist — it IS the product promise).
    (18, "watchlist.registration_windows", None),
    # The v16 index, in its OWN transaction: DuckDB can't CREATE INDEX on a
    # table updated earlier in the same transaction, and v16's backfill UPDATE
    # is exactly that on any DB with rows (crashed the 2026-07-11 prod deploy;
    # rolled back cleanly). By v19 the v16 transaction has committed, so the
    # index builds. Idempotent for DBs (local dev) that got the index back
    # when v16 still carried it.
    (19, "tracked_activities.type_index",
     lambda con: con.execute(
         "CREATE INDEX IF NOT EXISTS idx_tracked_activities_user_type "
         "ON tracked_activities (user_id, activity_type)"
     )),
    # beta-v1 Phase 1: household members / Circle. The table is NEW, so
    # HOUSEHOLD_DDL's CREATE IF NOT EXISTS (indexes included) covers fresh and
    # legacy DBs alike and there is nothing to ALTER. Marker only — it records
    # when the Circle schema arrived and pins its registration in
    # BOOTSTRAP_TABLES + the .dockerignore exclusion. household_members is the
    # DM authorization source, so losing it is a privacy event, not just data
    # loss.
    (20, "household.members_circle", None),
    # beta-v1 sprint 2: DROP the two retired surfaces' tables.
    #
    #   • the public community board  -> community_posts, post_replies
    #   • parent-to-parent 1:1 DMs    -> dm_conversations, dm_messages,
    #                                    dm_reactions
    #

    # Both surfaces are gone from every client (iOS deleted its views, the CMS
    # its editor) and their routes were withdrawn first. A DROP has to be
    # VERSIONED — a new table converges via CREATE-IF-NOT-EXISTS, but a removal
    # only happens if something runs it exactly once. The matching DDL was
    # deleted from duckdb_storage.py in the same commit, so nothing recreates
    # them on the next boot.
    #
    # RECOVERABILITY: export_parquet snapshots every BOOTSTRAP_TABLES entry to
    # data/<table>.parquet, and prod snapshots before any volume rebuild — so
    # data/community_posts.parquet, data/post_replies.parquet and
    # data/dm_*.parquet hold the last state of these five tables. Those files
    # are deliberately NOT deleted: they are the only way back. (Local dev at
    # drop time: community_posts 34 rows, post_replies 6, all dm_* empty.)
    #
    # saved_items rows with item_type='community_post' are deliberately UNTOUCHED
    # — real users' saves. iOS skips them on render, the server no longer
    # resolves them, and nothing here deletes them.
    #
    # Order is FK-safe (children before parents), and this migration is DROPs
    # and nothing else: run_migrations wraps each body in one transaction, and
    # DuckDB cannot CREATE INDEX on a table with outstanding same-transaction
    # updates (that combination took prod down on 2026-07-11). Keep it pure.
    (21, "retire_community_board_and_dms",
     lambda con: _drop_retired_surface_tables(con)),
    # beta-v1 sprint 2 planner redesign: match quality and reason.
    # tracked_activities gains fit_score and fit_reason (copied forward from
    # activity_candidates at track time). fit_score was the research LLM's 0..1
    # estimate (it existed on candidates but was dropped on track, so Planned
    # items have no score to render). fit_reason is the new "Why it matched"
    # sentence. Idempotent on re-run, no backfill — these two fields apply only
    # to new research runs after this schema lands. Separate transactions (INDEX
    # must not share a txn with an UPDATE).
    (22, "tracked_activities.add_fit_fields",
     lambda con: _add_tracked_activity_fit_fields(con)),
    # beta-v1 sprint 2 Phase B, three things in ONE version:
    #
    #   1. circle_requests — "type an email, and if that person already exists
    #      in the system, pull them from the system." The match creates a
    #      PENDING request; only the recipient's accept binds the mutual
    #      household_members link. The table is NEW, so CIRCLE_DDL's
    #      CREATE-IF-NOT-EXISTS (indexes included) already covers fresh DBs;
    #      this mirrors it for existing volumes.
    #   2/3. articles.kicker + articles.age_range — the article eyebrow
    #      ("WE TRIED IT · Ages 3–7 · 4 min"), consumed by Phase E. Both are
    #      also in CONTENT_DDL so a fresh install gets them from the DDL; the
    #      guarded ALTERs converge an existing DB on the same shape.
    #
    # Pure DDL, no UPDATE anywhere: a CREATE INDEX must never share a
    # transaction with an UPDATE (memory debugging_duckdb_ddl_gotchas — that
    # combination took prod down on 2026-07-11). Column-presence guards make
    # the whole body idempotent across a replay.
    (23, "circle_requests.create_and_article_eyebrow",
     lambda con: _add_circle_requests_and_article_eyebrow(con)),
    # Round 4: `track_activity` now copies a candidate's descriptive fields
    # (ages / schedule / price text / location / city / category) into
    # details_json at save time, so a saved activity's detail screen keeps the
    # information the search result showed. Rows saved BEFORE that change have
    # a candidate_id but an empty details_json, and would stay thin forever —
    # their candidate rows are still in activity_candidates, so backfill them.
    #
    # Pure UPDATE, no DDL in this body (a CREATE INDEX must never share a
    # transaction with an UPDATE — memory debugging_duckdb_ddl_gotchas).
    # Idempotent: only touches rows whose details_json has none of these keys.
    (24, "tracked_activities.backfill_candidate_details",
     lambda con: _backfill_tracked_activity_details(con)),
]


def _backfill_tracked_activity_details(con) -> None:
    """Migration v24: copy candidate detail fields onto already-saved rows.

    Only fills rows that (a) came from a candidate and (b) don't already carry
    the fields — an explicit later edit is never clobbered. `json_merge_patch`
    keeps any unrelated keys the details blob already holds.
    """
    con.execute(
        """
        UPDATE tracked_activities AS t
        SET details_json = json_merge_patch(
                COALESCE(t.details_json, '{}'),
                (SELECT json_object(
                            'age_min', c.age_min,
                            'age_max', c.age_max,
                            'schedule_text', c.schedule_text,
                            'price_text', c.price_text,
                            'location_text', c.location_text,
                            'city', c.city,
                            'category', c.category)
                   FROM activity_candidates c WHERE c.id = t.candidate_id)
            )
        WHERE t.candidate_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM activity_candidates c WHERE c.id = t.candidate_id)
          AND COALESCE(json_extract_string(t.details_json, '$.schedule_text'), '') = ''
          AND COALESCE(json_extract_string(t.details_json, '$.price_text'), '') = ''
          AND COALESCE(json_extract_string(t.details_json, '$.location_text'), '') = ''
        """
    )


def _add_circle_requests_and_article_eyebrow(con) -> None:
    """Migration v23: the Circle request inbox + the article eyebrow columns."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS circle_requests ("
        "id TEXT PRIMARY KEY, from_user_id TEXT NOT NULL, to_user_id TEXT NOT NULL, "
        "from_member_id TEXT, status TEXT NOT NULL DEFAULT 'pending', "
        "created_at TIMESTAMPTZ DEFAULT now(), responded_at TIMESTAMPTZ)"
    )
    # Indexes live HERE, with the CREATE TABLE, so an existing volume gets them
    # in the same committed transaction as the table they index.
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_circle_requests_to "
        "ON circle_requests (to_user_id, status)"
    )
    con.execute(
        "CREATE INDEX IF NOT EXISTS idx_circle_requests_from "
        "ON circle_requests (from_user_id, status)"
    )
    # NOTE: "at most one PENDING row per (from_user_id, to_user_id)" is NOT a
    # DB constraint — DuckDB has no partial unique index, and a full UNIQUE on
    # the pair would wrongly block a re-ask after a decline. It is enforced in
    # app/circle.py (find_pending_circle_request before insert), the same
    # posture as the one-draft-per-slug rule in LEGAL_DDL.
    article_cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'articles'"
        ).fetchall()
    }
    # DuckDB rejects a constraint on ADD COLUMN outright — "Adding columns with
    # constraints not yet supported" — so `NOT NULL DEFAULT ''` is a parser error,
    # not a no-op. It raised on every fresh-DB bootstrap. `DEFAULT ''` alone
    # backfills existing rows with '' and is what the reader needs: the eyebrow
    # joins only non-empty parts, so '' and NULL render the same. The bootstrap
    # DDL still declares NOT NULL, so new installs keep the stricter column.
    if "kicker" not in article_cols:
        con.execute("ALTER TABLE articles ADD COLUMN kicker TEXT DEFAULT ''")
    if "age_range" not in article_cols:
        con.execute("ALTER TABLE articles ADD COLUMN age_range TEXT DEFAULT ''")

# FK-safe order: children (reactions, messages, replies) before their parents.
_RETIRED_TABLES = (
    "dm_reactions",
    "dm_messages",
    "dm_conversations",
    "post_replies",
    "community_posts",
)


def _drop_retired_surface_tables(con) -> None:
    for table in _RETIRED_TABLES:
        # Table names are a fixed literal tuple above, never caller input.
        con.execute(f"DROP TABLE IF EXISTS {table}")


def _add_tracked_activity_fit_fields(con) -> None:
    """Migration v22: tracked_activities gains fit_score + fit_reason."""
    cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tracked_activities'"
        ).fetchall()
    }
    if "fit_score" not in cols:
        con.execute("ALTER TABLE tracked_activities ADD COLUMN fit_score DOUBLE")
    if "fit_reason" not in cols:
        con.execute("ALTER TABLE tracked_activities ADD COLUMN fit_reason TEXT")
    # Also add fit_reason to activity_candidates so research can write it.
    cand_cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'activity_candidates'"
        ).fetchall()
    }
    if "fit_reason" not in cand_cols:
        con.execute("ALTER TABLE activity_candidates ADD COLUMN fit_reason TEXT")


def _backfill_user_accounts(con) -> None:
    import uuid
    # Union every place a user_id has appeared so no existing family is missed.
    rows = con.execute(
        """
        SELECT DISTINCT user_id FROM (
            SELECT user_id FROM user_data
            UNION SELECT user_id FROM auth_tokens
            UNION SELECT user_id FROM consent_records
            UNION SELECT user_id FROM kid_agent_configs
        ) WHERE user_id IS NOT NULL
        """
    ).fetchall()
    for (uid,) in rows:
        con.execute(
            "INSERT OR IGNORE INTO user_accounts (user_id, analytics_id, created_at) "
            "VALUES (?, ?, now())",
            [uid, uuid.uuid4().hex],
        )

def _add_tracked_activity_dates(con) -> None:
    def _cols(table: str) -> set:
        return {
            r[0] for r in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = ?", [table]
            ).fetchall()
        }

    tracked = _cols("tracked_activities")
    for col, ddl_type in (
        ("start_date", "DATE"),
        ("end_date", "DATE"),
        ("rrule", "TEXT"),
        ("recur_time", "TEXT"),
        ("recur_duration_min", "INTEGER"),
    ):
        if col not in tracked:
            con.execute(f"ALTER TABLE tracked_activities ADD COLUMN {col} {ddl_type}")
    con.execute(
        "UPDATE tracked_activities "
        "SET start_date = week_start, end_date = week_start + INTERVAL 4 DAY "
        "WHERE start_date IS NULL AND week_start IS NOT NULL"
    )
    if "activity_id" not in _cols("recurring_appointments"):
        con.execute("ALTER TABLE recurring_appointments ADD COLUMN activity_id TEXT")


def _add_tracked_activity_type(con) -> None:
    cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'tracked_activities'"
        ).fetchall()
    }
    if "activity_type" not in cols:
        con.execute("ALTER TABLE tracked_activities ADD COLUMN activity_type TEXT")
    con.execute(
        "UPDATE tracked_activities SET activity_type = 'camp' "
        "WHERE activity_type IS NULL"
    )
    # NOTE: the (user_id, activity_type) index deliberately does NOT live here.
    # run_migrations wraps each body in ONE transaction, and DuckDB cannot
    # CREATE INDEX on a table with outstanding (same-transaction) updates —
    # the backfill UPDATE above trips "TransactionContext Error: Cannot create
    # index with outstanding updates" on any DB with real rows. (Took prod
    # down on the 2026-07-11 deploy; empty dev/test DBs never hit it.) The
    # index is v19, a separate migration = a separate committed transaction.


_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at  TIMESTAMPTZ DEFAULT now()
);
"""


def current_version(con) -> int:
    rows = con.execute("SELECT max(version) FROM schema_migrations").fetchone()
    return rows[0] if rows and rows[0] is not None else 0


def run_migrations(con) -> None:
    """
    Run all pending migrations in version order. `con` is the storage
    connection (the thread-safe proxy); it exposes execute()/fetchone()/
    fetchall(). Called once from DuckDBStorage.__init__ after the base schema
    has been created, before the app serves traffic.
    """
    con.execute(_MIGRATIONS_DDL)

    applied = {
        r[0] for r in con.execute("SELECT version FROM schema_migrations").fetchall()
    }

    # Pre-migration DBs already have the full current schema (it was built up
    # via CREATE-IF-NOT-EXISTS + the old inline ALTERs). Stamp them at the
    # highest version so historical migrations don't re-run and fail on
    # already-present columns. Detect by: schema_migrations empty AND a known
    # post-migration column already exists.
    if not applied:
        cols = {
            r[0] for r in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'auth_tokens'"
            ).fetchall()
        }
        has_user_data = con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_name = 'user_data'"
        ).fetchone()[0] > 0
        if has_user_data and "expires_at" in cols and "last_used_at" in cols:
            # Existing DB already at the latest pre-framework schema — stamp it
            # only up through v3 (the boundary at which the framework was
            # introduced). Migrations added after v3 must still run on these
            # legacy DBs — they describe net-new schema changes, not the
            # pre-existing baseline. Detecting "is this a pre-framework DB"
            # only proves the v1-v3 columns are present; it says nothing about
            # later migrations, and stamping them as applied would silently
            # skip required work.
            PRE_FRAMEWORK_MAX = 3
            for v, desc, _ in MIGRATIONS:
                if v > PRE_FRAMEWORK_MAX:
                    continue
                con.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    [v, desc],
                )
            applied = {v for v, _, _ in MIGRATIONS if v <= PRE_FRAMEWORK_MAX}
            logger.info(f"[migrations] stamped pre-framework DB at v{PRE_FRAMEWORK_MAX}")

    for version, description, body in sorted(MIGRATIONS, key=lambda m: m[0]):
        if version in applied:
            continue
        # Body + version stamp commit atomically: a crash between them would
        # otherwise re-run the body on next boot, which only stays safe while
        # every migration happens to be idempotent. DuckDB DDL is transactional.
        with _txn(con):
            if isinstance(body, str):
                con.execute(body)
            elif callable(body):
                body(con)
            # body is None -> marker only
            con.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                [version, description],
            )
        logger.info(f"[migrations] applied v{version}: {description}")


@contextmanager
def _txn(con):
    """BEGIN/COMMIT (ROLLBACK on error) that works for both the storage's
    thread-safe proxy (preferred: holds the connection lock across the block)
    and a raw DuckDB connection (tests)."""
    if hasattr(con, "transaction"):
        with con.transaction():
            yield
        return
    con.execute("BEGIN TRANSACTION")
    try:
        yield
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
