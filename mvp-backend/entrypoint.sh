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

# Remove stale duckdb so it bootstraps fresh from parquet files each deploy
rm -f /app/data/*.duckdb /app/data/*.duckdb.wal
echo "[entrypoint] Cleared duckdb, will bootstrap from parquet"
echo "[entrypoint] Final: $(ls -la /app/data/*.parquet 2>&1)"

exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8080}
