#!/bin/sh
# Seed the persistent volume with parquet files from the image.
# Copies any file that is missing OR smaller than the seed version.
echo "[entrypoint] data dir contents: $(ls -la /app/data/ 2>&1)"
echo "[entrypoint] seed dir contents: $(ls -la /app/seed-data/ 2>&1)"

## ONE-TIME FORCE SEED: taxonomy refactor (2026-06-05)
## Content parquets (categories, articles, community_posts) are force-replaced
## to push the 11-parent taxonomy cleanup to production. Remove this block after
## confirming the deploy is healthy.
FORCE_SEED="categories.parquet articles.parquet community_posts.parquet post_replies.parquet"

if [ -d /app/seed-data ]; then
    for seed_file in /app/seed-data/*.parquet; do
        filename=$(basename "$seed_file")
        target="/app/data/$filename"
        seed_size=$(stat -c%s "$seed_file" 2>/dev/null || stat -f%z "$seed_file")

        # Check if this file should be force-seeded
        force=false
        for f in $FORCE_SEED; do
            if [ "$filename" = "$f" ]; then force=true; break; fi
        done

        if [ "$force" = "true" ]; then
            echo "[entrypoint] FORCE seeding (taxonomy refactor): $filename ($seed_size bytes)"
            cp "$seed_file" "$target"
        elif [ ! -f "$target" ]; then
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

# ONE-TIME: force fresh bootstrap for taxonomy refactor. The old DuckDB has
# stale categories that won't match the new parquets. Remove this rm after
# confirming the deploy is healthy.
if [ -f /app/data/mvp.duckdb ]; then
    echo "[entrypoint] REMOVING DuckDB for taxonomy refactor rebuild."
    rm -f /app/data/mvp.duckdb /app/data/mvp.duckdb.wal
fi
echo "[entrypoint] Will bootstrap fresh from parquet on first request."
# Do NOT delete the WAL (A4). DuckDB replays it automatically on connect; the
# WAL can hold committed transactions not yet checkpointed to the main file
# (e.g. after an ungraceful previous shutdown). Deleting it here would discard
# those committed writes.
echo "[entrypoint] Final: $(ls -la /app/data/*.parquet 2>&1)"

exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8080}
