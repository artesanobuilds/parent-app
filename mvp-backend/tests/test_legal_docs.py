"""Versioned legal documents (privacy policy / terms) + acceptance (2026-07-18).

Covers the invariants that make the CMS-versioned model safe:
  • Bootstrap seeds repo markdown as published v1 — idempotent, and a slug with
    a published row is NEVER re-seeded (no v1 resurrection beside a CMS v2).
  • Public reads; draft→publish atomicity (prior versions immutable, duplicate
    version 409); admin gate; stale-version accept echo 409.
  • /legal/status: requires_reacceptance=false publishes don't nag; =true do.
  • delete_family removes legal_acceptances but legal_documents survive.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server,
mirroring tests/test_profile_edit.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "legal_docs.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

# ADMIN_TOKEN is read at CALL time by require_admin_token and may already be
# set by the local env/.env — tests pin it per-test via monkeypatch (the
# test_admin_session idiom), never module-level setdefault.
ADMIN = {"X-Admin-Token": "test-admin-token"}


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #


def test_seed_and_idempotency():
    import app.server as server

    _reconnect_shared_storage(server)
    docs = server.storage_backend.get_current_legal_docs()
    slugs = {d["slug"] for d in docs}
    assert {"privacy-policy", "terms"} <= slugs
    for d in docs:
        assert d["published_by"] == "seed"
        assert d["version"]
        assert d["body_md"]

    # Re-init: seed must not duplicate (slug-presence check, not row-count).
    _reconnect_shared_storage(server)
    assert len(server.storage_backend.list_legal_versions("terms")) == 1


def test_seed_never_resurrects_beside_cms_publish():
    import app.server as server

    _reconnect_shared_storage(server)
    server.storage_backend.upsert_legal_draft("terms", title="Terms", body_md="v2 body")
    server.storage_backend.publish_legal_draft(
        "terms", version="2.0-test-res", effective_date=None, requires_reacceptance=False
    )
    # Re-init runs the seeder again — the CMS-published 2.0 must stay current
    # and v1 must NOT come back as a duplicate row.
    before = len(server.storage_backend.list_legal_versions("terms"))
    _reconnect_shared_storage(server)
    after = server.storage_backend.list_legal_versions("terms")
    assert len(after) == before
    assert server.storage_backend.get_legal_doc("terms")["version"] == "2.0-test-res"


# --------------------------------------------------------------------------- #
# HTTP round-trip
# --------------------------------------------------------------------------- #


def test_legal_http_round_trip(monkeypatch):
    from fastapi.testclient import TestClient
    import app.server as server

    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)

            # ── public reads ─────────────────────────────────────────
            r = client.get("/content/legal")
            assert r.status_code == 200
            assert {d["slug"] for d in r.json()["documents"]} >= {"privacy-policy", "terms"}
            r = client.get("/content/legal/privacy-policy")
            assert r.status_code == 200 and r.json()["body_md"]
            assert client.get("/content/legal/nope").status_code == 404

            # ── auth gates ───────────────────────────────────────────
            assert client.get("/legal/status").status_code == 401
            assert client.get("/cms/legal").status_code == 401
            assert client.put(
                "/cms/legal/terms/draft", json={"title": "x", "body_md": "y"}
            ).status_code == 401

            user_id = "legal-http-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # ── status → accept → status ─────────────────────────────
            s = client.get("/legal/status", headers=auth).json()
            assert s["accepted_all"] is False
            versions = {d["slug"]: d["required_version"] for d in s["documents"]}
            # stale echo 409s and records nothing
            r = client.post(
                "/legal/accept",
                json={"versions": {"terms": "0.0-stale"}}, headers=auth,
            )
            assert r.status_code == 409 and "required" in r.json()
            # unknown slug 400s
            assert client.post(
                "/legal/accept", json={"versions": {"nope": "1.0"}}, headers=auth
            ).status_code == 400
            # real accept writes one row per doc
            r = client.post(
                "/legal/accept", json={"versions": versions, "platform": "ios"},
                headers=auth,
            )
            assert r.status_code == 200
            assert len(r.json()["accepted"]) == len(versions)
            assert client.get("/legal/status", headers=auth).json()["accepted_all"] is True

            # ── draft → publish (admin) ──────────────────────────────
            assert client.get("/cms/legal/terms/draft", headers=ADMIN).status_code in (200, 404)
            r = client.put(
                "/cms/legal/terms/draft",
                json={"title": "Terms of Service", "body_md": "updated body"},
                headers=ADMIN,
            )
            assert r.status_code == 200 and r.json()["published_at"] is None
            prior_current = client.get("/content/legal/terms").json()
            r = client.post(
                "/cms/legal/terms/publish",
                json={"version": "9.9-http", "requires_reacceptance": True,
                      "effective_date": "2026-08-01"},
                headers=ADMIN,
            )
            assert r.status_code == 200
            now_current = r.json()
            assert now_current["version"] == "9.9-http" and now_current["is_current"]

            # prior version row unchanged (immutable), just no longer current
            history = client.get("/cms/legal/terms/versions", headers=ADMIN).json()["versions"]
            prior_row = next(v for v in history if v["version"] == prior_current["version"])
            assert prior_row["body_md"] == prior_current["body_md"]
            assert prior_row["is_current"] is False

            # duplicate version 409; publish with no draft 409
            client.put("/cms/legal/terms/draft",
                       json={"title": "t", "body_md": "b"}, headers=ADMIN)
            assert client.post(
                "/cms/legal/terms/publish", json={"version": "9.9-http"}, headers=ADMIN
            ).status_code == 409
            client.delete("/cms/legal/terms/draft", headers=ADMIN)
            assert client.post(
                "/cms/legal/terms/publish", json={"version": "10.0"}, headers=ADMIN
            ).status_code == 409

            # unknown slug rejected on writes
            assert client.put(
                "/cms/legal/hacks/draft", json={"title": "x", "body_md": "y"},
                headers=ADMIN,
            ).status_code == 400

            # ── requires_reacceptance semantics ──────────────────────
            # 9.9-http required re-acceptance → terms (and only terms) nags.
            s = client.get("/legal/status", headers=auth).json()
            assert s["needs"] == ["terms"]
            # a typo-fix publish (requires_reacceptance=False) must NOT nag
            client.put("/cms/legal/terms/draft",
                       json={"title": "Terms of Service", "body_md": "typo fixed"},
                       headers=ADMIN)
            client.post("/cms/legal/terms/publish",
                        json={"version": "9.9.1-http", "requires_reacceptance": False},
                        headers=ADMIN)
            # accept 9.9-http first so the user has SOME acceptance for terms
            s = client.get("/legal/status", headers=auth).json()
            vs = {d["slug"]: d["required_version"] for d in s["documents"] if not d["accepted"]}
            client.post("/legal/accept", json={"versions": vs}, headers=auth)
            client.put("/cms/legal/terms/draft",
                       json={"title": "Terms of Service", "body_md": "another typo"},
                       headers=ADMIN)
            client.post("/cms/legal/terms/publish",
                        json={"version": "9.9.2-http", "requires_reacceptance": False},
                        headers=ADMIN)
            s = client.get("/legal/status", headers=auth).json()
            assert s["accepted_all"] is True  # old acceptance still satisfies

            # ── delete_family boundary ───────────────────────────────
            r = client.delete(f"/family/{user_id}", headers=auth)
            assert r.status_code == 200
            assert server.storage_backend.latest_legal_acceptance(user_id, "terms") is None
            assert server.storage_backend.get_legal_doc("terms") is not None
    finally:
        _reconnect_shared_storage(server)


# --------------------------------------------------------------------------- #
# Repo seed files
# --------------------------------------------------------------------------- #


def test_repo_seed_files_exist_with_frontmatter():
    """Fresh deploys depend on these files — lock their presence + frontmatter."""
    from app.duckdb_storage import _parse_legal_frontmatter

    legal_dir = BACKEND_ROOT / "legal"
    for slug in ("privacy-policy", "terms"):
        path = legal_dir / f"{slug}.md"
        assert path.is_file(), f"missing seed file {path}"
        meta, body = _parse_legal_frontmatter(path.read_text(encoding="utf-8"))
        assert meta.get("title"), f"{slug}: frontmatter needs title"
        assert meta.get("version"), f"{slug}: frontmatter needs version"
        assert meta.get("effective_date"), f"{slug}: frontmatter needs effective_date"
        assert body.strip(), f"{slug}: empty body"
