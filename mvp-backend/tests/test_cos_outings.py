"""Unit tests for the quick-outings flow (app/cos/outings.py) and its thin COS
tool wrapper (SuggestOutings). Both the Tavily search and the synthesis LLM are
faked, so these run with NO network / LLM cost and assert the flow's logic
directly: timeframe resolution, count honoring/clamping, grounding, the
needs-location path, and that the flow is EPHEMERAL (touches no storage).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.cos.outings as outings  # noqa: E402
import app.cos.tools as cos_tools  # noqa: E402
from app.profiling import profiling_service  # noqa: E402

USER = "outings-test-user"

# 2026-07-10 is a Friday — "this weekend" is Sat Jul 11 / Sun Jul 12.
FRIDAY = date(2026, 7, 10)


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class _FakeTavily:
    """Stands in for langchain_tavily.TavilySearch."""

    last_query: str | None = None

    def __init__(self, *a, **k):
        pass

    def invoke(self, payload, *a, **k):
        _FakeTavily.last_query = (payload or {}).get("query")
        return {
            "results": [
                {"title": "California Academy of Sciences", "url": "https://calacademy.org",
                 "content": "Aquarium + rainforest dome, stroller-friendly, in Golden Gate Park."},
                {"title": "Yerba Buena Gardens", "url": "https://ybgfestival.org",
                 "content": "Open lawn, carousel, shade; free."},
            ]
        }


def _fake_chat_factory(n_outings: int):
    """Return a fake ChatOpenAI class whose structured-output invoke yields
    ``n_outings`` Outing rows (to exercise count trimming)."""

    class _FakeStructured:
        def invoke(self, *a, **k):
            rows = [
                outings.Outing(
                    title=f"Idea {i}", where="SF", why_it_fits="age fit",
                    good_to_know="stroller-friendly; indoor backup", url="https://x",
                )
                for i in range(1, n_outings + 1)
            ]
            return outings._OutingList(outings=rows)

    class _FakeChat:
        def __init__(self, *a, **k):
            pass

        def with_structured_output(self, *a, **k):
            return _FakeStructured()

    return _FakeChat


def _patch_externals(monkeypatch, *, n_outings: int = 5):
    monkeypatch.setattr("langchain_tavily.TavilySearch", _FakeTavily)
    monkeypatch.setattr(outings, "ChatOpenAI", _fake_chat_factory(n_outings))


def _seed_family(postal_code: str | None = "94110"):
    profiling_service._profiles.pop(USER, None)  # type: ignore[attr-defined]
    parent = {"name": "Sam"}
    if postal_code:
        parent["postal_code"] = postal_code
        parent["country"] = "US"
    profiling_service.update_parent_profile(USER, parent)
    # A toddler and an infant — the age-sensitivity case from the trigger.
    profiling_service.update_child_profile(USER, "Nova", {"name": "Nova", "age": "2.5"})
    profiling_service.update_child_profile(USER, "Baby", {"name": "Baby", "age": "0.4"})


# --------------------------------------------------------------------------- #
# _resolve_when
# --------------------------------------------------------------------------- #
def test_resolve_this_weekend_from_a_friday():
    r = outings._resolve_when("this weekend", today=FRIDAY)
    assert r["start"] == "2026-07-11" and r["end"] == "2026-07-12"
    assert "this weekend" in r["label"] and "2026" in r["label"]


def test_resolve_weekend_when_today_is_saturday():
    r = outings._resolve_when("this weekend", today=date(2026, 7, 11))  # Saturday
    assert r["start"] == "2026-07-11" and r["end"] == "2026-07-12"


def test_resolve_weekend_when_today_is_sunday_uses_current_weekend():
    r = outings._resolve_when("this weekend", today=date(2026, 7, 12))  # Sunday
    assert r["start"] == "2026-07-11" and r["end"] == "2026-07-12"


def test_resolve_today_next_weekend_and_passthrough():
    assert outings._resolve_when("today", today=FRIDAY)["start"] == "2026-07-10"
    nxt = outings._resolve_when("next weekend", today=FRIDAY)
    assert nxt["start"] == "2026-07-18" and nxt["end"] == "2026-07-19"
    # Unrecognized phrase passes through verbatim with no resolved dates.
    passthru = outings._resolve_when("a rainy Tuesday", today=FRIDAY)
    assert passthru["start"] is None and passthru["label"] == "a rainy Tuesday"


# --------------------------------------------------------------------------- #
# suggest_outings
# --------------------------------------------------------------------------- #
def test_suggest_outings_grounded_and_honors_count(monkeypatch):
    _seed_family()
    _patch_externals(monkeypatch, n_outings=5)

    result = outings.suggest_outings(
        USER, location="San Francisco, CA", when="this weekend", count=3, today=FRIDAY
    )
    assert result["location"] == "San Francisco, CA"
    assert "this weekend" in result["when"]
    # count honored — asked for 3 even though the model returned 5.
    assert len(result["outings"]) == 3
    # kids carried through for grounding (ages are strings, untouched).
    ages = {k["age"] for k in result["kids"]}
    assert ages == {"2.5", "0.4"}
    # the search query was shaped by location + the resolved weekend.
    assert "San Francisco" in (_FakeTavily.last_query or "")


def test_suggest_outings_clamps_count(monkeypatch):
    _seed_family()
    _patch_externals(monkeypatch, n_outings=8)
    result = outings.suggest_outings(USER, location="SF", count=99, today=FRIDAY)
    assert len(result["outings"]) == outings._COUNT_MAX  # clamped to the ceiling


def test_suggest_outings_defaults_location_to_profile_zip(monkeypatch):
    _seed_family(postal_code="94110")
    _patch_externals(monkeypatch)
    result = outings.suggest_outings(USER, location=None, when="this weekend", today=FRIDAY)
    assert result["location"] == "94110"


def test_suggest_outings_needs_location_when_no_zip(monkeypatch):
    _seed_family(postal_code=None)
    _patch_externals(monkeypatch)
    result = outings.suggest_outings(USER, location=None, today=FRIDAY)
    assert result.get("needs_location") is True
    assert "outings" not in result


def test_suggest_outings_is_ephemeral_no_storage(monkeypatch):
    """The flow must never touch storage. Guard: if anything tries to resolve the
    storage backend during a suggestion, fail loudly."""
    _seed_family()
    _patch_externals(monkeypatch)

    def _boom():  # pragma: no cover - must not be called
        raise AssertionError("suggest_outings must not touch storage (it's ephemeral)")

    # tools._storage() is the only storage seam near this feature; ensure the
    # module never reaches for it.
    monkeypatch.setattr(cos_tools, "_storage", _boom)
    result = outings.suggest_outings(USER, location="SF", count=2, today=FRIDAY)
    assert len(result["outings"]) == 2


# --------------------------------------------------------------------------- #
# The SuggestOutings tool wrapper (via build_cos_tools)
# --------------------------------------------------------------------------- #
def _tool(name, user_id=USER):
    for t in cos_tools.build_cos_tools(user_id):
        if t.name == name:
            return t
    raise AssertionError(f"tool {name} not built")


def test_tool_registered_and_relays_ideas(monkeypatch):
    _seed_family()
    _patch_externals(monkeypatch, n_outings=3)
    out = _tool("SuggestOutings").invoke(
        {"location": "San Francisco", "when": "this weekend", "count": 3}
    )
    assert "not saved to the plan" in out  # signals ephemerality to the parent
    assert "Idea 1" in out and "Link: https://x" in out


def test_tool_relays_needs_location(monkeypatch):
    _seed_family(postal_code=None)
    _patch_externals(monkeypatch)
    out = _tool("SuggestOutings").invoke({"location": None, "when": "this weekend"})
    assert "which city" in out.lower() or "where" in out.lower()
