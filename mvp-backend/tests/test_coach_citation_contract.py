"""Cross-surface contract: the coach's mvp:// citation links (2026-07-18).

The coach cites content as [Title](mvp://library/{id}) — the backend EMITS that
shape (content catalog + prompt instruction) and iOS PARSES it (AgentView's
OpenURLAction → ArticleRoute). These links were dead in production for weeks
because nothing tied the two sides together: the prompt instructed a URL scheme
no client handled. This locks the pair, in the same grep-the-iOS-sources style
as test_ios_baseurl_guard.

**2026-08-07 (beta-v1 Phase 1 / sprint 2):** the public community board is
retired and `mvp://community/` is no longer a link shape anything serves — the
/content/community* routes are gone and the `community_posts` / `post_replies`
tables were dropped in migration v21. The catalog must therefore emit NO
community citation: an emitted link to a retired surface is the same dead-link
bug in a new costume.

Also locks the coach's name contract: the UI titles the screen "Coach" and
soul.md tells the model its name — if either side drifts, the coach introduces
itself as something the screen doesn't say.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
IOS_ROOT = REPO_ROOT / "mvp" / "MVP"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "citation.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")


def test_catalog_emits_the_mvp_link_shape_with_real_ids():
    """content_catalog_for_prompt must cite items as mvp://library/{article.id}
    — the exact id the public /content endpoints resolve, because iOS routes
    lastPathComponent straight into ArticleDetailView(articleId:) — and must
    cite NOTHING ELSE — the retired community board must not come back as a
    citation, in any form."""
    import app.server as server
    from app.duckdb_storage import DuckDBStorage
    from app.content import content_catalog_for_prompt

    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    storage = server.storage_backend
    storage.create_category({"id": "cat-cite", "name": "Citations", "emoji": "🔗", "description": ""})
    storage.create_article({
        "id": "art-cite-1", "category": "cat-cite", "title": "Cite Me",
        "subtitle": "s", "emoji": "", "read_time": "", "summary": "", "tags": [],
        "content": "body",
    })
    catalog = content_catalog_for_prompt()
    assert "(mvp://library/art-cite-1)" in catalog
    # The board is retired (its tables dropped in migration v21): no citation.
    assert "mvp://community/" not in catalog, (
        "the catalog still cites the retired community board — the coach would "
        "hand parents links to a surface that no longer exists"
    )
    # Every mvp:// link in the catalog uses the ONE host iOS still handles.
    for host in re.findall(r"mvp://([a-z-]+)/", catalog):
        assert host == "library", f"catalog emits unhandled host: {host}"


def test_prompt_instruction_matches_the_catalog_shape():
    """agent.py's instruction text and content.py's emitted links must agree —
    if the instruction shape changes, the catalog (and iOS) must move with it."""
    agent_src = (BACKEND_ROOT / "app" / "agent.py").read_text()
    assert "](mvp://library/" in agent_src, (
        "agent.py no longer instructs mvp://library citations — update "
        "content.py AND the iOS OpenURLAction in the same change"
    )


def test_ios_handles_every_link_shape_the_backend_emits():
    """AgentView must route mvp://library (OpenURLAction) and keep a handler
    for the disclaimer's mvp://learn-more. If this fails, coach citations are
    dead links again — the bug this file exists to prevent."""
    agent_view = (IOS_ROOT / "AgentView.swift").read_text()
    assert 'url.scheme == "mvp"' in agent_view, "AgentView lost the mvp:// OpenURLAction"
    assert '"library"' in agent_view and "ArticleRoute(" in agent_view
    assert '"learn-more"' in agent_view, "the disclaimer's Learn-more link has no handler"


def test_coach_name_is_consistent_across_surfaces():
    """The screen says "Coach" and the model is told its name is Coach — one
    identity, both surfaces."""
    soul = (BACKEND_ROOT / "soul.md").read_text()
    assert "Your name is **Coach**" in soul, "soul.md no longer names the coach"
    agent_view = (IOS_ROOT / "AgentView.swift").read_text()
    assert 'Text("Coach")' in agent_view, "AgentView nav title no longer says Coach"
