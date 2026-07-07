"""Phase 3b — scoped share links: mint (authed) → view (public, no login),
with scope filtering and revoke/expiry enforced at the token layer."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", tempfile.mktemp(suffix=".duckdb"))


def test_share_link_mint_and_public_view(tmp_path):
    from fastapi.testclient import TestClient
    from app.duckdb_storage import DuckDBStorage
    import app.server as server
    # Isolate on a fresh DB (and restore) so this test neither inherits a
    # closed shared connection from a prior test nor leaves one behind.
    prev = server.storage_backend
    server.storage_backend = DuckDBStorage(db_path=str(tmp_path / "share.duckdb"))
    try:
        with TestClient(server.app) as client:
            uid = "share-test-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # Mint requires auth.
            assert client.post("/cos/plan/share", json={"user_id": uid, "scope": "logistics"}).status_code == 401

            r = client.post("/cos/plan/share", json={"user_id": uid, "scope": "logistics", "label": "Nanny"}, headers=auth)
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["scope"] == "logistics" and body["token"] and body["url"].endswith("/share/" + body["token"])
            raw = body["token"]

            # Public view — NO auth header — renders HTML.
            v = client.get(f"/share/{raw}")
            assert v.status_code == 200
            assert "text/html" in v.headers["content-type"]
            assert "coverage" in v.text.lower() or "schedule" in v.text.lower()

            # It's listed for the owner.
            shares = client.get("/cos/plan/shares", headers=auth).json()["shares"]
            assert any(s["scope"] == "logistics" for s in shares)

            # A bogus token → 404 page, not a crash.
            assert client.get("/share/not-a-real-token").status_code == 404
    finally:
        server.storage_backend = prev
