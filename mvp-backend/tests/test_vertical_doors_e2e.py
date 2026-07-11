"""Phase 3 hermetic E2E: the V2 door end-to-end over real HTTP (TestClient) —
no LLM, no network.

Flow under test: the extracurricular door appears when its flag is on (via the
FLAG_* env kill-switch override, the same mechanism ops would use) → the
parent tracks a weekly class with an rrule (as the agent/UI would after a
discovery or a "I signed her up" turn) → the board renders a typed card
(activity_type=extracurricular) with the server-rendered `when` line, and the
derived recurring row exists for conflict detection. Also locks the 422 on an
unsupported rrule at the HTTP edge.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault(
    "MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "vertical_doors_e2e.duckdb")
)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

USER = "vertical-doors-e2e-user"


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from app.duckdb_storage import DuckDBStorage

    import app.server as server

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture()
def auth(client):
    resp = client.post("/auth/issue-token", json={"user_id": USER})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def test_v2_door_to_typed_board_card(client, auth, monkeypatch):
    # 1) Flag explicitly OFF: the extracurricular door hides, defaults show.
    # (Explicit setenv, not delenv-and-assume: the dev .env sets the FLAG_*
    # override to 1, and load_dotenv pulls it into the test process.)
    monkeypatch.setenv("FLAG_VERTICAL_V2_EXTRACURRICULARS", "0")
    doors = {d["key"] for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "camp" in doors and "outing" in doors
    assert "extracurricular" not in doors

    # 2) Flag ON via the env kill-switch override (ops mechanism, no PostHog).
    monkeypatch.setenv("FLAG_VERTICAL_V2_EXTRACURRICULARS", "1")
    doors = {d["key"]: d for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "extracurricular" in doors
    assert doors["extracurricular"]["starter_prompt"]

    # 3) Track a weekly class the way the UI/agent would after the door.
    resp = client.post(
        "/cos/activities/track",
        headers=auth,
        json={
            "user_id": USER,
            "name": "Fall Soccer",
            "kid_name": "Mar",
            "activity_type": "extracurricular",
            "status": "planned",
            "rrule": "FREQ=WEEKLY;BYDAY=TU",
            "recur_time": "16:00",
            "recur_duration_min": 60,
            "start_date": "2026-09-01",
            "end_date": "2026-12-15",
            "price_amount": 200.0,
        },
    )
    assert resp.status_code == 200, resp.text
    activity_id = resp.json()["id"]

    # 4) Board: typed card + server-rendered when line.
    board = client.get("/cos/plan/board", headers=auth).json()
    cards = [a for s in board["stages"] for a in s["activities"] if a["id"] == activity_id]
    assert cards, "tracked class missing from board"
    card = cards[0]
    assert card["activity_type"] == "extracurricular"
    assert card["when"] == "Tuesdays 4:00 PM through Dec 15"

    # 5) The derived recurring row exists (conflict detection input).
    recurring = client.get("/cos/recurring", headers=auth).json()["recurring"]
    derived = [r for r in recurring if r.get("activity_id") == activity_id]
    assert len(derived) == 1 and derived[0]["weekday"] == 1

    # 6) Unsupported rrule is a 422 at the HTTP edge, not a stored surprise.
    bad = client.post(
        "/cos/activities/track",
        headers=auth,
        json={"user_id": USER, "name": "Twice-a-week", "rrule": "FREQ=WEEKLY;BYDAY=TU,TH"},
    )
    assert bad.status_code == 422

    # Cleanup for repeatability within the shared module DB.
    client.delete(f"/cos/activities/{activity_id}", headers=auth)


def test_v5_trip_door_to_range_card_and_prep_todos(client, auth, monkeypatch):
    # 1) Door gated by its flag (env kill-switch, same mechanism as V2).
    monkeypatch.setenv("FLAG_VERTICAL_V5_TRIPS", "0")
    doors = {d["key"] for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "trip" not in doors
    monkeypatch.setenv("FLAG_VERTICAL_V5_TRIPS", "1")
    doors = {d["key"]: d for d in client.get("/cos/verticals", headers=auth).json()["verticals"]}
    assert "trip" in doors and doors["trip"]["starter_prompt"]

    # 2) Track a booked trip with its REAL range, as the agent/UI would.
    resp = client.post(
        "/cos/activities/track",
        headers=auth,
        json={
            "user_id": USER,
            "name": "Tahoe with the kids",
            "activity_type": "trip",
            "status": "signed_up",
            "start_date": "2026-06-14",
            "end_date": "2026-06-18",
            "price_amount": 900.0,
        },
    )
    assert resp.status_code == 200, resp.text
    activity_id = resp.json()["id"]

    # 3) Board: typed card + the range when line (never "Week of ...").
    board = client.get("/cos/plan/board", headers=auth).json()
    cards = [a for s in board["stages"] for a in s["activities"] if a["id"] == activity_id]
    assert cards, "tracked trip missing from board"
    assert cards[0]["activity_type"] == "trip"
    assert cards[0]["when"] == "Jun 14 – Jun 18"

    # 4) Created straight into signed_up → the enter-WATCHED hook seeded the
    # trip prep extras alongside the payment to-do.
    todos = client.get("/cos/todos", headers=auth).json()["todos"]
    mine = [t for t in todos if t.get("activity_id") == activity_id]
    titles = " | ".join(t["title"] for t in mine)
    assert "packing list" in titles.lower()
    assert "consent" in titles.lower()
    assert any(t["kind"] == "form" for t in mine)

    # Cleanup for repeatability within the shared module DB.
    client.delete(f"/cos/activities/{activity_id}", headers=auth)
