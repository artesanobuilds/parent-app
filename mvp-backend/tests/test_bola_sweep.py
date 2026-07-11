"""
Codebase-invariant guard: every route addressing data by id is authenticated.

BOLA (Broken Object-Level Authorization) is per-endpoint and easy to miss on
exactly one route. Rather than trusting review, this test introspects the live
FastAPI app: any route whose path contains an id-like parameter must resolve
the caller via `current_user` (per-family scoping) or `require_admin_token`
(operator endpoints) somewhere in its dependency tree.

Deliberately-public routes are allowlisted BY EXACT (method, path) with a
justification — adding a new id-addressed route without auth fails this test
until it is either authenticated or consciously allowlisted.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "bola_sweep.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.routing import APIRoute  # noqa: E402

import app.server as server  # noqa: E402
from app.auth import current_user  # noqa: E402
from app.admin_auth import require_admin_token  # noqa: E402

# Params that address a specific row/principal. `token` (share links) is a
# high-entropy capability and is judged separately; `full_path` is SPA static.
_SENSITIVE = ("user_id", "kid_name", "agent_id", "filename")


def _is_sensitive(param: str) -> bool:
    return param.endswith("_id") or param in _SENSITIVE


# (method, path) pairs that take an id-like param WITHOUT auth, on purpose.
PUBLIC_ALLOWLIST: dict[tuple[str, str], str] = {
    # Seeded/editorial content — same catalog for every family, no PII.
    ("GET", "/content/articles/{article_id}"): "public editorial content",
    ("GET", "/content/community/{post_id}"): "public community content",
    ("GET", "/content/community/{post_id}/replies"): "public community content",
}


def _dependency_calls(route: APIRoute) -> set:
    calls = set()
    stack = [route.dependant]
    while stack:
        dep = stack.pop()
        if dep.call is not None:
            calls.add(dep.call)
        stack.extend(dep.dependencies)
    return calls


def test_every_id_addressed_route_is_authenticated() -> None:
    violations: list[str] = []
    for route in server.app.routes:
        if not isinstance(route, APIRoute):
            continue
        params = set(route.param_convertors.keys())
        if not any(_is_sensitive(p) for p in params):
            continue
        calls = _dependency_calls(route)
        authed = current_user in calls or require_admin_token in calls
        for method in route.methods or set():
            if method == "HEAD":
                continue
            if authed or (method, route.path) in PUBLIC_ALLOWLIST:
                continue
            violations.append(f"{method} {route.path} (params: {sorted(params)})")

    assert not violations, (
        "Routes address data by id without current_user/require_admin_token. "
        "Authenticate them, or add to PUBLIC_ALLOWLIST with a justification:\n  "
        + "\n  ".join(sorted(violations))
    )


def test_allowlist_entries_still_exist() -> None:
    """A stale allowlist entry means a public exemption outlived its route."""
    live = {
        (method, route.path)
        for route in server.app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
    }
    stale = [key for key in PUBLIC_ALLOWLIST if key not in live]
    assert not stale, f"PUBLIC_ALLOWLIST entries for routes that no longer exist: {stale}"
