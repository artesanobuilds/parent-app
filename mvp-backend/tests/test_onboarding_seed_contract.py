"""Onboarding seed + profile-edit cross-surface contract (2026-06-28).

These tests lock the iOS↔backend wire contract so contract drift breaks the
build rather than silently shipping a broken onboarding:

  • test_seed_persists_parent_and_kids_ios_payload — POST /profile/seed with the
    EXACT JSON shape SwayApp.swift sends. Pins the type-coercion contract that
    must hold across the surfaces: kid `age` arrives as a STRING and is coerced
    to a float; `adults_in_household` is an int; `household` maps to
    `household_structure`. Also that the seed requires auth.
  • test_saving_basics_does_not_wipe_learned_fields — regression for the "save
    Basics blanks the learned data" smell: a Basics-only kid save (name /
    pronouns / grade_band / age) must NOT clear list fields the coach has
    learned (interests, challenges), because the backend only touches keys
    present in the payload.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server,
mirroring tests/test_profile_edit.py — including the _reconnect_shared_storage
teardown so storage isolation survives between modules.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "seed_contract.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def test_seed_persists_parent_and_kids_ios_payload():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            user_id = "seed-contract-ios-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # The EXACT payload shape the iOS app posts from SwayApp.swift.
            payload = {
                "user_id": user_id,
                "parent_name": "Greg",
                "kids": [
                    {"name": "Lily", "age": "12", "temperament": "", "pronouns": "", "grade_band": ""},
                    {"name": "Ben", "age": "5", "temperament": "", "pronouns": "", "grade_band": ""},
                ],
                "household": "Single parent",
                "postal_code": "98333",
                "adults_in_household": 2,
            }

            # ── seed requires auth ────────────────────────────────────
            assert client.post("/profile/seed", json=payload).status_code == 401

            # ── seed with the iOS payload ─────────────────────────────
            r = client.post("/profile/seed", json=payload, headers=auth)
            assert r.status_code == 200, r.text

            def _assert_family(fam):
                parent = fam["parent"]
                assert parent["name"] == "Greg"
                assert parent["postal_code"] == "98333"
                # `household` maps to `household_structure`.
                assert parent["household_structure"] == "Single parent"
                # int, not string.
                assert parent["adults_in_household"] == 2
                assert isinstance(parent["adults_in_household"], int)

                children = fam["children"]
                assert "Lily" in children and "Ben" in children
                # Kid `age` arrives as a STRING and is coerced to a float.
                assert children["Lily"]["age"] == 12.0
                assert isinstance(children["Lily"]["age"], float)
                assert children["Ben"]["age"] == 5.0
                assert isinstance(children["Ben"]["age"], float)

            # The seed response IS the family profile…
            _assert_family(r.json())
            # …and a follow-up GET confirms it persisted.
            _assert_family(client.get("/profile", headers=auth).json())
    finally:
        _reconnect_shared_storage(server)


def test_saving_basics_does_not_wipe_learned_fields():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            user_id = "seed-contract-basics-user"
            tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            kid = "Lily"

            # ── create the kid + record what the coach "learned" ─────
            r = client.patch(
                f"/profile/kids/{kid}",
                json={"age": "7", "interests": ["art", "soccer"], "challenges": ["bedtime"]},
                headers=auth,
            )
            assert r.status_code == 200, r.text
            learned = r.json()["children"][kid]
            assert learned["interests"] == ["art", "soccer"]
            assert learned["challenges"] == ["bedtime"]

            # ── simulate the iOS Basics save: only name/pronouns/grade_band/age.
            # It says nothing about interests/challenges, so they must survive.
            r = client.patch(
                f"/profile/kids/{kid}",
                json={"name": kid, "pronouns": "", "grade_band": "elementary", "age": 7},
                headers=auth,
            )
            assert r.status_code == 200, r.text

            # ── learned fields STILL intact ───────────────────────────
            got = client.get("/profile", headers=auth).json()["children"][kid]
            assert got["grade_band"] == "elementary"
            assert got["age"] == 7.0
            assert got["interests"] == ["art", "soccer"], (
                "Basics-only save wiped learned `interests` — backend must only "
                "touch keys present in the payload"
            )
            assert got["challenges"] == ["bedtime"], (
                "Basics-only save wiped learned `challenges`"
            )
    finally:
        _reconnect_shared_storage(server)


def test_secondary_language_is_actually_stored():
    """The iOS seed has posted `secondary_language` since the Phase-3 Figma pass,
    but `ParentProfile` had no such field — and `_apply_update` skips any key the
    dataclass lacks (a `hasattr` guard), so every bilingual household's second
    language was silently DISCARDED on write.

    Found on 2026-08-08 while removing the language rows from the onboarding
    funnel to match the design. The decision there was "match the screens, keep
    the data" — which is only honest if the field is stored at all. It wasn't.

    This test exists because the failure mode is invisible: the client sends it,
    the server 200s, and nothing ever reads it back.
    """
    from app.profiling import ParentProfile

    parent = ParentProfile()
    parent.apply_update({"primary_language": "es", "secondary_language": "en"})
    assert parent.primary_language == "es"
    assert parent.secondary_language == "en", (
        "secondary_language was dropped — _apply_update ignores keys that aren't "
        "dataclass fields, so adding it to the wire payload alone does nothing"
    )
    # …and it must survive serialization, or the profile GET and the coach's
    # context still never see it.
    from dataclasses import asdict

    assert asdict(parent).get("secondary_language") == "en", (
        "stored on the object but absent from the serialized profile"
    )


def test_the_kid_editor_rows_store_under_their_own_names():
    """The design's kid editor asks five things: Likes · Dislikes · Challenges ·
    Excels at · Goals for {name}.

    `dislikes` and a per-kid `goals` did not exist on `ChildProfile`, so the iOS
    rows borrowed `triggers` and `motivators` — the label and the storage
    disagreed, and any client that sent the honest key would have been silently
    dropped by the whitelist derived from this dataclass. Both are real fields
    now; this locks them so the mapping can't quietly regress to a synonym.
    """
    from dataclasses import asdict

    from app.profiling import ChildProfile

    kid = ChildProfile(name="Lily")
    kid.apply_update({
        "interests": ["dinosaurs"],
        "dislikes": ["loud noises"],
        "challenges": ["bathtime"],
        "strengths": ["math"],
        "goals": ["more independence"],
    })
    stored = asdict(kid)
    for key, expected in (
        ("interests", ["dinosaurs"]),
        ("dislikes", ["loud noises"]),
        ("challenges", ["bathtime"]),
        ("strengths", ["math"]),
        ("goals", ["more independence"]),
    ):
        assert stored.get(key) == expected, (
            f"{key} did not round-trip — the kid editor's '{key}' row would look "
            f"saved and not be"
        )
    # `triggers` / `motivators` keep their own meaning and must NOT be collateral.
    assert stored["triggers"] == []
    assert stored["motivators"] == []
