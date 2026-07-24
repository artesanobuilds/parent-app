"""
Codebase-invariant guard: every route is bound to the function it was written for.

Born from a real outage (2026-07-24): a helper (`_parent_voice_greeting`) was
inserted between `@app.get("/voice/parent-convai-token")` and its endpoint, so
the decorator silently captured the helper. Two things broke at once, with no
error anywhere: the route LOST `Depends(current_user)` (auth gone), and the
helper's plain `user_id: str` became a required query param — every voice
connect 422ed and prod voice was down until hotfix `3efad97`.

Python gives this failure mode no seam to fail on — the decorator doesn't know
which def you *meant*. So we pin two app-wide invariants that its symptoms
cannot slip past:

1. No registered route handler is a private helper (leading underscore). Route
   endpoints are the app's public surface; a `_name` handler means a decorator
   grabbed something it shouldn't have.
2. Any route that accepts an identity-like QUERY param without auth is flagged.
   `tests/test_bola_sweep.py` enforces this for PATH params; the outage route
   leaked `user_id` as a query param, which that sweep never inspects.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "route_guard.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.routing import APIRoute  # noqa: E402

import app.server as server  # noqa: E402
from app.auth import current_user  # noqa: E402
from app.admin_auth import require_admin_token  # noqa: E402


def _api_routes() -> list[APIRoute]:
    return [r for r in server.app.routes if isinstance(r, APIRoute)]


def _dependency_calls(route: APIRoute) -> set:
    calls = set()
    stack = [route.dependant]
    while stack:
        dep = stack.pop()
        if dep.call is not None:
            calls.add(dep.call)
        stack.extend(dep.dependencies)
    return calls


def _is_authed(route: APIRoute) -> bool:
    calls = _dependency_calls(route)
    return current_user in calls or require_admin_token in calls


def test_no_route_is_bound_to_a_private_helper() -> None:
    """A `_underscore` endpoint name is the outage's exact signature: the
    decorator captured a helper that happened to sit under it."""
    offenders = [
        f"{sorted(route.methods or set())} {route.path} -> {route.endpoint.__name__}"
        for route in _api_routes()
        if route.endpoint.__name__.startswith("_")
    ]
    assert not offenders, (
        "Route handlers must be the public endpoint functions, not private "
        "helpers — a decorator has probably captured the wrong def:\n  "
        + "\n  ".join(sorted(offenders))
    )


def test_route_paths_are_uniquely_bound() -> None:
    """The same (method, path) registered twice means one handler is shadowed —
    the second registration silently wins for matching, and which function
    serves the route becomes an import-order accident."""
    seen: dict[tuple[str, str], str] = {}
    dupes: list[str] = []
    for route in _api_routes():
        for method in route.methods or set():
            key = (method, route.path)
            if key in seen and seen[key] != route.endpoint.__name__:
                dupes.append(f"{method} {route.path}: {seen[key]} vs {route.endpoint.__name__}")
            seen.setdefault(key, route.endpoint.__name__)
    assert not dupes, "Same route registered to two different handlers:\n  " + "\n  ".join(dupes)


# Identity-ish query params that must not be readable without auth. `user_id`
# as a QUERY param is doubly suspect: authenticated endpoints get the caller
# from the token (Depends(current_user)), so a user_id query on an unauthed
# route usually means auth fell off — exactly the 2026-07-24 outage.
_SENSITIVE_QUERY = ("user_id", "kid_name", "agent_id", "parent_email")

# (method, path) pairs allowed to take a sensitive query param without
# current_user/require_admin_token, each with a justification.
QUERY_ALLOWLIST: dict[tuple[str, str], str] = {
    ("POST", "/auth/issue-token"): "the login bootstrap itself — rate-limited, mints the token auth would require",
}


def test_sensitive_query_params_require_auth() -> None:
    violations: list[str] = []
    for route in _api_routes():
        query_names = {
            p.name
            for p in route.dependant.query_params
            if p.name in _SENSITIVE_QUERY or p.name.endswith("_id")
        }
        if not query_names or _is_authed(route):
            continue
        for method in route.methods or set():
            if method == "HEAD" or (method, route.path) in QUERY_ALLOWLIST:
                continue
            violations.append(f"{method} {route.path} (query: {sorted(query_names)})")
    assert not violations, (
        "Routes accept identity-like query params without auth. Authenticate "
        "them, or allowlist with a justification:\n  " + "\n  ".join(sorted(violations))
    )


def test_query_allowlist_entries_still_exist() -> None:
    live = {
        (method, route.path)
        for route in _api_routes()
        for method in (route.methods or set())
    }
    stale = [k for k in QUERY_ALLOWLIST if k not in live]
    assert not stale, f"QUERY_ALLOWLIST entries for routes that no longer exist: {stale}"
