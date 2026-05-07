#!/usr/bin/env python3
"""
One-shot migration: local-storage JSON files → DuckDB + parquet.

Usage:
    python migrate_json_to_duckdb.py [--source local-storage] [--db data/mvp.duckdb]

Reads every <user>/<name>.json under the source directory and inserts
the data into the DuckDB user_data table, then exports a parquet snapshot.
"""

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent


def migrate(source_dir: Path, db_path: Path) -> None:
    # Import here so the script can show --help without duckdb installed
    from app.duckdb_storage import DuckDBStorage

    store = DuckDBStorage(db_path=db_path)

    user_dirs = sorted(p for p in source_dir.iterdir() if p.is_dir())
    if not user_dirs:
        logger.warning(f"No user directories found in {source_dir}")
        store.close()
        return

    migrated = 0
    for user_dir in user_dirs:
        user_id = user_dir.name
        json_files = sorted(user_dir.glob("*.json"))
        for jf in json_files:
            name = jf.stem  # e.g. "profiles", "chat_threads"
            try:
                data = json.loads(jf.read_text())
                store.save_user_data(user_id, name, data)
                migrated += 1
                logger.info(f"  ✓ {user_id}/{name}")
            except Exception as exc:
                logger.error(f"  ✗ {user_id}/{name}: {exc}")

    store.export_parquet()
    store.close()
    logger.info(f"Migration complete — {migrated} blob(s) imported.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate JSON storage to DuckDB + parquet")
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "local-storage",
        help="Path to the local-storage directory (default: ./local-storage)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT / "data" / "mvp.duckdb",
        help="Path to the DuckDB database file (default: ./data/mvp.duckdb)",
    )
    args = parser.parse_args()
    migrate(args.source, args.db)
