"""The whole migration chain, run against a POPULATED database.

`run_migrations` executes on **every prod boot**. There are 22 migrations and,
before this file, only one of them (v19, after it caused the 2026-07-11 outage)
had a test that ran it against a DB with real rows in it. Empty dev/test DBs are
exactly the shape that does NOT reproduce the failures that matter:

  * `CREATE INDEX` cannot share a transaction with an `UPDATE` — DuckDB refuses
    with "Cannot create index with outstanding updates" only when rows exist
    (the v16 outage).
  * A `DROP TABLE` is irreversible, and v21 drops FIVE of them. If a base-schema
    `CREATE TABLE IF NOT EXISTS` still names a dropped table, bootstrap
    resurrects it empty on the next boot and the migration silently un-applies.
  * A backfill that assumes a column is non-null crashes only on legacy rows.

So these tests seed data FIRST, rewind `schema_migrations`, and re-run the chain,
asserting both that it completes and that the data survived.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "chain.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app.duckdb_storage import DuckDBStorage  # noqa: E402
from app.migrations import MIGRATIONS, run_migrations  # noqa: E402

# The five tables migration v21 dropped with the public board + 1:1 DMs.
DROPPED_IN_V21 = (
    "dm_reactions", "dm_messages", "dm_conversations",
    "post_replies", "community_posts",
)


def _fresh() -> DuckDBStorage:
    return DuckDBStorage(db_path=str(Path(tempfile.mkdtemp()) / "chain.duckdb"))


def _live_tables(con) -> set[str]:
    return {
        r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
    }


def _applied(con) -> set[int]:
    return {
        r[0] for r in con.execute("SELECT version FROM schema_migrations").fetchall()
    }


def test_every_migration_has_a_unique_ascending_version():
    """A duplicate or out-of-order version silently skips a migration: the
    runner filters on `version not in applied`, so two entries sharing a number
    mean the second never runs on a DB that saw the first."""
    versions = [v for v, _name, _body in MIGRATIONS]
    assert versions == sorted(versions), f"MIGRATIONS is not in ascending order: {versions}"
    assert len(versions) == len(set(versions)), (
        f"duplicate migration versions: "
        f"{sorted(v for v in versions if versions.count(v) > 1)}"
    )
    names = [n for _v, n, _b in MIGRATIONS]
    assert len(names) == len(set(names)), "two migrations share a name"


def test_the_full_chain_reruns_on_a_populated_db():
    """Rewind to version 0 with rows present and replay all 22.

    This is the closest thing to "what happens when a long-lived prod volume
    boots a new image". Every migration must be idempotent enough to survive it,
    because the stamp table is the ONLY thing preventing a re-run and a partially
    stamped DB is a real state (a crash mid-chain leaves one).
    """
    store = _fresh()
    con = store._con

    # Seed across the surfaces migrations touch.
    store.track_activity("chain-user", name="Existing Camp", kid_name="Lily",
                         week_start="2026-07-13", status="signed_up")
    store.add_todo("chain-user", title="Register Lily")
    store.save_user_data("chain-user", "chat_threads", {"default": []})

    before_activities = con.execute(
        "SELECT count(*) FROM tracked_activities"
    ).fetchone()[0]
    assert before_activities == 1

    # Rewind the stamp table only — the schema stays current, which is precisely
    # the case a re-run must tolerate (every ALTER meets a column that exists).
    con.execute("DELETE FROM schema_migrations")
    run_migrations(con)

    assert con.execute("SELECT count(*) FROM tracked_activities").fetchone()[0] == 1, (
        "replaying the chain destroyed existing activity rows"
    )
    # The runner's own "pre-migration DB" detection stamps such a DB at the top
    # rather than replaying blindly; either way the end state must be current.
    assert max(_applied(con)) == max(v for v, _n, _b in MIGRATIONS)


def test_v21_drops_stay_dropped_across_a_reboot():
    """The bootstrap/migration ordering trap.

    `DuckDBStorage.__init__` runs the base-schema `CREATE TABLE IF NOT EXISTS`
    block BEFORE `run_migrations`. If any DDL constant still named one of v21's
    five tables, every boot would recreate it empty and v21 — already stamped —
    would never run again to clean up. The table would silently return, and with
    it the dead-code paths that read from it.

    Simulating a reboot by constructing a second storage object over the same
    file is the only way to catch that ordering.
    """
    path = str(Path(tempfile.mkdtemp()) / "reboot.duckdb")
    first = DuckDBStorage(db_path=path)
    live = _live_tables(first._con)
    for table in DROPPED_IN_V21:
        assert table not in live, f"{table} exists on a FRESH db — a DDL constant still creates it"
    first.close()

    second = DuckDBStorage(db_path=path)
    live_again = _live_tables(second._con)
    for table in DROPPED_IN_V21:
        assert table not in live_again, (
            f"{table} came back on reboot — the base schema recreates it, and v21 "
            "is already stamped so it will never be dropped again"
        )
    assert 21 in _applied(second._con)
    second.close()


def test_v21_is_safe_on_a_legacy_db_that_still_has_the_tables():
    """A real prod volume DOES still have these tables and rows.

    Recreate that shape — tables present, stamp rewound below 21 — and assert the
    drop runs cleanly and takes the rows with it, while leaving unrelated user
    data intact.
    """
    store = _fresh()
    con = store._con

    con.execute("""
        CREATE TABLE IF NOT EXISTS community_posts (
            id TEXT PRIMARY KEY, category TEXT, initials TEXT, name TEXT,
            title TEXT, preview TEXT, user_id TEXT,
            created_at TIMESTAMP, updated_at TIMESTAMP
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS post_replies (
            id TEXT PRIMARY KEY, post_id TEXT, user_id TEXT, author_name TEXT,
            initials TEXT, body TEXT, created_at TIMESTAMP
        )
    """)
    con.execute(
        "INSERT INTO community_posts (id, category, title, preview) "
        "VALUES ('legacy-post', 'sleep', 'Old board post', 'preview')"
    )
    con.execute(
        "INSERT INTO post_replies (id, post_id, body) "
        "VALUES ('legacy-reply', 'legacy-post', 'a reply')"
    )
    store.track_activity("legacy-user", name="Survivor Camp", kid_name="Ben")

    con.execute("DELETE FROM schema_migrations WHERE version >= 21")
    run_migrations(con)

    live = _live_tables(con)
    assert "community_posts" not in live and "post_replies" not in live, (
        "v21 did not drop the board tables on a DB that actually had them"
    )
    assert con.execute(
        "SELECT count(*) FROM tracked_activities"
    ).fetchone()[0] == 1, "v21 collateral-damaged unrelated rows"
    assert 21 in _applied(con)

    # Idempotent: running again must not raise on already-absent tables.
    con.execute("DELETE FROM schema_migrations WHERE version >= 21")
    run_migrations(con)


def test_v22_backfills_without_clobbering_existing_rows():
    """v22 adds fit_score/fit_reason to a SHIPPED table.

    An ALTER that assumed the column was absent would crash on a re-run, and one
    that rewrote rows would wipe a parent's real plan. Both directions asserted.
    """
    store = _fresh()
    con = store._con

    activity_id = store.track_activity(
        "v22-user", name="Scored Camp", kid_name="Lily",
        fit_score=0.75, fit_reason="Closest full-day option.",
        decision_rationale="We picked it for the location.",
    )

    con.execute("DELETE FROM schema_migrations WHERE version >= 22")
    run_migrations(con)

    row = store.get_tracked_activity(activity_id)
    assert row["fit_score"] == 0.75, "v22 re-run cleared an existing fit_score"
    assert row["fit_reason"] == "Closest full-day option."
    # The two rationale fields are different authors and must stay independent.
    assert row["decision_rationale"] == "We picked it for the location."


def test_v23_applies_to_a_populated_db_and_is_idempotent():
    """v23 does THREE things in one version: creates circle_requests (+ its two
    indexes) and adds articles.kicker / articles.age_range.

    Both hazards are here. The table already exists on a fresh DB (CIRCLE_DDL
    creates it before migrations run), and the two columns already exist in
    CONTENT_DDL — so an unguarded ALTER would raise "Column already exists" on
    every new install. And the body must stay pure DDL: a CREATE INDEX cannot
    share a transaction with an UPDATE on a table that has rows.
    """
    store = _fresh()
    con = store._con

    # Rows in both tables the migration touches.
    store.create_article({
        "id": "chain-article", "category": "sleep", "title": "Bedtime",
        "subtitle": "", "summary": "", "content": "body", "tags": [],
    })
    store.create_circle_request(
        from_user_id="v23-from", to_user_id="v23-to", from_member_id="v23-member",
    )

    con.execute("DELETE FROM schema_migrations WHERE version >= 23")
    run_migrations(con)

    article_cols = {
        r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'articles'"
        ).fetchall()
    }
    assert {"kicker", "age_range"} <= article_cols
    assert con.execute("SELECT count(*) FROM articles").fetchone()[0] == 1, (
        "v23 collateral-damaged an existing article row"
    )
    assert con.execute("SELECT count(*) FROM circle_requests").fetchone()[0] == 1, (
        "v23 re-ran the CREATE TABLE destructively over existing requests"
    )
    assert 23 in _applied(con)

    # Idempotent: a replay must not raise on the present table or columns.
    con.execute("DELETE FROM schema_migrations WHERE version >= 23")
    run_migrations(con)
    assert con.execute("SELECT count(*) FROM circle_requests").fetchone()[0] == 1


def test_v23_circle_requests_survives_a_reboot():
    """The bootstrap/migration ordering trap in the other direction from v21:
    CIRCLE_DDL and the migration must converge on the SAME shape, so a second
    boot over the same file neither loses the table nor re-raises."""
    path = str(Path(tempfile.mkdtemp()) / "v23-reboot.duckdb")
    first = DuckDBStorage(db_path=path)
    request_id = first.create_circle_request(
        from_user_id="reboot-from", to_user_id="reboot-to",
    )
    assert 23 in _applied(first._con)
    first.close()

    second = DuckDBStorage(db_path=path)
    assert "circle_requests" in _live_tables(second._con)
    row = second.get_circle_request(request_id)
    assert row is not None and row["status"] == "pending"
    assert row["from_user_id"] == "reboot-from" and row["to_user_id"] == "reboot-to"
    second.close()


def test_a_partially_stamped_db_completes(monkeypatch):
    """A crash mid-chain leaves some versions stamped and some not.

    Rewinding to an arbitrary midpoint must still converge — this is the state a
    failed deploy actually leaves behind, and the runner has to be re-entrant
    from it rather than from version 0 only.
    """
    store = _fresh()
    con = store._con
    store.track_activity("partial-user", name="Half Camp", kid_name="Ben",
                         week_start="2026-07-13")

    midpoint = MIGRATIONS[len(MIGRATIONS) // 2][0]
    con.execute("DELETE FROM schema_migrations WHERE version >= ?", [midpoint])
    assert max(_applied(con)) < midpoint

    run_migrations(con)

    assert max(_applied(con)) == max(v for v, _n, _b in MIGRATIONS)
    assert con.execute("SELECT count(*) FROM tracked_activities").fetchone()[0] == 1
