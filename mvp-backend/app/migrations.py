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
]

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
