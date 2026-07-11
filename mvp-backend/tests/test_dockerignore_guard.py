"""Deploy-hazard guard: every USER-STATE parquet in the bootstrap/export set
must be excluded from the Docker build context.

`railway up` uploads the working tree — a user-state parquet that isn't in
`.dockerignore` gets baked into the image, and a volume rebuild would then
seed prod with the developer's local data (memory
`debugging_railway_parquet_deploy_hazard`). Phase 4's watchlist tables shipped
in BOOTSTRAP_TABLES but missed `.dockerignore` and were only caught by hand at
deploy time — this test makes the pairing structural: add a table to
BOOTSTRAP_TABLES and the suite fails until its parquet is ignored (or
consciously listed as seed content below).
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.duckdb_storage import DuckDBStorage  # noqa: E402

# The ONLY parquets that intentionally ship in the image: read-only seed
# content (restored from git, not user state). Everything else in
# BOOTSTRAP_TABLES is user state and must be dockerignored.
CONTENT_PARQUETS = {
    "categories.parquet",
    "articles.parquet",
    "community_posts.parquet",
    "post_replies.parquet",
}


def test_every_user_state_parquet_is_dockerignored():
    ignored = {
        line.strip()
        for line in (BACKEND_ROOT / ".dockerignore").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    missing = [
        parquet
        for _table, parquet in DuckDBStorage.BOOTSTRAP_TABLES
        if parquet not in CONTENT_PARQUETS and f"data/{parquet}" not in ignored
    ]
    assert not missing, (
        f"user-state parquets NOT excluded from the Docker build context: {missing} — "
        "add `data/<name>` lines to mvp-backend/.dockerignore (or, only for "
        "read-only seed content, add to CONTENT_PARQUETS here)."
    )
