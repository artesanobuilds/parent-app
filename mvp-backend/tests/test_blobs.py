"""Profile photos on Railway Storage Buckets (2026-07-18).

The invariants that matter:
  • Keys are SERVER-derived (u/{user_id}/...) — a client-supplied key would be
    a cross-family read/write primitive. Attach verifies ownership + existence.
  • avatar_key is NOT PATCHable — the whitelists subtract it, so a client
    can't PATCH in another family's key and presign their kid's photo.
  • GET /profile presigns at read time (key stored, never a URL).
  • Deletes cascade: kid delete removes the kid's object; family delete sweeps
    the whole u/{user_id}/ prefix (list + batch — no native prefix delete).
  • Unconfigured = hard no-op (local dev default): upload-url 503s, reads omit
    avatar_url, delete_all returns 0.

A stub S3 client stands in for boto3 — no bucket, no network.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "blobs.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app import blobs  # noqa: E402


class FakeS3:
    """Just enough of the boto3 S3 client surface for app.blobs."""

    def __init__(self):
        self.objects: set[str] = set()
        self.deleted: list[str] = []

    def generate_presigned_url(self, op, Params=None, ExpiresIn=None):
        return f"https://stub.example/{op}/{Params['Key']}"

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise RuntimeError("404")
        return {"ContentLength": 123, "ContentType": "image/jpeg"}

    def delete_object(self, Bucket, Key):
        self.objects.discard(Key)
        self.deleted.append(Key)

    def delete_objects(self, Bucket, Delete):
        for entry in Delete["Objects"]:
            self.delete_object(Bucket, entry["Key"])

    def get_paginator(self, op):
        objects = self.objects

        class _Paginator:
            def paginate(self, Bucket, Prefix):
                contents = [{"Key": k} for k in sorted(objects) if k.startswith(Prefix)]
                return [{"Contents": contents}] if contents else [{}]

        return _Paginator()


def _configure(monkeypatch) -> FakeS3:
    monkeypatch.setenv("BLOB_BUCKET", "test-bucket")
    monkeypatch.setenv("BLOB_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("BLOB_SECRET_ACCESS_KEY", "s")
    monkeypatch.setenv("BLOB_ENDPOINT", "https://storage.railway.app")
    fake = FakeS3()
    monkeypatch.setattr(blobs, "_client_cache", fake)
    return fake


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


# --------------------------------------------------------------------------- #
# Environment guard
# --------------------------------------------------------------------------- #

# The prod bucket's name (not a secret — it's in every presigned URL). A dev
# environment that points BLOB_* here can read AND delete real families'
# photos — the exact hazard per-environment buckets exist to prevent.
PROD_BUCKET = "photos-blob-s9qqmpzeamgcz"


def test_local_env_never_points_at_the_prod_bucket():
    """Runs against the AMBIENT env (no monkeypatch on purpose): if this
    machine has BLOB_* set — e.g. for the moto dev emulator — it must not be
    the prod bucket. Local dev belongs on moto or a dedicated dev bucket;
    prod creds live in the untracked .env.production, never the loaded env."""
    bucket = os.getenv("BLOB_BUCKET")
    if not bucket:
        return  # unconfigured local default — the hard no-op
    assert bucket != PROD_BUCKET, (
        "local BLOB_BUCKET is the PROD bucket — move prod creds to "
        ".env.production and point local dev at moto (tools/dev_blob_server.py)"
    )


# --------------------------------------------------------------------------- #
# Module unit
# --------------------------------------------------------------------------- #


def test_unconfigured_is_a_hard_noop(monkeypatch):
    for var in ("BLOB_BUCKET", "BLOB_ACCESS_KEY_ID", "BLOB_SECRET_ACCESS_KEY", "BLOB_ENDPOINT"):
        monkeypatch.delenv(var, raising=False)
    assert blobs.is_configured() is False
    assert blobs.presign_get("u/x/avatar/y.jpg") is None
    assert blobs.delete_all("u/x/") == 0
    blobs.delete("u/x/avatar/y.jpg")  # must not raise


def test_key_derivation_and_ownership(monkeypatch):
    _configure(monkeypatch)
    key = blobs.new_key(user_id="fam1", kind="avatar", content_type="image/png")
    assert key.startswith("u/fam1/avatar/") and key.endswith(".png")
    assert blobs.key_belongs_to(key, "fam1")
    assert not blobs.key_belongs_to(key, "fam2")


def test_delete_all_sweeps_only_the_prefix(monkeypatch):
    fake = _configure(monkeypatch)
    fake.objects = {"u/a/avatar/1.jpg", "u/a/ingest/2.jpg", "u/b/avatar/3.jpg"}
    assert blobs.delete_all("u/a/") == 2
    assert fake.objects == {"u/b/avatar/3.jpg"}


# --------------------------------------------------------------------------- #
# HTTP round-trip
# --------------------------------------------------------------------------- #


def test_avatar_http_round_trip(monkeypatch):
    from fastapi.testclient import TestClient
    import app.server as server

    fake = _configure(monkeypatch)
    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            user_id = "blob-http-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}
            client.patch("/profile/kids/Nia", json={"age": "6"}, headers=auth)

            # ── upload-url: server-derived key + input validation ────
            assert client.post("/blobs/upload-url", json={
                "kind": "avatar", "content_type": "image/jpeg", "byte_size": 1000
            }).status_code == 401
            r = client.post("/blobs/upload-url", json={
                "kind": "avatar", "content_type": "image/jpeg", "byte_size": 1000
            }, headers=auth)
            assert r.status_code == 200, r.text
            key = r.json()["key"]
            assert key.startswith(f"u/{user_id}/avatar/") and r.json()["url"]
            for bad in (
                {"kind": "ingest", "content_type": "image/jpeg", "byte_size": 1},
                {"kind": "avatar", "content_type": "image/gif", "byte_size": 1},
                {"kind": "avatar", "content_type": "image/jpeg", "byte_size": 9_000_000},
            ):
                assert client.post("/blobs/upload-url", json=bad, headers=auth).status_code == 400

            # ── attach guards ────────────────────────────────────────
            foreign = "u/other-family/avatar/steal.jpg"
            fake.objects.add(foreign)
            r = client.post("/profile/kids/Nia/avatar", json={"key": foreign}, headers=auth)
            assert r.status_code == 403  # ownership boundary
            r = client.post("/profile/kids/Nia/avatar", json={"key": key}, headers=auth)
            assert r.status_code == 404  # nothing uploaded at key yet
            fake.objects.add(key)
            r = client.post("/profile/kids/Ghost/avatar", json={"key": key}, headers=auth)
            assert r.status_code == 404  # attach must not CREATE a kid
            r = client.post("/profile/kids/Nia/avatar", json={"key": key}, headers=auth)
            assert r.status_code == 200, r.text
            kid = r.json()["children"]["Nia"]
            assert kid["avatar_key"] == key
            assert kid["avatar_url"].startswith("https://stub.example/get_object/")

            # ── avatar_key is NOT PATCHable (the whitelist subtraction) ──
            r = client.patch("/profile/kids/Nia",
                             json={"avatar_key": foreign, "temperament": "sunny"},
                             headers=auth)
            assert r.json()["children"]["Nia"]["avatar_key"] == key  # unchanged
            r = client.patch("/profile", json={"avatar_key": foreign, "name": "P"}, headers=auth)
            assert r.json()["parent"].get("avatar_key") is None

            # ── replacing deletes the old object ─────────────────────
            r2 = client.post("/blobs/upload-url", json={
                "kind": "avatar", "content_type": "image/jpeg", "byte_size": 1000
            }, headers=auth)
            key2 = r2.json()["key"]
            fake.objects.add(key2)
            client.post("/profile/kids/Nia/avatar", json={"key": key2}, headers=auth)
            assert key in fake.deleted

            # ── parent avatar ────────────────────────────────────────
            r3 = client.post("/blobs/upload-url", json={
                "kind": "avatar", "content_type": "image/jpeg", "byte_size": 500
            }, headers=auth)
            pkey = r3.json()["key"]
            fake.objects.add(pkey)
            r = client.post("/profile/avatar", json={"key": pkey}, headers=auth)
            assert r.json()["parent"]["avatar_key"] == pkey

            # ── kid delete removes the kid's object ──────────────────
            client.delete("/profile/kids/Nia", headers=auth)
            assert key2 in fake.deleted

            # ── family delete sweeps the whole prefix ────────────────
            r = client.delete(f"/family/{user_id}", headers=auth)
            assert r.status_code == 200
            assert r.json()["deleted"].get("blobs", 0) >= 1
            assert not any(k.startswith(f"u/{user_id}/") for k in fake.objects)
            assert foreign in fake.objects  # other families untouched
    finally:
        _reconnect_shared_storage(server)


def test_upload_url_503_when_unconfigured(monkeypatch):
    from fastapi.testclient import TestClient
    import app.server as server

    for var in ("BLOB_BUCKET", "BLOB_ACCESS_KEY_ID", "BLOB_SECRET_ACCESS_KEY", "BLOB_ENDPOINT"):
        monkeypatch.delenv(var, raising=False)
    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            tok = client.post("/auth/issue-token", json={"user_id": "blob-noop-user"}).json()["token"]
            r = client.post("/blobs/upload-url", json={
                "kind": "avatar", "content_type": "image/jpeg", "byte_size": 1,
            }, headers={"Authorization": f"Bearer {tok}"})
            assert r.status_code == 503
    finally:
        _reconnect_shared_storage(server)
