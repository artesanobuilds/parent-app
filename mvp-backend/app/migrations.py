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
            # Existing DB already at the latest pre-framework schema — stamp it.
            top = max(v for v, _, _ in MIGRATIONS)
            for v, desc, _ in MIGRATIONS:
                con.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    [v, desc],
                )
            applied = {v for v, _, _ in MIGRATIONS}
            logger.info(f"[migrations] stamped pre-framework DB at v{top}")

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
