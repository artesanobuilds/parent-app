"""Tests for the offline ZIP -> nearby-towns grounding (app/research/geo.py).

The headline case: a 50-mile search from ZIP 95448 (Healdsburg, CA) MUST include
Sebastopol (~18mi) — the exact town the discovery agent used to miss because the
radius had no geographic grounding.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.research.geo import nearby_towns  # noqa: E402


def _cities(rows):
    return {r["city"] for r in rows}


def test_95448_50mi_includes_sebastopol_and_santa_rosa():
    rows = nearby_towns("95448", 50)
    cities = _cities(rows)
    assert "Sebastopol" in cities, "the town the agent used to miss"
    assert "Santa Rosa" in cities
    assert "Healdsburg" in cities  # origin
    # Origin is first, distance 0.
    assert rows[0]["city"] == "Healdsburg"
    assert rows[0]["distance_mi"] == 0.0
    # Nearest-first ordering.
    dists = [r["distance_mi"] for r in rows]
    assert dists == sorted(dists)
    # Deduped by (city, state).
    keys = [(r["city"], r["state"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_small_radius_excludes_farther_town():
    # Sebastopol (~18mi) is outside a 5-mile radius; Healdsburg (origin) stays.
    rows = nearby_towns("95448", 5)
    cities = _cities(rows)
    assert "Healdsburg" in cities
    assert "Sebastopol" not in cities


def test_cap_is_respected():
    rows = nearby_towns("95448", 50, max_towns=5)
    assert len(rows) <= 5


def test_50mi_spans_the_radius_not_just_nearest_cluster():
    # A 50-mile search must reach FAR towns, not stop ~16mi out. The outer-band
    # selection guarantees the list spans well past the nearby cluster.
    rows = nearby_towns("95448", 50)
    assert rows[0]["city"] == "Healdsburg"  # origin still first
    assert "Sebastopol" in _cities(rows)     # nearby cluster preserved
    assert max(r["distance_mi"] for r in rows) > 30, "should reach the outer radius"


def test_unknown_zip_returns_empty():
    assert nearby_towns("00000", 50) == []
    assert nearby_towns("", 50) == []
    assert nearby_towns(None, 50) == []


def test_nonpositive_radius_returns_empty():
    assert nearby_towns("95448", 0) == []


def test_distance_grows_with_radius():
    near = nearby_towns("95448", 10)
    far = nearby_towns("95448", 50)
    assert _cities(near).issubset(_cities(far))
    assert len(far) >= len(near)


def test_distance_for_city():
    from app.research.geo import distance_for_city
    # Healdsburg (95448) -> Sebastopol is ~15-18 miles.
    d = distance_for_city("95448", "Sebastopol", "CA")
    assert d is not None and 10 < d < 25
    # Origin city -> ~0.
    d0 = distance_for_city("95448", "Healdsburg", "CA")
    assert d0 is not None and d0 < 3
    # Unknown town / ZIP -> None (sorts last under Nearest).
    assert distance_for_city("95448", "Nowheresville", "CA") is None
    assert distance_for_city("00000", "Sebastopol", "CA") is None
    assert distance_for_city("95448", None) is None
