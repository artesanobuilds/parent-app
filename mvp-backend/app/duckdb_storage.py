"""
DuckDB + Parquet storage backend.

Stores user data as JSON blobs in a DuckDB database backed by parquet files.
Also stores content library tables (categories, articles, community_posts).
Drop-in replacement for LocalFileStorage — same StorageBackend interface.
"""

import json
import logging
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import duckdb


class _BufferedResult:
    """Holds eagerly-fetched rows so callers can chain .fetchone()/.fetchall()
    after the connection lock has been released."""

    __slots__ = ("_rows", "_i")

    def __init__(self, rows: List[Any]):
        self._rows = rows
        self._i = 0

    def fetchone(self):
        if self._i < len(self._rows):
            row = self._rows[self._i]
            self._i += 1
            return row
        return None

    def fetchall(self):
        rest = self._rows[self._i:]
        self._i = len(self._rows)
        return rest


class _ThreadSafeConn:
    """
    Serializes access to a DuckDB connection (B-8). DuckDB connections are not
    thread-safe, and FastAPI runs sync routes in a threadpool while async routes
    run on the event loop — concurrent execute()s on one connection can corrupt
    state or interleave writes. Every execute holds an RLock across execute +
    eager fetch, returning a buffered result so the lock is released before the
    caller chains .fetchone()/.fetchall(). The connection is only ever used via
    .execute()/.close() in this module, so this proxy is a complete surface.
    """

    def __init__(self, con: "duckdb.DuckDBPyConnection"):
        self._con = con
        self._lock = threading.RLock()

    def execute(self, sql: str, params: Optional[list] = None) -> _BufferedResult:
        with self._lock:
            rel = self._con.execute(sql, params) if params is not None else self._con.execute(sql)
            try:
                rows = rel.fetchall()
            except Exception:
                # Statements without a result set (some DDL) — nothing to buffer.
                rows = []
            return _BufferedResult(rows)

    @contextmanager
    def transaction(self):
        """
        Hold the connection lock across a BEGIN/COMMIT so a multi-statement
        transaction is both atomic AND isolated — no other thread can execute
        against the shared connection (and thus join the implicit DuckDB
        transaction) while this block runs. RLock is reentrant, so the inner
        execute() calls re-acquire it fine. Rolls back on any exception.
        """
        with self._lock:
            self._con.execute("BEGIN TRANSACTION")
            try:
                yield self
                self._con.execute("COMMIT")
            except Exception:
                self._con.execute("ROLLBACK")
                raise

    def close(self) -> None:
        with self._lock:
            self._con.close()

from app.storage import StorageBackend

logger = logging.getLogger(__name__)


class DuckDBStorage(StorageBackend):
    """
    DuckDB-backed implementation of StorageBackend.

    Tables:
        user_data(user_id, name, data, updated_at)
        categories(id, name, emoji, description)
        articles(id, category, title, subtitle, emoji, author, read_time, summary, tags, content, created_at, updated_at)
        community_posts(id, category, initials, name, title, preview, user_id, created_at, updated_at)
    """

    DDL = """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id  TEXT NOT NULL,
        name     TEXT NOT NULL,
        data     JSON NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (user_id, name)
    );
    """

    CONTENT_DDL = """
    CREATE TABLE IF NOT EXISTS categories (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        emoji       TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS articles (
        id          TEXT PRIMARY KEY,
        category    TEXT NOT NULL,
        title       TEXT NOT NULL,
        subtitle    TEXT NOT NULL DEFAULT '',
        emoji       TEXT NOT NULL DEFAULT '',
        author      TEXT NOT NULL DEFAULT 'MVP Editorial',
        read_time   TEXT NOT NULL DEFAULT '',
        summary     TEXT NOT NULL DEFAULT '',
        tags        TEXT[] NOT NULL DEFAULT [],
        content     TEXT NOT NULL DEFAULT '',
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS community_posts (
        id          TEXT PRIMARY KEY,
        category    TEXT NOT NULL,
        initials    TEXT NOT NULL DEFAULT '',
        name        TEXT NOT NULL DEFAULT '',
        title       TEXT NOT NULL DEFAULT '',
        preview     TEXT NOT NULL DEFAULT '',
        user_id     TEXT,
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS post_replies (
        id          TEXT PRIMARY KEY,
        post_id     TEXT NOT NULL,
        user_id     TEXT NOT NULL,
        author_name TEXT NOT NULL DEFAULT '',
        initials    TEXT NOT NULL DEFAULT '',
        body        TEXT NOT NULL DEFAULT '',
        created_at  TIMESTAMPTZ DEFAULT now()
    );
    """

    # Family Companion (kid agent + handoff). Real tables, not blobs:
    # configs are versioned with content-hash; messages are append-only;
    # credentials and moderation events get their own rows.
    KID_DDL = """
    CREATE TABLE IF NOT EXISTS kid_agent_configs (
        id              TEXT PRIMARY KEY,           -- uuid
        user_id         TEXT NOT NULL,
        kid_name        TEXT NOT NULL,
        version         INTEGER NOT NULL,
        invariants_json JSON NOT NULL,              -- structured: tools, blocklist, goals, voice_template
        free_text_brief TEXT NOT NULL DEFAULT '',
        system_prompt   TEXT NOT NULL,
        content_hash    TEXT NOT NULL,
        model           TEXT NOT NULL,
        enabled         BOOLEAN NOT NULL DEFAULT FALSE,
        created_at      TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_kid_agent_configs_user_kid
        ON kid_agent_configs (user_id, kid_name, version);

    -- One row per (user, kid, version). DB-level guard against the check+insert
    -- TOCTOU race in save_kid_agent_config (B-9): two concurrent writers that
    -- read the same max(version) can't both land the same next version.
    CREATE UNIQUE INDEX IF NOT EXISTS uq_kid_agent_configs_version
        ON kid_agent_configs (user_id, kid_name, version);

    CREATE TABLE IF NOT EXISTS kid_messages (
        id                TEXT PRIMARY KEY,         -- uuid
        agent_id          TEXT NOT NULL,            -- references kid_agent_configs.id
        thread_id         TEXT NOT NULL DEFAULT 'default',
        role              TEXT NOT NULL,            -- 'user' | 'assistant' | 'system'
        content           TEXT NOT NULL,
        moderation_score  DOUBLE,
        age_score         DOUBLE,
        voice_score       DOUBLE,
        parent_flagged    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at        TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_kid_messages_agent_thread
        ON kid_messages (agent_id, thread_id, created_at);

    CREATE TABLE IF NOT EXISTS kid_credentials (
        user_id          TEXT NOT NULL,
        kid_name         TEXT NOT NULL,
        pin_hash         TEXT NOT NULL,             -- bcrypt hash (salt embedded)
        last_rotated_at  TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (user_id, kid_name)
    );

    CREATE TABLE IF NOT EXISTS moderation_events (
        id                  TEXT PRIMARY KEY,       -- uuid
        user_id             TEXT NOT NULL,
        kid_name            TEXT NOT NULL,
        agent_id            TEXT,
        message_id          TEXT,
        severity            TEXT NOT NULL,          -- 'low' | 'medium' | 'high' | 'crisis'
        category            TEXT NOT NULL,          -- e.g., 'self_harm' | 'age_inappropriate' | 'jailbreak' | 'voice_drift'
        action              TEXT NOT NULL,          -- 'allowed' | 'blocked_input' | 'blocked_output' | 'crisis_routed'
        details             JSON,
        parent_notified_at  TIMESTAMPTZ,
        created_at          TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_moderation_events_user_kid
        ON moderation_events (user_id, kid_name, created_at);

    -- Crisis locks: when an input or output trips a crisis pattern, we lock
    -- the agent until a parent explicitly revives it. Replaces the in-process
    -- _killed_agents set, which evaporated on every Railway restart. agent_id
    -- references kid_agent_configs.id, one row per lock cycle.
    CREATE TABLE IF NOT EXISTS kid_agent_crisis_locks (
        agent_id     TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL,
        kid_name     TEXT NOT NULL,
        locked_at    TIMESTAMPTZ DEFAULT now(),
        category     TEXT NOT NULL,
        severity     TEXT NOT NULL,
        reason       TEXT NOT NULL,
        revived_at   TIMESTAMPTZ,
        revived_by   TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_crisis_locks_user_kid
        ON kid_agent_crisis_locks (user_id, kid_name);

    -- PRIMARY KEY column stores sha256(raw_token) hex, NOT the raw token itself.
    -- Clients hold the raw token. Server only sees the hash at rest.
    -- Older plaintext rows are tolerated by the schema, but the runtime lookup
    -- requires expires_at to be set, so legacy rows fail closed and force re-issue.
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token         TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        created_at    TIMESTAMPTZ DEFAULT now(),
        expires_at    TIMESTAMPTZ,
        last_used_at  TIMESTAMPTZ,
        revoked_at    TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens (user_id);

    CREATE TABLE IF NOT EXISTS consent_records (
        id                 TEXT PRIMARY KEY,        -- uuid
        user_id            TEXT NOT NULL,
        parent_name        TEXT,
        parent_email       TEXT,
        kid_age_band       TEXT,
        agreement_version  TEXT NOT NULL,
        accepted_at        TIMESTAMPTZ DEFAULT now(),
        ip_address         TEXT,
        user_agent         TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_consent_user_version
        ON consent_records (user_id, agreement_version, accepted_at);

    CREATE TABLE IF NOT EXISTS daily_summaries (
        id            TEXT PRIMARY KEY,        -- uuid
        user_id       TEXT NOT NULL,
        kid_name      TEXT NOT NULL,
        summary_date  DATE NOT NULL,
        agent_id      TEXT,
        message_count INTEGER NOT NULL,
        headline      TEXT NOT NULL,           -- "Today Nova talked to Julio for 12 minutes about X."
        curiosity     TEXT,                    -- one quoted moment
        frustration   TEXT,                    -- one quoted moment
        prompt_for_parent TEXT,                -- "Ask Julio about the multiplication problem..."
        full_json     JSON,                    -- raw LLM output for audit
        created_at    TIMESTAMPTZ DEFAULT now()
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_summaries_unique
        ON daily_summaries (user_id, kid_name, summary_date);

    -- Append-only audit log for sensitive parent actions: family delete,
    -- export, crisis revive. Survives every other table delete.
    CREATE TABLE IF NOT EXISTS audit_events (
        id          TEXT PRIMARY KEY,
        user_id     TEXT,
        actor       TEXT,
        action      TEXT NOT NULL,
        details     JSON,
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_audit_events_user
        ON audit_events (user_id, created_at);
    """

    # Every table that must survive a volume rebuild, mapped to its parquet
    # snapshot filename. Used for both export (A2/A3) and bootstrap-merge (A2).
    # auth_tokens is safe to export — only sha256 hashes are stored at rest.
    BOOTSTRAP_TABLES = [
        ("user_data", "mvp.parquet"),
        ("categories", "categories.parquet"),
        ("articles", "articles.parquet"),
        ("community_posts", "community_posts.parquet"),
        ("post_replies", "post_replies.parquet"),
        ("kid_agent_configs", "kid_agent_configs.parquet"),
        ("kid_messages", "kid_messages.parquet"),
        ("kid_credentials", "kid_credentials.parquet"),
        ("moderation_events", "moderation_events.parquet"),
        ("kid_agent_crisis_locks", "kid_agent_crisis_locks.parquet"),
        ("consent_records", "consent_records.parquet"),
        ("daily_summaries", "daily_summaries.parquet"),
        ("audit_events", "audit_events.parquet"),
        ("auth_tokens", "auth_tokens.parquet"),
    ]

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "data" / "mvp.duckdb"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.parquet_dir = self.db_path.parent
        self.parquet_path = self.db_path.with_suffix(".parquet")

        self._con = _ThreadSafeConn(duckdb.connect(str(self.db_path)))
        self._con.execute(self.DDL)
        for stmt in self.CONTENT_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.KID_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")

        # Versioned schema migrations (A1) — replaces the old bare-except ALTERs.
        from app.migrations import run_migrations
        run_migrations(self._con)

        # Bootstrap every table from its parquet snapshot using INSERT OR IGNORE
        # (A2). This is a per-table MERGE, not the old all-or-nothing count gate:
        # rows already present (by primary key) are skipped, missing rows are
        # added. Fixes both the no-backup-path gap for kid tables and the
        # stranded-user bug where one existing row skipped the whole import.
        # Path is a bound parameter (H-10); table names are a fixed allowlist.
        for table, pq_name in self.BOOTSTRAP_TABLES:
            pq = self.parquet_dir / pq_name
            if not pq.exists():
                continue
            try:
                self._con.execute(
                    f"INSERT OR IGNORE INTO {table} SELECT * FROM read_parquet(?)",
                    [str(pq)],
                )
                logger.info(f"[duckdb] bootstrap-merged {table} from {pq_name}")
            except Exception as exc:
                # A schema-mismatched snapshot (older column set) shouldn't take
                # the whole boot down — log and continue. The live table keeps
                # whatever it has.
                logger.warning(f"[duckdb] bootstrap of {table} from {pq_name} skipped: {exc}")

        logger.info(f"[duckdb] opened {self.db_path}")

    # ── StorageBackend interface ──────────────────────────────────────

    def save_user_data(self, user_id: str, name: str, data: Dict[str, Any]) -> None:
        try:
            payload = json.dumps(data, ensure_ascii=False)
            self._con.execute(
                """
                INSERT INTO user_data (user_id, name, data, updated_at)
                VALUES (?, ?, ?, now())
                ON CONFLICT (user_id, name)
                DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
                """,
                [user_id, name, payload],
            )
            logger.debug(f"[duckdb] saved {name} for user {user_id}")
        except Exception as exc:
            logger.error(f"[duckdb] failed to save {name} for user {user_id}: {exc}")

    def load_user_data(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        try:
            row = self._con.execute(
                "SELECT data FROM user_data WHERE user_id = ? AND name = ?",
                [user_id, name],
            ).fetchone()
            if row is None:
                return None
            return json.loads(row[0])
        except Exception as exc:
            logger.error(f"[duckdb] failed to load {name} for user {user_id}: {exc}")
            return None

    def list_users(self) -> Iterable[str]:
        try:
            rows = self._con.execute(
                "SELECT DISTINCT user_id FROM user_data ORDER BY user_id"
            ).fetchall()
            return [r[0] for r in rows]
        except Exception as exc:
            logger.error(f"[duckdb] failed to list users: {exc}")
            return []

    # ── Content query methods ─────────────────────────────────────────

    def get_categories(self) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, name, emoji, description FROM categories ORDER BY id"
        ).fetchall()
        return [{"id": r[0], "name": r[1], "emoji": r[2], "description": r[3]} for r in rows]

    def get_articles(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if category:
            rows = self._con.execute(
                "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags "
                "FROM articles WHERE category = ? ORDER BY id LIMIT ?",
                [category, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags "
                "FROM articles ORDER BY id LIMIT ?",
                [limit],
            ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags, content "
            "FROM articles WHERE id = ?",
            [article_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "category": row[1], "title": row[2], "subtitle": row[3],
            "emoji": row[4], "author": row[5], "read_time": row[6], "summary": row[7],
            "tags": list(row[8]) if row[8] else [], "content": row[9],
        }

    def get_community_posts(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if category:
            rows = self._con.execute(
                "SELECT id, category, initials, name, title, preview "
                "FROM community_posts WHERE category = ? ORDER BY id LIMIT ?",
                [category, limit],
            ).fetchall()
            posts = [
                {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
                 "title": r[4], "preview": r[5]}
                for r in rows
            ]
        else:
            rows = self._con.execute(
                "SELECT id, category, initials, name, title, preview "
                "FROM community_posts ORDER BY id LIMIT ?",
                [limit],
            ).fetchall()
            posts = [
                {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
                 "title": r[4], "preview": r[5]}
                for r in rows
            ]
        # Add reply counts
        post_ids = [p["id"] for p in posts]
        if post_ids:
            counts = self.get_reply_counts(post_ids)
            for p in posts:
                p["reply_count"] = counts.get(p["id"], 0)
        return posts

    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags "
            "FROM articles "
            "WHERE title ILIKE ? OR subtitle ILIKE ? OR summary ILIKE ? OR array_to_string(tags, ' ') ILIKE ? "
            "ORDER BY id LIMIT ?",
            [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit],
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def search_community_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, category, initials, name, title, preview "
            "FROM community_posts "
            "WHERE title ILIKE ? OR preview ILIKE ? "
            "ORDER BY id LIMIT ?",
            [f"%{query}%", f"%{query}%", limit],
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
             "title": r[4], "preview": r[5]}
            for r in rows
        ]

    def score_articles_by_words(self, words: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Score articles by counting how many topic words match title/subtitle/tags."""
        # Build a SUM(CASE ...) expression for each word
        cases = " + ".join(
            f"(CASE WHEN title ILIKE '%' || ${i+1} || '%' OR subtitle ILIKE '%' || ${i+1} || '%' "
            f"OR array_to_string(tags, ' ') ILIKE '%' || ${i+1} || '%' THEN 1 ELSE 0 END)"
            for i in range(len(words))
        )
        sql = (
            f"SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags, "
            f"({cases}) AS score "
            f"FROM articles HAVING score > 0 ORDER BY score DESC LIMIT ?"
        )
        rows = self._con.execute(sql, words + [limit]).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def score_posts_by_words(self, words: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Score community posts by counting how many topic words match title/preview."""
        cases = " + ".join(
            f"(CASE WHEN title ILIKE '%' || ${i+1} || '%' OR preview ILIKE '%' || ${i+1} || '%' "
            f"THEN 1 ELSE 0 END)"
            for i in range(len(words))
        )
        sql = (
            f"SELECT id, category, initials, name, title, preview, "
            f"({cases}) AS score "
            f"FROM community_posts HAVING score > 0 ORDER BY score DESC LIMIT ?"
        )
        rows = self._con.execute(sql, words + [limit]).fetchall()
        return [
            {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
             "title": r[4], "preview": r[5]}
            for r in rows
        ]

    # ── Content CRUD methods ─────────────────────────────────────────

    def create_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO articles (id, category, title, subtitle, emoji, author, read_time, summary, tags, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())",
            [data["id"], data["category"], data["title"], data.get("subtitle", ""),
             data.get("emoji", ""), data.get("author", "MVP Editorial"),
             data.get("read_time", ""), data.get("summary", ""),
             data.get("tags", []), data.get("content", "")],
        )
        return self.get_article(data["id"])

    def update_article(self, article_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_article(article_id)
        if existing is None:
            return None
        fields = []
        values = []
        for key in ("category", "title", "subtitle", "emoji", "author", "read_time", "summary", "tags", "content"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return existing
        fields.append("updated_at = now()")
        values.append(article_id)
        self._con.execute(
            f"UPDATE articles SET {', '.join(fields)} WHERE id = ?", values
        )
        return self.get_article(article_id)

    def delete_article(self, article_id: str) -> bool:
        existing = self.get_article(article_id)
        if existing is None:
            return False
        self._con.execute("DELETE FROM articles WHERE id = ?", [article_id])
        return True

    def get_community_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, category, initials, name, title, preview, user_id "
            "FROM community_posts WHERE id = ?",
            [post_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "category": row[1], "initials": row[2], "name": row[3],
            "title": row[4], "preview": row[5], "user_id": row[6],
        }

    def create_community_post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO community_posts (id, category, initials, name, title, preview, user_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, now(), now())",
            [data["id"], data["category"], data.get("initials", ""),
             data.get("name", ""), data.get("title", ""),
             data.get("preview", ""), data.get("user_id")],
        )
        return self.get_community_post(data["id"])

    def update_community_post(self, post_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_community_post(post_id)
        if existing is None:
            return None
        fields = []
        values = []
        for key in ("category", "initials", "name", "title", "preview", "user_id"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return existing
        fields.append("updated_at = now()")
        values.append(post_id)
        self._con.execute(
            f"UPDATE community_posts SET {', '.join(fields)} WHERE id = ?", values
        )
        return self.get_community_post(post_id)

    def delete_community_post(self, post_id: str) -> bool:
        existing = self.get_community_post(post_id)
        if existing is None:
            return False
        self._con.execute("DELETE FROM community_posts WHERE id = ?", [post_id])
        return True

    def get_replies_for_post(self, post_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, post_id, user_id, author_name, initials, body "
            "FROM post_replies WHERE post_id = ? ORDER BY created_at ASC LIMIT ?",
            [post_id, limit],
        ).fetchall()
        return [
            {"id": r[0], "post_id": r[1], "user_id": r[2], "author_name": r[3],
             "initials": r[4], "body": r[5]}
            for r in rows
        ]

    def create_reply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO post_replies (id, post_id, user_id, author_name, initials, body, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, now())",
            [data["id"], data["post_id"], data["user_id"], data.get("author_name", ""),
             data.get("initials", ""), data.get("body", "")],
        )
        return {"id": data["id"], "post_id": data["post_id"], "user_id": data["user_id"],
                "author_name": data.get("author_name", ""), "initials": data.get("initials", ""),
                "body": data.get("body", "")}

    def get_reply_counts(self, post_ids: List[str]) -> Dict[str, int]:
        if not post_ids:
            return {}
        placeholders = ", ".join(["?"] * len(post_ids))
        rows = self._con.execute(
            f"SELECT post_id, count(*) FROM post_replies WHERE post_id IN ({placeholders}) GROUP BY post_id",
            post_ids,
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO categories (id, name, emoji, description) VALUES (?, ?, ?, ?)",
            [data["id"], data["name"], data.get("emoji", ""), data.get("description", "")],
        )
        return {"id": data["id"], "name": data["name"], "emoji": data.get("emoji", ""), "description": data.get("description", "")}

    def update_category(self, category_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._con.execute("SELECT id FROM categories WHERE id = ?", [category_id]).fetchone()
        if row is None:
            return None
        fields = []
        values = []
        for key in ("name", "emoji", "description"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return self._get_category(category_id)
        values.append(category_id)
        self._con.execute(
            f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", values
        )
        return self._get_category(category_id)

    def delete_category(self, category_id: str) -> bool:
        row = self._con.execute("SELECT id FROM categories WHERE id = ?", [category_id]).fetchone()
        if row is None:
            return False
        self._con.execute("DELETE FROM categories WHERE id = ?", [category_id])
        return True

    def _get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, name, emoji, description FROM categories WHERE id = ?", [category_id]
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "emoji": row[2], "description": row[3]}

    def get_content_stats(self) -> Dict[str, Any]:
        articles_count = self._con.execute("SELECT count(*) FROM articles").fetchone()[0]
        posts_count = self._con.execute("SELECT count(*) FROM community_posts").fetchone()[0]
        categories_count = self._con.execute("SELECT count(*) FROM categories").fetchone()[0]
        articles_by_cat = self._con.execute(
            "SELECT category, count(*) FROM articles GROUP BY category ORDER BY category"
        ).fetchall()
        posts_by_cat = self._con.execute(
            "SELECT category, count(*) FROM community_posts GROUP BY category ORDER BY category"
        ).fetchall()
        return {
            "articles": articles_count,
            "community_posts": posts_count,
            "categories": categories_count,
            "articles_by_category": {r[0]: r[1] for r in articles_by_cat},
            "posts_by_category": {r[0]: r[1] for r in posts_by_cat},
        }

    # ── Family Companion (kid agent) ─────────────────────────────────

    def save_kid_agent_config(
        self,
        user_id: str,
        kid_name: str,
        invariants: Dict[str, Any],
        free_text_brief: str,
        system_prompt: str,
        content_hash: str,
        model: str,
        enabled: bool,
        expected_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Append a new versioned config row. The "current" config for a (user, kid)
        is the row with the highest version. expected_version supports optimistic
        concurrency: pass the version the caller thinks is current, and the
        function will refuse to write if that's stale.

        Raises ValueError on version conflict.
        """
        import uuid

        latest = self._con.execute(
            "SELECT max(version) FROM kid_agent_configs WHERE user_id = ? AND kid_name = ?",
            [user_id, kid_name],
        ).fetchone()
        current_version = (latest[0] if latest and latest[0] is not None else 0)

        if expected_version is not None and expected_version != current_version:
            raise ValueError(
                f"version conflict: caller had v{expected_version}, current is v{current_version}"
            )

        new_version = current_version + 1
        config_id = str(uuid.uuid4())
        invariants_json = json.dumps(invariants, ensure_ascii=False)

        try:
            self._con.execute(
                """
                INSERT INTO kid_agent_configs (
                    id, user_id, kid_name, version, invariants_json,
                    free_text_brief, system_prompt, content_hash, model, enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
                """,
                [
                    config_id, user_id, kid_name, new_version, invariants_json,
                    free_text_brief, system_prompt, content_hash, model, enabled,
                ],
            )
        except duckdb.ConstraintException as exc:
            # uq_kid_agent_configs_version: a concurrent writer already landed
            # this version. Surface as a version conflict (mapped to 409) — the
            # DB-level guard for the check+insert TOCTOU race (B-9).
            raise ValueError(
                f"version conflict: v{new_version} for {user_id}/{kid_name} was "
                f"written concurrently; retry with the latest version"
            ) from exc
        logger.info(f"[duckdb] saved kid_agent_config v{new_version} for {user_id}/{kid_name}")
        return self.get_kid_agent_config(user_id, kid_name)

    def get_kid_agent_config(self, user_id: str, kid_name: str) -> Optional[Dict[str, Any]]:
        """Return the highest-version config row for (user_id, kid_name), or None."""
        row = self._con.execute(
            """
            SELECT id, user_id, kid_name, version, invariants_json, free_text_brief,
                   system_prompt, content_hash, model, enabled, created_at
            FROM kid_agent_configs
            WHERE user_id = ? AND kid_name = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            [user_id, kid_name],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "kid_name": row[2],
            "version": row[3],
            "invariants": json.loads(row[4]),
            "free_text_brief": row[5],
            "system_prompt": row[6],
            "content_hash": row[7],
            "model": row[8],
            "enabled": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
        }

    def list_kid_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """Return the latest config for each kid belonging to user_id."""
        rows = self._con.execute(
            """
            SELECT kid_name, max(version) AS v
            FROM kid_agent_configs
            WHERE user_id = ?
            GROUP BY kid_name
            ORDER BY kid_name
            """,
            [user_id],
        ).fetchall()
        results = []
        for kid_name, _ in rows:
            cfg = self.get_kid_agent_config(user_id, kid_name)
            if cfg:
                results.append(cfg)
        return results

    def append_kid_message(
        self,
        agent_id: str,
        thread_id: str,
        role: str,
        content: str,
        moderation_score: Optional[float] = None,
        age_score: Optional[float] = None,
        voice_score: Optional[float] = None,
        parent_flagged: bool = False,
    ) -> str:
        """Append a kid-chat message; returns the new message id."""
        import uuid
        message_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO kid_messages (
                id, agent_id, thread_id, role, content,
                moderation_score, age_score, voice_score, parent_flagged, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                message_id, agent_id, thread_id, role, content,
                moderation_score, age_score, voice_score, parent_flagged,
            ],
        )
        return message_id

    def get_kid_messages(
        self,
        agent_id: str,
        thread_id: str = "default",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Return messages for a kid agent thread, oldest first."""
        rows = self._con.execute(
            """
            SELECT id, role, content, moderation_score, age_score, voice_score,
                   parent_flagged, created_at
            FROM kid_messages
            WHERE agent_id = ? AND thread_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            [agent_id, thread_id, limit],
        ).fetchall()
        return [
            {
                "id": r[0],
                "role": r[1],
                "content": r[2],
                "moderation_score": r[3],
                "age_score": r[4],
                "voice_score": r[5],
                "parent_flagged": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
            }
            for r in rows
        ]

    def set_kid_pin(self, user_id: str, kid_name: str, pin_hash: str) -> None:
        """Upsert a kid PIN. Caller must provide a bcrypt hash."""
        self._con.execute(
            """
            INSERT INTO kid_credentials (user_id, kid_name, pin_hash, last_rotated_at)
            VALUES (?, ?, ?, now())
            ON CONFLICT (user_id, kid_name)
            DO UPDATE SET pin_hash = excluded.pin_hash, last_rotated_at = excluded.last_rotated_at
            """,
            [user_id, kid_name, pin_hash],
        )

    def get_kid_pin_hash(self, user_id: str, kid_name: str) -> Optional[str]:
        row = self._con.execute(
            "SELECT pin_hash FROM kid_credentials WHERE user_id = ? AND kid_name = ?",
            [user_id, kid_name],
        ).fetchone()
        return row[0] if row else None

    def log_moderation_event(
        self,
        user_id: str,
        kid_name: str,
        severity: str,
        category: str,
        action: str,
        agent_id: Optional[str] = None,
        message_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        parent_notified_at: Optional[str] = None,
    ) -> str:
        """Record a moderation event. Returns the event id."""
        import uuid
        event_id = str(uuid.uuid4())
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        self._con.execute(
            """
            INSERT INTO moderation_events (
                id, user_id, kid_name, agent_id, message_id,
                severity, category, action, details, parent_notified_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                event_id, user_id, kid_name, agent_id, message_id,
                severity, category, action, details_json, parent_notified_at,
            ],
        )
        logger.warning(
            f"[moderation] {severity}/{category}/{action} user={user_id} kid={kid_name}"
        )
        return event_id

    def get_moderation_events(
        self,
        user_id: str,
        kid_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        if kid_name:
            rows = self._con.execute(
                """
                SELECT id, kid_name, agent_id, message_id, severity, category,
                       action, details, parent_notified_at, created_at
                FROM moderation_events
                WHERE user_id = ? AND kid_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, kid_name, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                """
                SELECT id, kid_name, agent_id, message_id, severity, category,
                       action, details, parent_notified_at, created_at
                FROM moderation_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, limit],
            ).fetchall()
        return [
            {
                "id": r[0],
                "kid_name": r[1],
                "agent_id": r[2],
                "message_id": r[3],
                "severity": r[4],
                "category": r[5],
                "action": r[6],
                "details": json.loads(r[7]) if r[7] else None,
                "parent_notified_at": r[8].isoformat() if r[8] else None,
                "created_at": r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ]

    # ── Auth tokens ──────────────────────────────────────────────────

    AUTH_TOKEN_TTL_DAYS = int(os.getenv("AUTH_TOKEN_TTL_DAYS", "30"))

    @staticmethod
    def _hash_token(raw: str) -> str:
        import hashlib
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def issue_auth_token(self, user_id: str) -> str:
        """
        Generate a fresh raw token, persist its sha256 hash, return the raw
        token to the caller. Server never sees the raw token at rest again.
        """
        import uuid
        from datetime import datetime, timedelta, timezone
        raw = uuid.uuid4().hex
        token_hash = self._hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.AUTH_TOKEN_TTL_DAYS)
        self._con.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) "
            "VALUES (?, ?, now(), ?)",
            [token_hash, user_id, expires_at],
        )
        return raw

    def lookup_auth_token(self, token: str) -> Optional[str]:
        """
        Return user_id for an active, unexpired, non-revoked token.
        Refuses tokens with NULL expires_at (legacy plaintext rows).
        """
        token_hash = self._hash_token(token)
        row = self._con.execute(
            "SELECT user_id FROM auth_tokens "
            "WHERE token = ? "
            "  AND revoked_at IS NULL "
            "  AND expires_at IS NOT NULL "
            "  AND expires_at > now()",
            [token_hash],
        ).fetchone()
        if row is None:
            return None
        # Update last_used_at fire-and-forget; failure here doesn't deny.
        try:
            self._con.execute(
                "UPDATE auth_tokens SET last_used_at = now() WHERE token = ?",
                [token_hash],
            )
        except Exception:
            pass
        return row[0]

    def revoke_auth_token(self, token: str) -> None:
        token_hash = self._hash_token(token)
        self._con.execute(
            "UPDATE auth_tokens SET revoked_at = now() WHERE token = ?",
            [token_hash],
        )

    def write_audit_event(
        self, *, user_id: Optional[str], actor: Optional[str],
        action: str, details: Optional[Dict[str, Any]] = None,
    ) -> str:
        import uuid
        event_id = uuid.uuid4().hex
        self._con.execute(
            "INSERT INTO audit_events (id, user_id, actor, action, details) "
            "VALUES (?, ?, ?, ?, ?)",
            [event_id, user_id, actor, action,
             json.dumps(details or {})],
        )
        return event_id

    def delete_family(self, *, user_id: str, actor: str) -> Dict[str, Any]:
        """
        Cascade-delete every row keyed to user_id across all tables that hold
        family data. Returns {"counts": {table: rows}, "agent_ids": [...]} —
        the caller uses agent_ids to abort in-flight streams (H-5). Always
        writes an audit_events row LAST so the delete itself is logged.

        Tables touched (every one that references user_id):
            user_data, kid_agent_configs, kid_messages (via agent_id),
            kid_credentials, moderation_events, kid_agent_crisis_locks,
            auth_tokens, daily_summaries, consent_records.

        Tables left intact: content (categories/articles/community_posts/
        post_replies) and audit_events itself.
        """
        deleted: Dict[str, int] = {}

        # Wrap the whole cascade in one transaction (A5) so a kill mid-delete
        # can't leave a half-deleted family (e.g. user_data gone but consent +
        # auth_tokens still present). The proxy holds the connection lock for
        # the duration, so no other thread joins this transaction.
        with self._con.transaction():
            # kid_messages joins via agent_id, so collect agent_ids first and
            # snapshot the pre-delete row count before running DELETEs.
            agent_ids = [r[0] for r in self._con.execute(
                "SELECT id FROM kid_agent_configs WHERE user_id = ?",
                [user_id],
            ).fetchall()]
            if agent_ids:
                placeholders = ",".join(["?"] * len(agent_ids))
                deleted["kid_messages"] = self._con.execute(
                    f"SELECT count(*) FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                )
            else:
                deleted["kid_messages"] = 0

            for table in [
                "kid_agent_crisis_locks",
                "kid_agent_configs",
                "kid_credentials",
                "moderation_events",
                "auth_tokens",
                "daily_summaries",
                "consent_records",
                "user_data",
            ]:
                pre = self._con.execute(
                    f"SELECT count(*) FROM {table} WHERE user_id = ?",
                    [user_id],
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM {table} WHERE user_id = ?", [user_id],
                )
                deleted[table] = pre

            self.write_audit_event(
                user_id=user_id, actor=actor,
                action="family_deleted", details={"counts": deleted},
            )
        return {"counts": deleted, "agent_ids": agent_ids}

    # ── Crisis locks ─────────────────────────────────────────────────

    def lock_kid_agent_for_crisis(
        self, *, agent_id: str, user_id: str, kid_name: str,
        category: str, severity: str, reason: str,
    ) -> None:
        """
        Persist a crisis lock for an agent. Idempotent: re-locking refreshes the
        timestamp. Survives restarts (replaces the in-process _killed_agents
        set, which didn't).
        """
        self._con.execute(
            """
            INSERT INTO kid_agent_crisis_locks
                (agent_id, user_id, kid_name, locked_at, category, severity, reason)
            VALUES (?, ?, ?, now(), ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                locked_at = now(),
                category = excluded.category,
                severity = excluded.severity,
                reason = excluded.reason,
                revived_at = NULL,
                revived_by = NULL
            """,
            [agent_id, user_id, kid_name, category, severity, reason],
        )
        # Mirror to kid_agent_configs.enabled so the existing "is enabled?"
        # check in /kid-chat remains the single read-side gate.
        self._con.execute(
            "UPDATE kid_agent_configs SET enabled = FALSE WHERE id = ?",
            [agent_id],
        )

    def is_kid_agent_crisis_locked(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return the active crisis lock row (or None if not locked)."""
        row = self._con.execute(
            """
            SELECT user_id, kid_name, locked_at, category, severity, reason
            FROM kid_agent_crisis_locks
            WHERE agent_id = ? AND revived_at IS NULL
            """,
            [agent_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "agent_id": agent_id,
            "user_id": row[0],
            "kid_name": row[1],
            "locked_at": row[2],
            "category": row[3],
            "severity": row[4],
            "reason": row[5],
        }

    def revive_kid_agent_from_crisis(self, *, agent_id: str, by: str) -> bool:
        """Mark a crisis lock as cleared. Returns True if a lock was active."""
        result = self._con.execute(
            """
            UPDATE kid_agent_crisis_locks
            SET revived_at = now(), revived_by = ?
            WHERE agent_id = ? AND revived_at IS NULL
            """,
            [by, agent_id],
        )
        # rowcount on duckdb returns -1; verify via separate read
        active = self._con.execute(
            "SELECT count(*) FROM kid_agent_crisis_locks "
            "WHERE agent_id = ? AND revived_at IS NULL",
            [agent_id],
        ).fetchone()[0]
        return active == 0

    def set_kid_agent_enabled(self, agent_id: str, enabled: bool) -> None:
        """Toggle the enabled flag on a single agent config (used by crisis revive)."""
        self._con.execute(
            "UPDATE kid_agent_configs SET enabled = ? WHERE id = ?",
            [enabled, agent_id],
        )

    def list_active_crisis_locks(self, user_id: str) -> List[Dict[str, Any]]:
        """All currently-locked agents for a parent user."""
        rows = self._con.execute(
            """
            SELECT agent_id, kid_name, locked_at, category, severity, reason
            FROM kid_agent_crisis_locks
            WHERE user_id = ? AND revived_at IS NULL
            ORDER BY locked_at DESC
            """,
            [user_id],
        ).fetchall()
        return [
            {
                "agent_id": r[0], "kid_name": r[1], "locked_at": r[2],
                "category": r[3], "severity": r[4], "reason": r[5],
            }
            for r in rows
        ]

    # ── Consent records ──────────────────────────────────────────────

    def record_consent(
        self,
        *,
        user_id: str,
        parent_name: Optional[str],
        parent_email: Optional[str],
        kid_age_band: Optional[str],
        agreement_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        import uuid
        record_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO consent_records (
                id, user_id, parent_name, parent_email, kid_age_band,
                agreement_version, accepted_at, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, now(), ?, ?)
            """,
            [
                record_id, user_id, parent_name, parent_email, kid_age_band,
                agreement_version, ip_address, user_agent,
            ],
        )
        return {
            "id": record_id, "user_id": user_id, "agreement_version": agreement_version,
        }

    def latest_consent(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT id, agreement_version, accepted_at, parent_name, parent_email,
                   kid_age_band
            FROM consent_records
            WHERE user_id = ?
            ORDER BY accepted_at DESC
            LIMIT 1
            """,
            [user_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "agreement_version": row[1],
            "accepted_at": row[2].isoformat() if row[2] else None,
            "parent_name": row[3],
            "parent_email": row[4],
            "kid_age_band": row[5],
        }

    # ── Daily summaries ──────────────────────────────────────────────

    def get_kid_messages_in_range(
        self,
        agent_id: str,
        start_iso: str,
        end_iso: str,
        thread_id: str = "default",
    ) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            """
            SELECT id, role, content, created_at
            FROM kid_messages
            WHERE agent_id = ? AND thread_id = ?
              AND created_at >= ? AND created_at < ?
            ORDER BY created_at ASC
            """,
            [agent_id, thread_id, start_iso, end_iso],
        ).fetchall()
        return [
            {"id": r[0], "role": r[1], "content": r[2],
             "created_at": r[3].isoformat() if r[3] else None}
            for r in rows
        ]

    def save_daily_summary(
        self,
        *,
        user_id: str,
        kid_name: str,
        summary_date: str,                 # 'YYYY-MM-DD'
        agent_id: Optional[str],
        message_count: int,
        headline: str,
        curiosity: Optional[str],
        frustration: Optional[str],
        prompt_for_parent: Optional[str],
        full_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        import uuid
        record_id = str(uuid.uuid4())
        # Upsert by (user_id, kid_name, date)
        existing = self._con.execute(
            "SELECT id FROM daily_summaries WHERE user_id=? AND kid_name=? AND summary_date=?",
            [user_id, kid_name, summary_date],
        ).fetchone()
        full_json_str = json.dumps(full_json, ensure_ascii=False)
        if existing:
            self._con.execute(
                """
                UPDATE daily_summaries SET
                    agent_id=?, message_count=?, headline=?, curiosity=?, frustration=?,
                    prompt_for_parent=?, full_json=?, created_at=now()
                WHERE id=?
                """,
                [agent_id, message_count, headline, curiosity, frustration,
                 prompt_for_parent, full_json_str, existing[0]],
            )
            return self.get_daily_summary(user_id, kid_name, summary_date)
        else:
            self._con.execute(
                """
                INSERT INTO daily_summaries (
                    id, user_id, kid_name, summary_date, agent_id, message_count,
                    headline, curiosity, frustration, prompt_for_parent, full_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
                """,
                [record_id, user_id, kid_name, summary_date, agent_id, message_count,
                 headline, curiosity, frustration, prompt_for_parent, full_json_str],
            )
            return self.get_daily_summary(user_id, kid_name, summary_date)

    def get_daily_summary(
        self, user_id: str, kid_name: str, summary_date: str,
    ) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT id, summary_date, agent_id, message_count, headline, curiosity,
                   frustration, prompt_for_parent, full_json, created_at
            FROM daily_summaries
            WHERE user_id = ? AND kid_name = ? AND summary_date = ?
            """,
            [user_id, kid_name, summary_date],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "summary_date": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
            "agent_id": row[2],
            "message_count": row[3],
            "headline": row[4],
            "curiosity": row[5],
            "frustration": row[6],
            "prompt_for_parent": row[7],
            "full_json": json.loads(row[8]) if row[8] else None,
            "created_at": row[9].isoformat() if row[9] else None,
        }

    def list_daily_summaries(
        self, user_id: str, kid_name: Optional[str] = None, limit: int = 30,
    ) -> List[Dict[str, Any]]:
        if kid_name:
            rows = self._con.execute(
                """
                SELECT id, kid_name, summary_date, message_count, headline,
                       curiosity, frustration, prompt_for_parent, created_at
                FROM daily_summaries
                WHERE user_id = ? AND kid_name = ?
                ORDER BY summary_date DESC
                LIMIT ?
                """,
                [user_id, kid_name, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                """
                SELECT id, kid_name, summary_date, message_count, headline,
                       curiosity, frustration, prompt_for_parent, created_at
                FROM daily_summaries
                WHERE user_id = ?
                ORDER BY summary_date DESC, kid_name ASC
                LIMIT ?
                """,
                [user_id, limit],
            ).fetchall()
        return [
            {
                "id": r[0], "kid_name": r[1],
                "summary_date": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]),
                "message_count": r[3], "headline": r[4],
                "curiosity": r[5], "frustration": r[6], "prompt_for_parent": r[7],
                "created_at": r[8].isoformat() if r[8] else None,
            } for r in rows
        ]

    # ── Parquet export / import ───────────────────────────────────────

    def _export_table_atomic(self, table: str, target: Path) -> None:
        """
        Export one table to parquet atomically (A3): COPY to a .tmp file, then
        os.replace() into place. An interrupted COPY can only corrupt the .tmp,
        never the live snapshot — and replace() is atomic on the same
        filesystem, so a reader never sees a half-written file.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            self._con.execute(
                f"COPY {table} TO '{tmp}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE)"
            )
            os.replace(tmp, target)
        except Exception:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            raise

    def export_parquet(self, path: Path | str | None = None) -> Path:
        """Export the full user_data table to a parquet file (atomic)."""
        target = Path(path) if path else self.parquet_path
        self._export_table_atomic("user_data", target)
        logger.info(f"[duckdb] exported parquet → {target}")
        return target

    def export_content_parquet(self) -> None:
        """Export content tables to separate parquet files (atomic)."""
        for table in ("categories", "articles", "community_posts", "post_replies"):
            self._export_table_atomic(table, self.parquet_dir / f"{table}.parquet")

    def export_all_parquet(self) -> None:
        """
        Export every table in BOOTSTRAP_TABLES atomically (A2). This is the
        full backup path — kid/consent/audit/auth tables included, so a volume
        rebuild can recover them. user_data uses its conventional mvp.parquet
        name. Failures on individual tables are logged but don't abort the rest.
        """
        for table, pq_name in self.BOOTSTRAP_TABLES:
            target = self.parquet_dir / pq_name
            try:
                self._export_table_atomic(table, target)
            except Exception as exc:
                logger.error(f"[duckdb] export of {table} → {pq_name} failed: {exc}")

    def ping(self) -> bool:
        """Cheap liveness probe for the health check (A6): confirms the DB is
        open and answering. Raises/returns False if the connection is dead."""
        try:
            row = self._con.execute("SELECT 1").fetchone()
            return bool(row and row[0] == 1)
        except Exception:
            return False

    def close(self) -> None:
        """Export every table to parquet and close the connection."""
        try:
            self.export_all_parquet()
        except Exception as exc:
            logger.error(f"[duckdb] parquet export on close failed: {exc}")
        self._con.close()
        logger.info("[duckdb] connection closed")
