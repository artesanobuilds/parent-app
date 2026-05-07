#!/usr/bin/env python3
"""Migrate content_library.json into DuckDB content tables and export parquet."""

import json
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.duckdb_storage import DuckDBStorage


def main():
    json_path = Path(__file__).resolve().parent / "app" / "content_library.json"
    if not json_path.exists():
        print(f"ERROR: {json_path} not found")
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    # Accept optional --db-path argument for when the default DB is locked
    db_path = None
    if "--db-path" in sys.argv:
        idx = sys.argv.index("--db-path")
        db_path = sys.argv[idx + 1]

    storage = DuckDBStorage(db_path=db_path)

    # Clear existing content tables (idempotent re-runs)
    for table in ("community_posts", "articles", "categories"):
        storage._con.execute(f"DELETE FROM {table}")

    # Insert categories
    categories = data["categories"]
    for cat in categories:
        storage._con.execute(
            "INSERT INTO categories (id, name, emoji, description) VALUES (?, ?, ?, ?)",
            [cat["id"], cat["name"], cat["emoji"], cat.get("description", "")],
        )
    print(f"Inserted {len(categories)} categories")

    # Insert articles
    articles = data["library_articles"]
    for a in articles:
        storage._con.execute(
            "INSERT INTO articles (id, category, title, subtitle, emoji, author, read_time, summary, tags, content) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                a["id"],
                a["category"],
                a["title"],
                a.get("subtitle", ""),
                a.get("emoji", ""),
                a.get("author", "MVP Editorial"),
                a.get("read_time", ""),
                a.get("summary", ""),
                a.get("tags", []),
                a.get("content", ""),
            ],
        )
    print(f"Inserted {len(articles)} articles")

    # Insert community posts
    posts = data["community_posts"]
    for p in posts:
        storage._con.execute(
            "INSERT INTO community_posts (id, category, initials, name, title, preview) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [
                p["id"],
                p["category"],
                p.get("initials", ""),
                p.get("name", ""),
                p["title"],
                p.get("preview", ""),
            ],
        )
    print(f"Inserted {len(posts)} community posts")

    total = len(categories) + len(articles) + len(posts)
    print(f"Total: {total} items imported")

    # Export parquet snapshots
    storage.export_content_parquet()
    print("Parquet files exported")

    storage.close()
    print("Done!")


if __name__ == "__main__":
    main()
