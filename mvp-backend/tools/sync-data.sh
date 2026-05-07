#!/bin/bash
# sync-data.sh — Pull production parquet files to local data/ when they change.
# After syncing, rebuilds the local DuckDB and logs an audit trail.
#
# Usage:
#   ./tools/sync-data.sh              # one-shot sync
#   ./tools/sync-data.sh --watch      # sync every 30 minutes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data"
CHECKSUM_FILE="$DATA_DIR/.remote-checksums.json"
AUDIT_LOG="$DATA_DIR/.sync-audit.log"
REMOTE_URL="${MVP_REMOTE_URL:-https://mvp-backend-production-8678.up.railway.app}"
INTERVAL=1800  # 30 minutes

rebuild_local_db() {
    echo "  ⟳ Rebuilding local DuckDB from parquet files..."
    python3 - "$DATA_DIR" <<'PYEOF'
import sys, json
from pathlib import Path

data_dir = Path(sys.argv[1])
db_path = data_dir / "mvp.duckdb"

# Remove stale db so it's rebuilt cleanly
for f in data_dir.glob("*.duckdb"):
    f.unlink()
for f in data_dir.glob("*.duckdb.wal"):
    f.unlink()

import duckdb
con = duckdb.connect(str(db_path))

# Import the storage module to get DDL definitions
sys.path.insert(0, str(data_dir.parent))
from app.duckdb_storage import DuckDBStorage

# Create tables using the class DDL
con.execute(DuckDBStorage.DDL)
for stmt in DuckDBStorage.CONTENT_DDL.strip().split(";"):
    stmt = stmt.strip()
    if stmt:
        con.execute(stmt + ";")

# Bootstrap from parquet files
tables = {
    "user_data": "mvp.parquet",
    "categories": "categories.parquet",
    "articles": "articles.parquet",
    "community_posts": "community_posts.parquet",
    "post_replies": "post_replies.parquet",
}

summary = {}
for table, filename in tables.items():
    pq = data_dir / filename
    if pq.exists():
        con.execute(f"INSERT INTO {table} SELECT * FROM read_parquet('{pq}')")
        count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        summary[table] = count
        print(f"    ✓ {table}: {count} rows")
    else:
        summary[table] = 0
        print(f"    · {table}: no parquet file")

con.close()
# Write summary for audit log
json.dump(summary, open(str(data_dir / ".last-sync-summary.json"), "w"))
PYEOF
    echo "  ✓ Local DuckDB rebuilt"
}

log_audit() {
    local changed_files="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Read row counts from rebuild summary
    local summary=""
    if [ -f "$DATA_DIR/.last-sync-summary.json" ]; then
        summary=$(python3 -c "
import json
s = json.load(open('$DATA_DIR/.last-sync-summary.json'))
print(' | '.join(f'{k}={v}' for k,v in s.items()))
")
    fi

    # Append to audit log
    echo "[$timestamp] Synced from $REMOTE_URL" >> "$AUDIT_LOG"
    echo "  Files updated: $changed_files" >> "$AUDIT_LOG"
    echo "  Row counts: $summary" >> "$AUDIT_LOG"
    echo "---" >> "$AUDIT_LOG"

    echo "  📋 Audit logged to $(basename "$AUDIT_LOG")"
}

sync_once() {
    echo "[$(date '+%H:%M:%S')] Checking remote for changes..."

    # Ask the server to export fresh parquets and return checksums
    response=$(curl -sf "$REMOTE_URL/data/export" 2>/dev/null) || {
        echo "  ✗ Could not reach $REMOTE_URL/data/export"
        return 1
    }

    remote_checksums="$response"

    # Compare with last known checksums
    if [ -f "$CHECKSUM_FILE" ]; then
        old_checksums=$(cat "$CHECKSUM_FILE")
        if [ "$remote_checksums" = "$old_checksums" ]; then
            echo "  ✓ No changes"
            return 0
        fi
    fi

    echo "  ↓ Changes detected, downloading..."

    # Extract filenames and detect which ones changed
    changed_files=""
    files=$(echo "$remote_checksums" | python3 -c "import sys,json; [print(f) for f in json.load(sys.stdin)['checksums'].keys()]")

    # Get old checksums for per-file comparison
    old_file_checksums=""
    if [ -f "$CHECKSUM_FILE" ]; then
        old_file_checksums=$(cat "$CHECKSUM_FILE")
    fi

    for file in $files; do
        # Check if this specific file changed
        file_changed=$(python3 -c "
import json, sys
new = json.loads('$remote_checksums')['checksums'].get('$file', '')
old = json.loads('${old_file_checksums:-\"{}\"}').get('checksums', {}).get('$file', '')
print('yes' if new != old else 'no')
" 2>/dev/null || echo "yes")

        if [ "$file_changed" = "yes" ]; then
            echo "    ↓ $file (changed)"
            curl -sf "$REMOTE_URL/data/download/$file" -o "$DATA_DIR/$file.tmp" && \
                mv "$DATA_DIR/$file.tmp" "$DATA_DIR/$file"
            changed_files="$changed_files $file"
        else
            echo "    · $file (unchanged)"
        fi
    done

    # Save checksums
    echo "$remote_checksums" > "$CHECKSUM_FILE"

    # Rebuild local DuckDB from the updated parquet files
    rebuild_local_db

    # Log the sync to audit trail
    log_audit "${changed_files# }"

    echo "  ✓ Sync complete"
}

if [ "${1:-}" = "--watch" ]; then
    echo "Watching for changes every $(( INTERVAL / 60 )) minutes..."
    echo "Remote: $REMOTE_URL"
    echo "Local:  $DATA_DIR"
    echo "Audit:  $AUDIT_LOG"
    echo "Press Ctrl+C to stop"
    echo ""
    while true; do
        sync_once || true
        sleep $INTERVAL
    done
else
    sync_once
fi
