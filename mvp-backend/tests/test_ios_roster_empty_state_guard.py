"""
Codebase-invariant guard: a FAILED roster fetch must never render as "no kids".

Why this test exists
--------------------
A shipped bug (reported 2026-08-08, "when I navigate and come back to home, it
looks like there are no kids"). Two defects compounded:

1. **`.task(id:)` cancels its predecessor when the id changes.** Switching to
   another tab and back bumps `homeRefreshToken`, so an in-flight
   `KidsHomeViewModel.refresh()` was cancelled partway; the replacement call hit
   `guard !isLoading else { return }` and bailed, leaving `kids` empty.
2. **The view had TWO states where it needed THREE.** `kids.isEmpty` rendered the
   "add your first child" empty state, so a cancelled/failed fetch was
   indistinguishable from a family with no children — and the `catch` only
   `print`ed, so nothing surfaced.

A parent seeing their children vanish from Home cannot tell a display problem
from lost data, and this app HAS lost a family before
(`debugging_onboarding_seed_localhost`). So the empty state must be reachable
only from a fetch that actually succeeded.

The invariant
-------------
In `KidsHomeSection.swift`:
  • the view model exposes a "we have loaded successfully at least once" flag,
  • the empty-state branch is gated on it,
  • there is a distinct failure state,
  • and the `catch` does NOT clear the roster.

Pure-Python, no network, no app import — it just reads the Swift source.
"""
from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SECTION = REPO_ROOT / "mvp" / "MVP" / "KidsHomeSection.swift"


@pytest.fixture(scope="module")
def source() -> str:
    assert SECTION.is_file(), f"missing {SECTION}"
    return SECTION.read_text(encoding="utf-8")


def test_the_view_model_tracks_a_successful_load(source: str):
    """Without this flag the view cannot tell "no kids" from "no answer"."""
    assert "hasLoadedOnce" in source, (
        "KidsHomeViewModel must publish a successful-load flag. Without it the "
        "empty state and a failed fetch are the same rendering, which is how "
        "kids appeared to vanish on returning to the Home tab."
    )
    assert re.search(r"self\.hasLoadedOnce\s*=\s*true", source), (
        "hasLoadedOnce must be set on the SUCCESS path of refresh()"
    )


def test_the_empty_state_is_gated_on_a_successful_load(source: str):
    """`kids.isEmpty` alone must not reach the "add your first child" copy."""
    empty_branches = re.findall(r"if\s+vm\.kids\.isEmpty[^\{]*\{", source)
    assert empty_branches, "expected an empty-kids branch in the section body"
    gated = [b for b in empty_branches if "hasLoadedOnce" in b]
    assert gated, (
        "every `vm.kids.isEmpty` branch must consider `hasLoadedOnce`, so an "
        "offline or failed refresh renders a failure state rather than telling "
        "the parent they have no children"
    )


def test_a_distinct_failure_state_exists(source: str):
    """The failure copy must reassure, not imply data loss."""
    assert "loadFailedState" in source, (
        "expected a distinct load-failure view separate from `emptyState`"
    )
    # The reassurance is the point of the state, not decoration.
    assert "connection problem" in source, (
        "the failure state must say this is a connection problem and the kids "
        "are safe — a parent cannot otherwise distinguish it from lost data"
    )


def test_the_catch_does_not_clear_the_roster(source: str):
    """A failed re-fetch keeps whatever we last knew."""
    catch_start = source.index("} catch {", source.index("func performRefresh"))
    catch_body = source[catch_start:catch_start + 700]
    assert not re.search(r"self\.kids\s*=\s*\[\]", catch_body), (
        "refresh()'s catch must NOT blank `kids` — a transient failure would "
        "erase a known-good roster on screen"
    )


def test_overlapping_refreshes_coalesce_instead_of_bailing(source: str):
    """The tab-switch cancellation is what actually triggered the bug."""
    assert "inFlight" in source, (
        "refresh() must coalesce concurrent calls (await the in-flight task) "
        "rather than dropping the second one. `.task(id:)` cancels its "
        "predecessor when the token changes, so a bare `guard !isLoading` "
        "returns without ever populating `kids`."
    )
    assert not re.search(r"func refresh\(\) async \{\s*guard !isLoading else \{ return \}", source), (
        "the bare `guard !isLoading else { return }` at the top of refresh() is "
        "the dropped-call bug; coalesce on the in-flight task instead"
    )
