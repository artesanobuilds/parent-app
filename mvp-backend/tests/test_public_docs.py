"""Phase 7 of the vertical expansion: public product docs on the dashboard.

Two guard rails, both source-level (the docs are static markdown bundled at
build time — there's no runtime to test from here):

1. GUARD EXCLUSION: the /docs routes must stay OUTSIDE ProtectedRoute in
   App.tsx. A guard regression silently kills the GTM funnel's "read the
   docs" link (visitors would bounce to /login), so it's locked by test —
   same idea as tests/test_ios_baseurl_guard.py.
2. REGISTRY COVERAGE (docs freshness): every registered vertical has a doc
   page named after its key (camp.md, outing.md, ...). The CLAUDE.md rule
   says a door-adding phase updates its docs in the same PR; this asserts
   the page at least exists. Frontmatter must parse (title + section) so a
   malformed page can't ship as a blank public doc.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.cos import verticals  # noqa: E402

DASHBOARD = BACKEND_ROOT / "parent-dashboard"
DOCS_DIR = DASHBOARD / "docs"
APP_TSX = DASHBOARD / "src" / "App.tsx"


def _frontmatter(text: str) -> dict:
    meta: dict = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    return meta


def test_docs_routes_outside_the_auth_guard():
    src = APP_TSX.read_text()
    assert 'path="/docs"' in src and 'path="/docs/:slug"' in src, (
        "the public /docs routes are gone from App.tsx"
    )
    # Everything between <ProtectedRoute> and </ProtectedRoute> is the guarded
    # subtree — the docs routes must not appear inside it.
    guarded = re.search(r"<ProtectedRoute>(.*?)</ProtectedRoute>", src, re.S)
    assert guarded is not None, "ProtectedRoute block not found in App.tsx"
    assert "docs" not in guarded.group(1).lower(), (
        "/docs moved INSIDE the auth guard — the public docs link would "
        "bounce visitors to /login"
    )
    # The docs routes must come before the guarded block (sibling of /login).
    assert src.index('path="/docs"') < src.index("<ProtectedRoute>")


def test_every_registered_vertical_has_a_doc_page():
    for key in verticals.REGISTRY:
        page = DOCS_DIR / f"{key}.md"
        assert page.is_file(), (
            f"vertical '{key}' has no docs page at {page} — the door-adding "
            "phase must ship its doc in the same PR (CLAUDE.md rule)"
        )


def test_doc_frontmatter_parses():
    pages = sorted(DOCS_DIR.glob("*.md"))
    assert pages, f"no docs found under {DOCS_DIR}"
    for page in pages:
        meta = _frontmatter(page.read_text())
        assert meta.get("title"), f"{page.name}: missing frontmatter title"
        assert meta.get("section"), f"{page.name}: missing frontmatter section"
        assert meta.get("draft", "false").lower() in ("true", "false"), (
            f"{page.name}: draft must be true/false"
        )
