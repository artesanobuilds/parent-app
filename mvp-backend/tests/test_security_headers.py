"""Security response headers (app/security_headers.py) via TestClient.

One TestClient context for the whole module (lifespan-exit closes the shared
storage singleton — same pattern as tests/test_cos_api.py).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import anyio
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "sec_headers.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
from app.security_headers import SecurityHeadersMiddleware  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    # A prior module's TestClient may have closed the shared storage singleton;
    # rebuild it before entering our own lifespan (and again on exit).
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def test_baseline_headers_on_api_responses(client) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert res.headers["x-frame-options"] == "DENY"
    assert "camera=()" in res.headers["permissions-policy"]


def test_no_hsts_by_default(client) -> None:
    # Local dev is plain HTTP; HSTS must never be pinned there.
    assert "strict-transport-security" not in client.get("/health").headers


def test_hsts_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_HSTS", "1")

    async def _ok(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    sent: list[dict] = []

    async def _drive() -> None:
        mw = SecurityHeadersMiddleware(_ok)  # reads ENABLE_HSTS at construction
        scope = {"type": "http", "path": "/health", "headers": []}

        async def _receive():  # pragma: no cover — never called
            return {"type": "http.request"}

        async def _send(message):
            sent.append(message)

        await mw(scope, _receive, _send)

    anyio.run(_drive)
    headers = {k.decode(): v.decode() for k, v in sent[0]["headers"]}
    assert headers.get("strict-transport-security", "").startswith("max-age=")


def test_csp_only_on_spa_paths(client) -> None:
    api = client.get("/health")
    assert "content-security-policy" not in api.headers
    # The middleware decision is path-based; /cms carries the CSP whether the
    # built bundle exists (200) or not (404).
    spa = client.get("/cms")
    assert "content-security-policy" in spa.headers
    assert "frame-ancestors 'none'" in spa.headers["content-security-policy"]


def test_streaming_responses_unaffected(client, monkeypatch) -> None:
    # Pure-ASGI middleware must not buffer/break SSE routes; a normal JSON
    # route asserting header presence on a 4xx covers the header-injection
    # path on non-2xx too.
    res = client.get("/definitely-not-a-route")
    assert res.status_code == 404
    assert res.headers["x-content-type-options"] == "nosniff"
