"""
Regression guard for the parquet bootstrap when the live table's schema has
drifted past the snapshot parquet's schema.

The bug we're guarding against (May 2026):
  - Migration v4 added `categories.parent_id` to the live table (5 cols).
  - The on-disk `categories.parquet` snapshot still had 4 cols.
  - The bootstrap UPSERT used `INSERT OR IGNORE INTO categories SELECT *
    FROM parquet(?)` — DuckDB raised a `Binder Error` ("table excluded has
    4 columns available but 5 columns specified"), the bootstrap silently
    warned + skipped, and on a fresh deploy (Railway volume blown away, no
    .duckdb file, parquet is source of truth) the categories table would
    have come up empty.

Why this is a unit test, not a flow test:
  - The failure only manifests on a *fresh* DB. A warm DB has the rows
    already (from prior boots) and the live API stays green.
  - The flow harness runs against a warm backend; it can't easily simulate
    "delete the .duckdb file and restart."
  - A tempfile DuckDB + a synthetic narrow parquet hermetically reproduces
    the exact code path that broke.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import duckdb
import pytest

# Make `app.*` importable from the backend root, regardless of pytest cwd.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402


def _write_narrow_categories_parquet(parquet_path: Path) -> None:
    """
    Build a 4-column categories parquet — matching the pre-v4 schema. This
    is what a deployment that pre-dated migration v4 would have shipped.
    """
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE tmp_cats (
            id TEXT, name TEXT, emoji TEXT, description TEXT
        )
    """)
    con.execute("""
        INSERT INTO tmp_cats VALUES
            ('adventures-play', 'Adventures', '*', 'desc'),
            ('emotional-wellness', 'Wellness',  '*', 'desc')
    """)
    con.execute(
        "COPY tmp_cats TO ? (FORMAT PARQUET)", [str(parquet_path)],
    )
    con.close()


def test_fresh_boot_with_narrow_parquet_populates_drifted_table():
    """
    Simulate a fresh deploy where the snapshot parquet pre-dates a column
    addition. The bootstrap must:
      1. Not crash boot
      2. Populate the drifted table with all snapshot rows
      3. Default the new column to NULL (it's nullable)
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "mvp.duckdb"

        # Write the narrow snapshot BEFORE booting the storage; the
        # bootstrap reads from `db_path.parent / "categories.parquet"`.
        _write_narrow_categories_parquet(tmp_path / "categories.parquet")

        # Boot — this runs CREATE-IF-NOT-EXISTS DDL (5-col table) + all
        # migrations + the bootstrap merge. Must not raise.
        storage = DuckDBStorage(db_path=db_path)

        # The 2 narrow-parquet rows landed in the 5-col table.
        rows = storage._con.execute(
            "SELECT id, name, parent_id FROM categories ORDER BY id"
        ).fetchall()

        assert len(rows) == 2, (
            f"expected 2 rows bootstrapped from narrow parquet, got {len(rows)}. "
            "Bootstrap likely silently skipped (the bug we're guarding against)."
        )

        for row in rows:
            assert row[2] is None, (
                f"parent_id should default to NULL for migrated rows; got {row[2]!r}"
            )


def test_fresh_boot_with_no_snapshot_does_not_crash():
    """
    If no parquet snapshot exists at all (true cold start, no prior export),
    bootstrap must skip gracefully and leave tables empty — not crash.
    """
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "mvp.duckdb"
        # Intentionally no parquets in tmp_path
        storage = DuckDBStorage(db_path=db_path)
        n = storage._con.execute(
            "SELECT count(*) FROM categories"
        ).fetchone()[0]
        assert n == 0, "no snapshot → table should be empty (not magically populated)"


def test_fresh_boot_drift_log_note_includes_added_column(caplog):
    """
    The bootstrap log message should include a drift note when the parquet
    is missing a column the live table has. This is documentation, not just
    a behavior guarantee — when this fires in production logs, on-call
    knows which migration is out of sync with the snapshot.
    """
    import logging

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_narrow_categories_parquet(tmp_path / "categories.parquet")
        db_path = tmp_path / "mvp.duckdb"

        with caplog.at_level(logging.INFO, logger="app.duckdb_storage"):
            DuckDBStorage(db_path=db_path)

        cat_logs = [
            r.getMessage() for r in caplog.records
            if "bootstrap-merged categories" in r.getMessage()
        ]
        assert cat_logs, (
            "expected a 'bootstrap-merged categories' log line. Got: "
            + "\n  ".join(r.getMessage() for r in caplog.records[-10:])
        )
        joined = " | ".join(cat_logs)
        assert "drift" in joined, (
            "expected a `drift:` annotation in the log line when the parquet "
            f"is narrower than the table. Got: {joined}"
        )
        assert "parent_id" in joined, (
            "drift note should name the missing column (parent_id). "
            f"Got: {joined}"
        )


def test_fresh_boot_with_wide_parquet_only_inserts_shared_columns():
    """
    Forward-compatibility: if a parquet snapshot has EXTRA columns the live
    table doesn't have (e.g. snapshot taken from a newer deploy, then
    restored on an older deploy), the bootstrap must insert only the
    intersection — not crash on the unknown columns.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        # Build a parquet with an EXTRA col the table doesn't have
        con = duckdb.connect()
        con.execute("""
            CREATE TABLE tmp_cats (
                id TEXT, name TEXT, emoji TEXT, description TEXT,
                parent_id TEXT, future_only_col TEXT
            )
        """)
        con.execute("""
            INSERT INTO tmp_cats VALUES
                ('cat-a', 'A', '*', 'd', NULL, 'futurevalue')
        """)
        con.execute(
            "COPY tmp_cats TO ? (FORMAT PARQUET)",
            [str(tmp_path / "categories.parquet")],
        )
        con.close()

        db_path = tmp_path / "mvp.duckdb"
        storage = DuckDBStorage(db_path=db_path)

        n = storage._con.execute("SELECT count(*) FROM categories").fetchone()[0]
        assert n == 1, "wide parquet row should have bootstrapped"
