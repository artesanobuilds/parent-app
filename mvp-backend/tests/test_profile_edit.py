"""Profile-editor write path (2026-06-28).

Two layers:
  • Pure unit — ParentProfile/ChildProfile.apply_update(replace_lists=True) SETS
    list fields (so the editor can edit/remove items), while the default still
    MERGES (how the coaching/onboarding agents accumulate facts).
  • HTTP — PATCH /profile and PATCH /profile/kids/{name} round-trip: edit rich
    parent fields, ADD a kid, remove a list item (persists), unknown keys dropped,
    and the auth/ownership guard.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server,
mirroring tests/test_cos_api.py.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "profile_edit.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app.profiling import ParentProfile, ChildProfile  # noqa: E402


# --------------------------------------------------------------------------- #
# Pure unit: merge vs replace
# --------------------------------------------------------------------------- #


def test_default_merges_lists():
    p = ParentProfile()
    p.apply_update({"stressors": ["mornings"]})
    p.apply_update({"stressors": ["bedtime"]})
    assert p.stressors == ["mornings", "bedtime"]  # accumulated, deduped


def test_replace_sets_lists_and_allows_removal():
    p = ParentProfile(stressors=["mornings", "bedtime", "sibling fights"])
    # Editor removed "bedtime" → sends the remaining two as the full list.
    p.apply_update({"stressors": ["mornings", "sibling fights"]}, replace_lists=True)
    assert p.stressors == ["mornings", "sibling fights"]
    # Clearing entirely sticks.
    p.apply_update({"stressors": []}, replace_lists=True)
    assert p.stressors == []


def test_replace_coerces_scalar_to_list():
    c = ChildProfile()
    c.apply_update({"interests": "soccer"}, replace_lists=True)
    assert c.interests == ["soccer"]


def test_unknown_keys_ignored():
    p = ParentProfile()
    p.apply_update({"not_a_field": "x", "name": "Pat"}, replace_lists=True)
    assert not hasattr(p, "not_a_field")
    assert p.name == "Pat"


# --------------------------------------------------------------------------- #
# HTTP round-trip
# --------------------------------------------------------------------------- #


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def test_patch_profile_and_add_kid_round_trip():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            user_id = "profile-edit-http-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # ── unauth + cross-user guards ───────────────────────────
            assert client.patch("/profile", json={"name": "X"}).status_code == 401
            cross = client.patch(
                "/profile", json={"user_id": "someone-else", "name": "X"}, headers=auth
            )
            assert cross.status_code == 403

            # ── edit rich parent fields (no write path before today) ──
            r = client.patch(
                "/profile",
                json={
                    "name": "Pat",
                    "parenting_style": "connection-first",
                    "work_hours": "9-5 some evenings",
                    "adults_in_household": "2",          # coerced to int
                    "goals": ["more patience", "fewer power struggles"],
                    "bogus_field": "ignored",            # dropped
                },
                headers=auth,
            )
            assert r.status_code == 200, r.text
            parent = r.json()["parent"]
            assert parent["parenting_style"] == "connection-first"
            assert parent["work_hours"] == "9-5 some evenings"
            assert parent["adults_in_household"] == 2
            assert parent["goals"] == ["more patience", "fewer power struggles"]
            assert "bogus_field" not in parent

            # ── remove a list item → persists (replace semantics) ─────
            r = client.patch(
                "/profile", json={"goals": ["more patience"]}, headers=auth
            )
            assert r.json()["parent"]["goals"] == ["more patience"]

            # ── add a kid via PATCH /profile/kids/{name} ──────────────
            r = client.patch(
                "/profile/kids/Ceiba",
                json={"age": "7", "grade_band": "elementary", "interests": ["art", "soccer"]},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            fam = r.json()
            assert "Ceiba" in fam["children"]
            kid = fam["children"]["Ceiba"]
            assert kid["age"] == 7.0           # coerced to float
            assert kid["interests"] == ["art", "soccer"]

            # ── GET reflects everything ───────────────────────────────
            got = client.get("/profile", headers=auth).json()
            assert got["parent"]["goals"] == ["more patience"]
            assert got["children"]["Ceiba"]["grade_band"] == "elementary"

            # ── remove a kid via DELETE /profile/kids/{name} ──────────
            assert client.delete("/profile/kids/Ceiba").status_code == 401  # unauth
            r = client.delete("/profile/kids/Ceiba", headers=auth)
            assert r.status_code == 200, r.text
            assert "Ceiba" not in r.json()["children"]
            # idempotent: deleting a non-existent kid is a no-op 200
            assert client.delete("/profile/kids/Nope", headers=auth).status_code == 200
            assert "Ceiba" not in client.get("/profile", headers=auth).json()["children"]
    finally:
        _reconnect_shared_storage(server)
