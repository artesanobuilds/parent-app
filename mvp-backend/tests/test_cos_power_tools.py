"""Unit tests for the Chief-of-Staff power-tools added 2026-06-28
(LookupAndSaveActivity, UpdateActivity, UntrackActivity, StartDiscovery,
GetKidsInfo, Help). Storage + the web lookup (Tavily + extractor) are faked, so
these run with NO network/LLM cost and assert the tool's logic + ownership
guards directly. The tools call ``_storage()`` and ``profiling_service`` — both
are monkeypatched / seeded here.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.cos.tools as cos_tools  # noqa: E402
from app.profiling import profiling_service  # noqa: E402

USER = "power-tools-test-user"


class FakeStorage:
    def __init__(self, candidates=None, tracked=None):
        self._candidates = candidates or []
        self._tracked = {t["id"]: t for t in (tracked or [])}
        self._next = 1
        self.enqueued = []

    # candidates / tracking
    def list_candidates(self, *, user_id=None, kid_name=None, category=None):
        return list(self._candidates)

    def track_activity(self, user_id, *, name, **fields):
        aid = f"act-{self._next}"
        self._next += 1
        row = {"id": aid, "user_id": user_id, "name": name, **fields}
        self._tracked[aid] = row
        return aid

    def get_tracked_activity(self, activity_id):
        return self._tracked.get(activity_id)

    def update_tracked_activity(self, activity_id, **fields):
        self._tracked[activity_id].update(fields)

    def delete_tracked_activity(self, activity_id):
        self._tracked.pop(activity_id, None)

    # discovery
    def enqueue_research_run(self, *, user_id, location, kids, params=None):
        self.enqueued.append({"location": location, "kids": kids, "params": params})
        return {"run_id": "run-1", "status": "queued", "deduped": False}


def _tool(name, user_id=USER):
    for t in cos_tools.build_cos_tools(user_id):
        if t.name == name:
            # These are business-logic unit tests with FakeStorage. Exercise
            # that body directly; test_durable_agent_commands runs the actual
            # decorated ToolNode against DuckDB (receipts + ownership + replay).
            fn = getattr(t.func, "__wrapped__", None)
            if fn is not None:
                from types import SimpleNamespace
                return SimpleNamespace(invoke=lambda args: fn(**args))
            return t
    raise AssertionError(f"tool {name} not built")


def _seed_kids():
    # Reset just this user's profile so GetKidsInfo / StartDiscovery read it.
    profiling_service._profiles.pop(USER, None)  # type: ignore[attr-defined]
    profiling_service.update_parent_profile(
        USER, {"name": "Pat", "postal_code": "95448", "country": "US"}
    )
    profiling_service.update_child_profile(
        USER, "Ceiba", {"name": "Ceiba", "age": 7.0, "grade_band": "elementary", "interests": ["art"]}
    )


# --------------------------------------------------------------------------- #
# LookupAndSaveActivity
# --------------------------------------------------------------------------- #


def test_lookup_matches_existing_candidate_no_web(monkeypatch):
    storage = FakeStorage(
        candidates=[
            {"id": "cand-1", "name": "Camp Galileo", "provider": "Galileo",
             "price_amount": 420.0, "signup_url": "https://x", "kid_name": "Ceiba"}
        ]
    )
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)

    # If the web path were taken this would explode (no key) — assert it isn't.
    def _boom(*a, **k):  # pragma: no cover - must not be called
        raise AssertionError("web lookup should not run when a candidate matches")

    monkeypatch.setattr("langchain_tavily.TavilySearch", _boom)

    out = _tool("LookupAndSaveActivity").invoke(
        {"activity_name": "galileo", "status": "signed_up"}
    )
    assert "Saved" in out and "signed_up" in out
    saved = list(storage._tracked.values())[-1]
    assert saved["name"] == "Camp Galileo"
    assert saved["status"] == "signed_up"
    assert saved["candidate_id"] == "cand-1"


def test_lookup_falls_back_to_web_extract(monkeypatch):
    storage = FakeStorage(candidates=[])  # nothing pre-discovered
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)

    class FakeTavily:
        def __init__(self, *a, **k):
            pass

        def invoke(self, *a, **k):
            return {"results": [{"title": "Steve & Kate's", "url": "https://sk.com",
                                 "content": "Summer camp, ages 5-12, $500"}]}

    monkeypatch.setattr("langchain_tavily.TavilySearch", FakeTavily)

    from app.ingest.extract import ExtractedActivity, Contact

    def fake_extract(text, *, source_hint=None, cost_user=None):
        assert "Steve" in text  # the flattened results reached the extractor
        return ExtractedActivity(
            provider="Steve & Kate's", activity_name="Steve & Kate's Camp",
            location="Sebastopol", amount_due=500.0,
            contact=Contact(email="hi@sk.com"),
            links=[],
        )

    monkeypatch.setattr("app.ingest.extract.extract_from_text", fake_extract)

    out = _tool("LookupAndSaveActivity").invoke(
        {"activity_name": "Steve & Kate's", "kid_name": "Ceiba", "status": "signed_up"}
    )
    assert "Looked up and saved" in out
    saved = list(storage._tracked.values())[-1]
    assert saved["name"] == "Steve & Kate's Camp"
    assert saved["status"] == "signed_up"
    assert saved["kid_name"] == "Ceiba"
    assert saved["price_amount"] == 500.0


# --------------------------------------------------------------------------- #
# Update / untrack — ownership guard
# --------------------------------------------------------------------------- #


def test_update_activity_changes_status(monkeypatch):
    storage = FakeStorage(
        tracked=[{"id": "a1", "user_id": USER, "name": "Soccer", "status": "exploring"}]
    )
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)
    out = _tool("UpdateActivity").invoke(
        {"activity_id": "a1", "status": "confirmed", "decision_rationale": "best fit"}
    )
    assert "Updated" in out
    assert storage._tracked["a1"]["status"] == "confirmed"


def test_update_activity_rejects_other_users_row(monkeypatch):
    storage = FakeStorage(
        tracked=[{"id": "a1", "user_id": "someone-else", "name": "Soccer"}]
    )
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)
    out = _tool("UpdateActivity").invoke({"activity_id": "a1", "status": "confirmed"})
    assert "doesn't belong" in out
    assert "status" not in storage._tracked["a1"]


def test_untrack_activity_removes_owned_row(monkeypatch):
    storage = FakeStorage(
        tracked=[{"id": "a1", "user_id": USER, "name": "Soccer"}]
    )
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)
    out = _tool("UntrackActivity").invoke({"activity_id": "a1"})
    assert "Removed" in out
    assert "a1" not in storage._tracked


# --------------------------------------------------------------------------- #
# StartDiscovery
# --------------------------------------------------------------------------- #


def test_start_discovery_enqueues_with_profile(monkeypatch):
    _seed_kids()
    storage = FakeStorage()
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)
    out = _tool("StartDiscovery").invoke(
        {"focus": "art camps", "radius_miles": 25, "max_candidates": 10}
    )
    assert "Started a discovery run" in out
    assert storage.enqueued, "a run should be enqueued"
    run = storage.enqueued[0]
    assert run["location"]["postal_code"] == "95448"
    assert run["params"] == {
        "focus": "art camps",
        "radius_miles": 25,
        "max_candidates": 10,
    }
    assert run["kids"][0]["name"] == "Ceiba"


def test_start_discovery_needs_zip(monkeypatch):
    profiling_service._profiles.pop(USER, None)  # type: ignore[attr-defined]
    profiling_service.update_parent_profile(USER, {"name": "Pat"})  # no zip
    storage = FakeStorage()
    monkeypatch.setattr(cos_tools, "_storage", lambda: storage)
    out = _tool("StartDiscovery").invoke({})
    assert "ZIP" in out or "postal" in out
    assert not storage.enqueued


# --------------------------------------------------------------------------- #
# GetKidsInfo + Help
# --------------------------------------------------------------------------- #


def test_get_kids_info(monkeypatch):
    _seed_kids()
    out = _tool("GetKidsInfo").invoke({})
    assert "Ceiba" in out and "age 7" in out and "art" in out


def test_help_lists_capabilities():
    out = _tool("Help").invoke({})
    assert "Chief of Staff" in out
    for word in ("DISCOVER", "DECIDE", "TRACK", "signed up"):
        assert word in out
