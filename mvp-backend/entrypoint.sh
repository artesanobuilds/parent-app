#!/bin/sh
# Seed the persistent volume with parquet files from the image.
# Copies any file that is missing OR smaller than the seed version.
echo "[entrypoint] data dir contents: $(ls -la /app/data/ 2>&1)"
echo "[entrypoint] seed dir contents: $(ls -la /app/seed-data/ 2>&1)"

# Seed only parquets that are MISSING from the volume — i.e. a fresh volume, or
# a newly-added table's snapshot. We do NOT force-overwrite: content is edited
# live via the CMS (writes straight to the DB), so the volume copy is the source
# of truth. To change content on an existing deploy, use the CMS — not a redeploy.
if [ -d /app/seed-data ]; then
    for seed_file in /app/seed-data/*.parquet; do
        filename=$(basename "$seed_file")
        target="/app/data/$filename"
        if [ ! -f "$target" ]; then
            seed_size=$(stat -c%s "$seed_file" 2>/dev/null || stat -f%z "$seed_file")
            echo "[entrypoint] Seeding missing: $filename ($seed_size bytes)"
            cp "$seed_file" "$target"
        else
            echo "[entrypoint] Keeping volume copy: $filename"
        fi
    done
fi

# The DuckDB PERSISTS on the volume across deploys — we no longer wipe it. The
# migration framework (app/migrations.py) + the bootstrap (CREATE IF NOT EXISTS
# + parquet column-intersection merge) evolve the schema in place, so new
# tables/columns (e.g. the activity-planning tables) are added without data loss.
# Do NOT delete the WAL (A4). DuckDB replays it automatically on connect; the
# WAL can hold committed transactions not yet checkpointed to the main file
# (e.g. after an ungraceful previous shutdown). Deleting it here would discard
# those committed writes.
echo "[entrypoint] Final: $(ls -la /app/data/*.parquet 2>&1)"

exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8080}
