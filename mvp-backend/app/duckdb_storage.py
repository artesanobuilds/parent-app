"""
DuckDB + Parquet storage backend.

Stores user data as JSON blobs in a DuckDB database backed by parquet files.
Also stores content library tables (categories, articles, community_posts).
Drop-in replacement for LocalFileStorage — same StorageBackend interface.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import duckdb

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

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "data" / "mvp.duckdb"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.parquet_dir = self.db_path.parent
        self.parquet_path = self.db_path.with_suffix(".parquet")

        self._con = duckdb.connect(str(self.db_path))
        self._con.execute(self.DDL)
        for stmt in self.CONTENT_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")

        # Bootstrap user_data from parquet if DB is empty
        if self.parquet_path.exists():
            count = self._con.execute("SELECT count(*) FROM user_data").fetchone()[0]
            if count == 0:
                logger.info(f"[duckdb] bootstrapping user_data from {self.parquet_path}")
                self._con.execute(
                    f"INSERT INTO user_data SELECT * FROM read_parquet('{self.parquet_path}')"
                )

        # Bootstrap content tables from parquet snapshots
        for table in ("categories", "articles", "community_posts", "post_replies"):
            pq = self.parquet_dir / f"{table}.parquet"
            if pq.exists():
                count = self._con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                if count == 0:
                    logger.info(f"[duckdb] bootstrapping {table} from {pq}")
                    self._con.execute(
                        f"INSERT INTO {table} SELECT * FROM read_parquet('{pq}')"
                    )

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

    # ── Parquet export / import ───────────────────────────────────────

    def export_parquet(self, path: Path | str | None = None) -> Path:
        """Export the full user_data table to a parquet file."""
        target = Path(path) if path else self.parquet_path
        target.parent.mkdir(parents=True, exist_ok=True)
        self._con.execute(
            f"COPY user_data TO '{target}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE)"
        )
        logger.info(f"[duckdb] exported parquet → {target}")
        return target

    def export_content_parquet(self) -> None:
        """Export content tables to separate parquet files."""
        for table in ("categories", "articles", "community_posts", "post_replies"):
            target = self.parquet_dir / f"{table}.parquet"
            self._con.execute(
                f"COPY {table} TO '{target}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE)"
            )
            logger.info(f"[duckdb] exported {table} parquet → {target}")

    def close(self) -> None:
        """Export to parquet and close the connection."""
        try:
            self.export_parquet()
        except Exception as exc:
            logger.error(f"[duckdb] parquet export on close failed: {exc}")
        self._con.close()
        logger.info("[duckdb] connection closed")
