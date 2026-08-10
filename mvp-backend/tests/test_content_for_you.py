"""Ranked "For you" library feed — GET /content/for-you (2026-08-07).

Home's `FOR YOU → See all` is NOT the categorical browse: it is the whole
library, stack-ranked against the family profile. The invariants this locks:

  • Ranking works — articles matching the parent's stressors/goals/household
    and the kids' challenges/interests/age band sort ABOVE ones that don't,
    even when the non-matching article would win on plain library order (id).
  • The feed is NEVER empty. `score_articles_by_words` has `HAVING score > 0`,
    so a brand-new family with an empty profile scores zero rows; the endpoint
    must top the list up from the unranked library. A blank Home on first open
    is the exact failure the redesign exists to fix.
  • Item shape matches /content/articles exactly (iOS Codable is strict — one
    divergent key/type empties the whole list), and numeric envelope fields
    are ints, not DuckDB DOUBLEs.
  • It requires auth (it reads the caller's profile).

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server,
mirroring tests/test_onboarding_seed_contract.py — including the
_reconnect_shared_storage teardown so storage isolation survives between
modules (a TestClient context exit closes the storage singleton).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "for_you.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

# /content/articles' payload keys — the shape iOS decodes. /content/for-you
# items must be identical.
ARTICLE_KEYS = {
    "id", "category", "title", "subtitle", "emoji", "author",
    # `kicker` + `age_range` added in migration v23 — they feed the reader's
    # eyebrow ("WE TRIED IT · Ages 3–7 · 4 min"). They belong in BOTH payloads:
    # For-You cards show the same eyebrow, and iOS decodes both endpoints with
    # one model, so a key present in only one silently nils the other.
    "read_time", "kicker", "age_range", "summary", "tags",
}


def _reconnect_shared_storage(server):
    from app.duckdb_storage import DuckDBStorage
    from app import content as content_service

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    # app.content holds its OWN reference (bound at import via content.init),
    # so the standard reconnect alone leaves it pointing at the connection the
    # TestClient exit just closed — every later /content/* read would raise
    # "Connection already closed".
    content_service.init(server.storage_backend)


def _seed_library(storage):
    """Two decoy articles that sort FIRST by id, and two that only a profiled
    family should surface. Ids are prefixed so ordering is deterministic
    regardless of what other test modules left in the shared library.

    Idempotent — the modules share one DuckDB for the whole session (every test
    file MVP_DUCKDB_PATH-setdefaults, so the first one wins)."""
    if storage.get_article("art-fy-0-decoy-a") is not None:
        return
    storage.create_article({
        "id": "art-fy-0-decoy-a", "category": "cat-fy", "title": "Quarterly Budget Basics",
        "subtitle": "Spreadsheets for the household", "emoji": "", "author": "MVP Editorial",
        "read_time": "4 min", "summary": "", "tags": ["money"], "content": "body",
    })
    storage.create_article({
        "id": "art-fy-1-decoy-b", "category": "cat-fy", "title": "Choosing A Family Car",
        "subtitle": "Seats, trunks, and warranties", "emoji": "", "author": "MVP Editorial",
        "read_time": "6 min", "summary": "", "tags": ["logistics"], "content": "body",
    })
    storage.create_article({
        "id": "art-fy-8-match-a", "category": "cat-fy", "title": "Ending Bedtime Standoffs",
        "subtitle": "A calmer routine for a preschool kid", "emoji": "", "author": "MVP Editorial",
        "read_time": "5 min", "summary": "", "tags": ["bedtime", "preschool"], "content": "body",
    })
    storage.create_article({
        "id": "art-fy-9-match-b", "category": "cat-fy", "title": "When Tantrums Escalate",
        "subtitle": "Co-parenting through the meltdown", "emoji": "", "author": "MVP Editorial",
        "read_time": "7 min", "summary": "", "tags": ["tantrums"], "content": "body",
    })


def test_for_you_ranks_the_library_by_family_profile():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _seed_library(server.storage_backend)

            uid = "for-you-ranked-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            # ── auth is required ─────────────────────────────────────
            assert client.get("/content/for-you").status_code == 401

            # ── a rich profile: parent stressors/goals/household + a kid ──
            r = client.patch("/profile", json={
                "stressors": ["bedtime standoffs"],
                "goals": ["fewer tantrums"],
                "household_structure": "co-parenting",
            }, headers=auth)
            assert r.status_code == 200, r.text
            r = client.patch("/profile/kids/Ben", json={
                "age": "5", "challenges": ["meltdowns"], "interests": ["dinosaurs"],
            }, headers=auth)
            assert r.status_code == 200, r.text

            r = client.get("/content/for-you?limit=100", headers=auth)
            assert r.status_code == 200, r.text
            feed = r.json()

            assert feed["ranked"] is True
            # The word bag really was built from the profile (age 5 → "preschool").
            assert {"bedtime", "standoffs", "tantrums", "meltdowns", "dinosaurs",
                    "preschool"} <= set(feed["signals"])

            ids = [a["id"] for a in feed["items"]]
            for wanted in ("art-fy-8-match-a", "art-fy-9-match-b",
                           "art-fy-0-decoy-a", "art-fy-1-decoy-b"):
                assert wanted in ids, f"{wanted} missing — the feed is the WHOLE library"

            # Profile-relevant items outrank the decoys, which would otherwise
            # come first (the unranked library is ordered by id).
            assert ids.index("art-fy-8-match-a") < ids.index("art-fy-0-decoy-a")
            assert ids.index("art-fy-9-match-b") < ids.index("art-fy-0-decoy-a")
            assert ids.index("art-fy-8-match-a") < ids.index("art-fy-1-decoy-b")
            assert ids.index("art-fy-9-match-b") < ids.index("art-fy-1-decoy-b")

            # ── item shape == /content/articles, exactly ─────────────
            listed = client.get("/content/articles?limit=500").json()
            by_id = {a["id"]: a for a in listed}
            for item in feed["items"]:
                assert set(item.keys()) == ARTICLE_KEYS, (
                    "for-you items must decode with the SAME Codable model as "
                    "/content/articles"
                )
                assert item == by_id[item["id"]]
                assert isinstance(item["tags"], list)
                assert all(isinstance(t, str) for t in item["tags"])

            # ── envelope types are stable ints/bools, not DuckDB doubles ──
            assert isinstance(feed["total"], int) and not isinstance(feed["total"], bool)
            assert isinstance(feed["limit"], int)
            assert isinstance(feed["offset"], int)
            assert isinstance(feed["ranked"], bool)
            assert all(isinstance(w, str) for w in feed["signals"])
            assert feed["total"] == len(listed)
    finally:
        _reconnect_shared_storage(server)


def test_for_you_is_never_empty_for_a_brand_new_family():
    """Empty profile → empty word bag → `HAVING score > 0` returns nothing.
    The endpoint must fall back to the unranked library rather than hand Home
    a blank surface."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _seed_library(server.storage_backend)

            uid = "for-you-brand-new-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            assert client.get("/profile", headers=auth).json()["children"] == {}

            feed = client.get("/content/for-you", headers=auth).json()
            assert feed["signals"] == []
            assert feed["ranked"] is False
            assert len(feed["items"]) > 0, "a brand-new family must not get a blank feed"
            assert feed["total"] >= len(feed["items"])
            for item in feed["items"]:
                assert set(item.keys()) == ARTICLE_KEYS

            # A profile whose words match NOTHING in the library degrades the
            # same way — still a full feed, just unranked.
            client.patch("/profile", json={"stressors": ["zzzqqqxyzzy"]}, headers=auth)
            feed = client.get("/content/for-you", headers=auth).json()
            assert feed["signals"] == ["zzzqqqxyzzy"]
            assert feed["ranked"] is False
            assert len(feed["items"]) > 0
    finally:
        _reconnect_shared_storage(server)


def test_word_scorer_survives_duckdb():
    """Regression for the bug the for-you build surfaced: the scorer filtered
    with a bare `HAVING score > 0` and no GROUP BY, which DuckDB 1.5 reads as an
    aggregate over the whole table — so `/content/relevant` (and anything else
    on score_articles_by_words) raised BinderException on EVERY call."""
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _seed_library(server.storage_backend)

            r = client.get("/content/relevant?topic=bedtime standoffs&limit=5")
            assert r.status_code == 200, r.text
            body = r.json()
            assert any(a["id"] == "art-fy-8-match-a" for a in body["articles"])
            # The board is retired: articles are the only content kind left.
            assert set(body) == {"articles"}
    finally:
        _reconnect_shared_storage(server)


def test_for_you_paginates_and_caps():
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _seed_library(server.storage_backend)

            # No profile → the unranked library order (by id), so paging is
            # deterministic and can be diffed against the full list.
            uid = "for-you-paging-user"
            tok = client.post("/auth/issue-token", json={"user_id": uid}).json()["token"]
            auth = {"Authorization": f"Bearer {tok}"}

            full = client.get("/content/for-you?limit=100", headers=auth).json()
            assert full["ranked"] is False
            assert full["total"] >= 4

            page1 = client.get("/content/for-you?limit=2&offset=0", headers=auth).json()
            page2 = client.get("/content/for-you?limit=2&offset=2", headers=auth).json()
            assert [a["id"] for a in page1["items"]] == [a["id"] for a in full["items"][:2]]
            assert [a["id"] for a in page2["items"]] == [a["id"] for a in full["items"][2:4]]
            assert page2["offset"] == 2 and page2["limit"] == 2
            assert page1["total"] == page2["total"] == full["total"]

            # Past the end is empty but still a 200 with a sane envelope.
            tail = client.get(
                f"/content/for-you?limit=5&offset={full['total'] + 10}", headers=auth
            ).json()
            assert tail["items"] == []
            assert tail["total"] == full["total"]

            # Out-of-range params are rejected, never unbounded.
            assert client.get("/content/for-you?limit=0", headers=auth).status_code == 422
            assert client.get("/content/for-you?limit=1000", headers=auth).status_code == 422
            assert client.get("/content/for-you?offset=-1", headers=auth).status_code == 422
    finally:
        _reconnect_shared_storage(server)


def test_the_reader_eyebrow_fields_survive_every_article_path():
    """`kicker` + `age_range` (migration v23) feed the reader's eyebrow —
    "WE TRIED IT · Ages 3–7 · 4 min".

    Adding the columns is not shipping the feature. The first pass added them to
    the DDL and the migration ONLY: no SELECT read them, no write path set them,
    and the CMS had no field — so the eyebrow would have rendered blank forever
    while every test passed. This asserts all five paths carry them, and that the
    two endpoints iOS decodes with ONE model agree on the shape.
    """
    from fastapi.testclient import TestClient
    import app.server as server

    try:
        with TestClient(server.app) as client:
            _reconnect_shared_storage(server)
            storage = server.storage_backend

            made = storage.create_article({
                "id": "art-eyebrow-1", "category": "cat-fy",
                "title": "A Rainy Saturday, Nothing Bought",
                "subtitle": "Four things to do with tape and a bedsheet",
                "emoji": "", "author": "Miguel Alvarado", "read_time": "4 min",
                "kicker": "WE TRIED IT", "age_range": "Ages 3–7",
                "summary": "", "tags": ["rainy-day"], "content": "body",
            })
            assert made["kicker"] == "WE TRIED IT"
            assert made["age_range"] == "Ages 3–7"

            # detail read
            got = storage.get_article("art-eyebrow-1")
            assert (got["kicker"], got["age_range"]) == ("WE TRIED IT", "Ages 3–7")

            # list read
            listed = {a["id"]: a for a in storage.get_articles()}
            assert listed["art-eyebrow-1"]["age_range"] == "Ages 3–7"

            # search + word-scorer reads (separate SELECTs, each easy to miss)
            found = storage.search_articles("Rainy Saturday")
            assert found and found[0]["kicker"] == "WE TRIED IT"
            scored = storage.score_articles_by_words(["rainy"])
            assert scored and "age_range" in scored[0]

            # a partial update must not blank the sibling column
            patched = storage.update_article("art-eyebrow-1", {"kicker": "WE ASKED"})
            assert patched["kicker"] == "WE ASKED"
            assert patched["age_range"] == "Ages 3–7", "a partial PATCH wiped the other field"

            # an article with NEITHER set decodes fine and yields no eyebrow —
            # the client joins only non-empty parts, so '' must not become ' · '.
            plain = storage.create_article({
                "id": "art-eyebrow-2", "category": "cat-fy", "title": "Plain",
                "subtitle": "", "emoji": "", "author": "MVP Editorial",
                "read_time": "", "summary": "", "tags": [], "content": "body",
            })
            assert plain["kicker"] == "" and plain["age_range"] == ""

            # …and the two HTTP payloads iOS decodes with one model agree.
            over = client.get("/content/articles?limit=500")
            assert over.status_code == 200, over.text
            # /content/articles returns a bare LIST (the ranked feed wraps its
            # items in an envelope) — the shape difference is the endpoint's, not
            # the item's, and the item shape is what iOS decodes.
            for item in over.json():
                assert "kicker" in item and "age_range" in item, item["id"]
    finally:
        _reconnect_shared_storage(server)
