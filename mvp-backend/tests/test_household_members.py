"""Household members + Circle (beta-v1 Phase 1).

The invariants this pins:
  • Member CRUD is keyed by the stable id, never display_name — a rename does
    not move the row, and another family's member id is a 404 (not a 403,
    which would confirm the id exists).
  • Attributes are ROLE-SCOPED server-side: "Co-Parent goals" exists only on a
    co_parent, and sending it on any other role is rejected — not silently
    stored where nothing will ever render it.
  • Children are NOT members. Writes with role/kind "child" are refused and
    the kids are projected READ-ONLY into GET /household from their existing
    FamilyProfile store (the seam this phase deliberately did not move).
  • delete_family cascades to household_members, and clears the reciprocal
    links other families hold on the deleted account.
Circle-conversation scoping (the Circle is a MUTUAL authorization set, and a
one-sided link unlocks nothing) is pinned in tests/test_circle_conversations.py
— the 1:1 DM surface that used to be tested here is retired.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing
app.server; every TestClient block restores server.storage_backend in a
finally (a TestClient context exit closes the storage singleton).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "household.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


def _parent(client, user_id, name):
    tok = client.post("/auth/issue-token", json={"user_id": user_id}).json()["token"]
    auth = {"Authorization": f"Bearer {tok}"}
    client.patch("/profile", json={"name": name}, headers=auth)
    return auth


def _add(client, auth, **body):
    r = client.post("/household/members", json=body, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()["member"]


def test_member_crud_and_stable_id():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            auth = _parent(client, "hh-crud", "Miguel Alvarado")

            nanny = _add(client, auth, display_name="Ana Ruiz", role="nanny",
                         relation="Nanny", email="ana@example.com",
                         attributes={"likes": ["parks"], "excels_at": ["bedtime"]})
            assert nanny["kind"] == "adult"
            assert nanny["role"] == "nanny" and nanny["role_label"] == "Nanny"
            assert nanny["mvp_username"] == "mvpAna"        # issued locally
            assert nanny["attributes"]["likes"] == ["parks"]
            assert nanny["attributes"]["dislikes"] == []    # every allowed key present
            assert nanny["in_circle"] is False and nanny["linked"] is False
            member_id = nanny["id"]

            # a linked caregivers row was mirrored — the nanny is entered once
            assert nanny["caregiver_id"]
            caregivers = client.get("/cos/caregivers", headers=auth).json()["caregivers"]
            assert any(c["id"] == nanny["caregiver_id"] and c["name"] == "Ana Ruiz"
                       and c["role"] == "nanny" for c in caregivers)

            # duplicate names get distinct usernames (unique within household)
            second = _add(client, auth, display_name="Ana Sole", role="other")
            assert second["mvp_username"] == "mvpAna2"

            listed = client.get("/household/members", headers=auth).json()["members"]
            assert [m["id"] for m in listed] == [member_id, second["id"]]

            # ── rename: the ID is the key, so the row does not move ──
            r = client.patch(f"/household/members/{member_id}",
                             json={"display_name": "Ana R. Ruiz"}, headers=auth)
            assert r.status_code == 200, r.text
            renamed = r.json()["member"]
            assert renamed["id"] == member_id
            assert renamed["display_name"] == "Ana R. Ruiz"
            # untouched keys survive a partial save
            assert renamed["attributes"]["likes"] == ["parks"]
            assert renamed["mvp_username"] == "mvpAna"
            # the mirrored caregivers row follows the member
            caregivers = client.get("/cos/caregivers", headers=auth).json()["caregivers"]
            assert next(c for c in caregivers
                        if c["id"] == renamed["caregiver_id"])["name"] == "Ana R. Ruiz"

            # explicit null clears; omitted keys are untouched
            r = client.patch(f"/household/members/{member_id}",
                             json={"relation": None}, headers=auth)
            assert r.json()["member"]["relation"] is None
            assert r.json()["member"]["email"] == "ana@example.com"

            assert client.get(f"/household/members/{member_id}",
                              headers=auth).json()["member"]["id"] == member_id

            # ── delete cascades to the mirrored caregiver ────────────
            r = client.delete(f"/household/members/{member_id}", headers=auth)
            assert r.status_code == 200, r.text
            assert r.json()["deleted"]["household_members"] == 1
            assert r.json()["deleted"]["caregivers"] == 1
            assert client.get(f"/household/members/{member_id}",
                              headers=auth).status_code == 404
            caregivers = client.get("/cos/caregivers", headers=auth).json()["caregivers"]
            assert all(c["name"] != "Ana R. Ruiz" for c in caregivers)

            # ── auth boundary: another family sees a 404, not a 403 ──
            other = _parent(client, "hh-stranger", "Stranger")
            mine = _add(client, auth, display_name="Grandma Rose", role="grandparent")
            assert client.get(f"/household/members/{mine['id']}",
                              headers=other).status_code == 404
            assert client.patch(f"/household/members/{mine['id']}",
                                json={"display_name": "Hacked"},
                                headers=other).status_code == 404
            assert client.delete(f"/household/members/{mine['id']}",
                                 headers=other).status_code == 404
            assert client.get("/household/members").status_code == 401
            # a body user_id can never re-scope the write
            assert client.post("/household/members",
                               json={"user_id": "hh-crud", "display_name": "X"},
                               headers=other).status_code == 403
    finally:
        _reconnect_shared_storage(server)


def test_attributes_are_role_scoped():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            auth = _parent(client, "hh-roles", "Role Parent")

            # ── Co-Parent goals: ONLY on a co_parent ─────────────────
            co = _add(client, auth, display_name="Sarah", role="co_parent",
                      relation="Step Mom",
                      attributes={"co_parent_goals": ["one bedtime story rule"],
                                  "goals": ["consistent handoffs"]})
            assert co["attributes"]["co_parent_goals"] == ["one bedtime story rule"]
            assert "co_parent_goals" in {f["key"] for f in co["attribute_fields"]}
            assert next(f for f in co["attribute_fields"]
                        if f["key"] == "goals")["label"] == "Goals for Sarah"

            nanny = _add(client, auth, display_name="Ana", role="nanny")
            assert "co_parent_goals" not in nanny["attributes"]
            assert "co_parent_goals" not in {f["key"] for f in nanny["attribute_fields"]}

            # writing it on a non-co-parent is refused, not silently stored
            r = client.patch(f"/household/members/{nanny['id']}",
                             json={"attributes": {"co_parent_goals": ["nope"]}},
                             headers=auth)
            assert r.status_code == 400, r.text
            assert "co_parent_goals" in r.json()["detail"]
            assert client.post("/household/members",
                               json={"display_name": "Gran", "role": "grandparent",
                                     "attributes": {"co_parent_goals": ["nope"]}},
                               headers=auth).status_code == 400

            # demoting a co_parent drops the now-invalid key
            r = client.patch(f"/household/members/{co['id']}",
                             json={"role": "other"}, headers=auth)
            assert r.status_code == 200, r.text
            assert "co_parent_goals" not in r.json()["member"]["attributes"]
            assert r.json()["member"]["attributes"]["goals"] == ["consistent handoffs"]

            # unknown roles rejected; the catalog agrees with the enforcement
            assert client.post("/household/members",
                               json={"display_name": "Z", "role": "wizard"},
                               headers=auth).status_code == 400
            catalog = client.get("/household/roles").json()["roles"]
            by_key = {r["key"]: r for r in catalog}
            assert "co_parent_goals" in {a["key"] for a in by_key["co_parent"]["attributes"]}
            assert "co_parent_goals" not in {a["key"] for a in by_key["nanny"]["attributes"]}
    finally:
        _reconnect_shared_storage(server)


def test_children_stay_on_the_profile_path():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            auth = _parent(client, "hh-kids", "Kid Parent")
            client.post("/profile/seed", json={
                "user_id": "hh-kids", "parent_name": "Kid Parent",
                "kids": [{"name": "Ben", "age": "7"}],
            }, headers=auth)
            client.patch("/profile/kids/Ben", json={"interests": ["lego"]},
                         headers=auth)
            _add(client, auth, display_name="Ana", role="nanny")

            household = client.get("/household", headers=auth).json()
            assert household["counts"] == {"members": 1, "children": 1, "circle": 0}
            ben = household["children"][0]
            assert ben["id"] == "child:Ben" and ben["kind"] == "child"
            assert ben["editable"] is False
            assert ben["editable_via"] == "/profile/kids/Ben"
            assert ben["attributes"]["likes"] == ["lego"]

            # kids cannot be created through the member surface
            r = client.post("/household/members",
                            json={"display_name": "Ben", "role": "child"}, headers=auth)
            assert r.status_code == 400
            assert "/profile/kids" in r.json()["detail"]
            # nor by demoting an existing member into one
            ana = client.get("/household/members", headers=auth).json()["members"][0]
            assert client.patch(f"/household/members/{ana['id']}",
                                json={"role": "child"}, headers=auth).status_code == 400
    finally:
        _reconnect_shared_storage(server)


def test_delete_family_cascades_to_members_and_links():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            gone = _parent(client, "hh-gone", "Going Away")
            keeper = _parent(client, "hh-keeper", "Stays Put")

            _add(client, gone, display_name="Stays Put", role="co_parent",
                 member_user_id="hh-keeper")
            kept = _add(client, keeper, display_name="Going Away", role="co_parent",
                        member_user_id="hh-gone")
            _add(client, gone, display_name="Grandma", role="grandparent")

            r = client.delete("/family/hh-gone", headers=gone)
            assert r.status_code == 200, r.text
            deleted = r.json()["deleted"]
            assert deleted["household_members"] == 2
            # the peer KEEPS their row (their data about their person)…
            assert deleted["household_member_links_cleared"] == 1
            still = client.get("/household/members", headers=keeper).json()["members"]
            assert [m["id"] for m in still] == [kept["id"]]
            # …but the pointer at the deleted account is gone, so a re-issued
            # user_id can never inherit a stranger's Circle (or its threads)
            assert still[0]["member_user_id"] is None

            # the deleted family's rows really are gone from storage
            assert server.storage_backend.list_household_members("hh-gone") == []
    finally:
        _reconnect_shared_storage(server)
