#!/bin/sh
# Seed the persistent volume with parquet files from the image.
# Copies any file that is missing OR smaller than the seed version.
echo "[entrypoint] data dir contents: $(ls -la /app/data/ 2>&1)"
echo "[entrypoint] seed dir contents: $(ls -la /app/seed-data/ 2>&1)"

if [ -d /app/seed-data ]; then
    for seed_file in /app/seed-data/*.parquet; do
        filename=$(basename "$seed_file")
        target="/app/data/$filename"
        seed_size=$(stat -c%s "$seed_file" 2>/dev/null || stat -f%z "$seed_file")

        if [ ! -f "$target" ]; then
            echo "[entrypoint] Seeding missing: $filename ($seed_size bytes)"
            cp "$seed_file" "$target"
        else
            target_size=$(stat -c%s "$target" 2>/dev/null || stat -f%z "$target")
            if [ "$seed_size" -gt "$target_size" ]; then
                echo "[entrypoint] Replacing stale: $filename (volume: $target_size → seed: $seed_size bytes)"
                cp "$seed_file" "$target"
            else
                echo "[entrypoint] Keeping: $filename (volume: $target_size bytes, seed: $seed_size bytes)"
            fi
        fi
    done
fi

# Keep the existing DuckDB on the volume — wiping it on every deploy destroyed
# kid_messages, moderation_events, consent_records, auth_tokens (they aren't
# in the parquet seed export). Fresh bootstrap only happens when the DB file
# is actually missing (cold volume).
if [ ! -f /app/data/mvp.duckdb ]; then
    echo "[entrypoint] No existing DuckDB — will bootstrap from parquet on first request."
else
    echo "[entrypoint] Preserving DuckDB on volume."
fi
# Do NOT delete the WAL (A4). DuckDB replays it automatically on connect; the
# WAL can hold committed transactions not yet checkpointed to the main file
# (e.g. after an ungraceful previous shutdown). Deleting it here would discard
# those committed writes.
echo "[entrypoint] Final: $(ls -la /app/data/*.parquet 2>&1)"

exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8080}
