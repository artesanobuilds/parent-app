"""Vertical registry invariants + the GET /cos/verticals doors endpoint
(Phase 1 of the vertical expansion — plan `one-agent-five-doors`).

The registry is data-only, so these tests are the behavioral lock: canonical
keys, frozen profiles, camp wording rendering EXACTLY the strings lifecycle
seeds (locked separately by test_lifecycle/test_activity_type), degradation of
unregistered types to camp, and — mirroring the plan's docs-freshness test —
every registered vertical must have an nl-harness flow spec.

The doors endpoint is the ONE place flags touch verticals; it must fail open
to the default-enabled doors and never 500.
"""
from __future__ import annotations

import dataclasses
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault(
    "MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "verticals_registry.duckdb")
)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app.cos import verticals  # noqa: E402

REPO_ROOT = BACKEND_ROOT.parent
HARNESS_SPECS = REPO_ROOT / "tests" / "nl-harness" / "specs"

_DATE_MODELS = {"week_block", "recurring_weekly", "single_date", "date_range", "none"}


# --------------------------------------------------------------------------- #
# Registry invariants
# --------------------------------------------------------------------------- #


def test_registry_keys_are_canonical():
    for key, profile in verticals.REGISTRY.items():
        assert key in verticals.ACTIVITY_TYPES
        assert profile.key == key
        assert profile.date_model in _DATE_MODELS


def test_phase1_profiles_registered():
    # Registered phase-by-phase: camp (V1) + outing (V3, built) are live today.
    # Later phases ADD keys here; this must never assert an exact set.
    assert verticals.CAMP in verticals.REGISTRY
    assert verticals.OUTING in verticals.REGISTRY
    assert verticals.DEFAULT_ACTIVITY_TYPE in verticals.REGISTRY


def test_profiles_are_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        verticals.REGISTRY[verticals.CAMP].label = "hacked"  # type: ignore[misc]


def test_camp_wording_renders_locked_strings():
    # lifecycle.on_enter_watched reads these templates; the rendered strings are
    # the exact ones the pre-registry code seeded (and prod users have seen).
    w = verticals.REGISTRY[verticals.CAMP].todo_wording
    assert (
        w.payment_title.format(name="Robotics Camp", price="120")
        == "Pay $120 for Robotics Camp"
    )
    assert w.payment_detail == (
        "Added when you marked this registered — check it off once paid."
    )
    assert (
        w.confirm_title.format(name="Robotics Camp")
        == "Forward or paste Robotics Camp's confirmation email"
    )
    assert w.confirm_detail.startswith("Gmail isn't connected")


def test_all_wording_templates_render():
    for profile in verticals.REGISTRY.values():
        w = profile.todo_wording
        assert profile.label and profile.chip_label
        assert "{name}" in w.payment_title and "{price}" in w.payment_title
        w.payment_title.format(name="X", price="1")
        w.confirm_title.format(name="X")
        assert profile.research_focus.strip()
        assert profile.door.title and profile.door.starter_prompt


def test_get_profile_degrades_to_camp():
    camp = verticals.REGISTRY[verticals.CAMP]
    assert verticals.get_profile(None) is camp
    assert verticals.get_profile("") is camp
    assert verticals.get_profile("garbage") is camp
    # Canonical but not yet registered (school_event lands Phase 5, trip
    # Phase 6): degrade, don't crash.
    for pending in verticals.ACTIVITY_TYPES - set(verticals.REGISTRY):
        assert verticals.get_profile(pending) is camp
    assert verticals.get_profile("  OUTING ") is verticals.REGISTRY[verticals.OUTING]
    assert (
        verticals.get_profile(verticals.EXTRACURRICULAR)
        is verticals.REGISTRY[verticals.EXTRACURRICULAR]
    )


def test_camp_capabilities():
    camp = verticals.REGISTRY[verticals.CAMP]
    outing = verticals.REGISTRY[verticals.OUTING]
    assert camp.email_sync and camp.registration_watch and camp.provides_coverage
    assert not outing.email_sync and not outing.registration_watch
    assert not outing.provides_coverage


def test_every_registered_vertical_has_a_harness_spec():
    # Mirrors the plan's docs-freshness test: a vertical isn't "shipped" without
    # black-box flow coverage. The spec path is declared on the profile.
    for profile in verticals.REGISTRY.values():
        assert profile.harness_spec, f"{profile.key} declares no harness spec"
        spec = HARNESS_SPECS / profile.harness_spec
        assert spec.is_file(), f"{profile.key}: missing harness spec {spec}"


def test_default_doors_fail_open_set():
    keys = {p.key for p in verticals.default_doors()}
    # Phase 1: no registered vertical is flag-gated, so all doors are default.
    assert {verticals.CAMP, verticals.OUTING} <= keys


# --------------------------------------------------------------------------- #
# GET /cos/verticals — the doors endpoint
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def client():
    # TestClient context exit runs lifespan shutdown, which closes the shared
    # storage singleton — rebuild it before AND after so this module neither
    # inherits nor leaves behind a dead connection (test_auth_v2 idiom).
    from fastapi.testclient import TestClient
    from app.duckdb_storage import DuckDBStorage

    import app.server as server

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _auth(client, user_id: str) -> dict:
    resp = client.post("/auth/issue-token", json={"user_id": user_id})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def test_verticals_endpoint(client):
    # Auth required like every other /cos surface.
    assert client.get("/cos/verticals").status_code == 401

    auth = _auth(client, "verticals-endpoint-test-user")
    r = client.get("/cos/verticals", headers=auth)
    assert r.status_code == 200
    assert "max-age=300" in (r.headers.get("Cache-Control") or "")
    doors = {d["key"]: d for d in r.json()["verticals"]}
    assert verticals.CAMP in doors and verticals.OUTING in doors
    for d in doors.values():
        for field in ("label", "chip_label", "title", "subtitle", "starter_prompt"):
            assert d.get(field), f"door {d['key']} missing {field}"


def test_verticals_endpoint_flag_gating_and_fail_open(client, monkeypatch):
    import app.analytics.flags as flags

    gated = dataclasses.replace(
        verticals.REGISTRY[verticals.CAMP],
        key="extracurricular",
        label="Classes & sports",
        chip_label="Class",
        flag="vertical-v2-extracurriculars",
    )
    monkeypatch.setitem(verticals.REGISTRY, "extracurricular", gated)
    auth = _auth(client, "verticals-flag-test-user")

    # Flag OFF → gated door hidden, defaults present.
    monkeypatch.setattr(flags, "is_enabled", lambda *a, **k: False)
    keys = {d["key"] for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "extracurricular" not in keys and verticals.CAMP in keys

    # Flag ON → gated door appears.
    monkeypatch.setattr(flags, "is_enabled", lambda *a, **k: True)
    keys = {d["key"] for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "extracurricular" in keys

    # Flag eval BLOWS UP → fail open to the default (unflagged) doors, 200.
    def _boom(*a, **k):
        raise RuntimeError("flag service down")

    monkeypatch.setattr(flags, "is_enabled", _boom)
    r = client.get("/cos/verticals", headers=auth)
    assert r.status_code == 200
    keys = {d["key"] for d in r.json()["verticals"]}
    assert verticals.CAMP in keys and verticals.OUTING in keys
    assert "extracurricular" not in keys
